"""Agent discovery & governance lifecycle.

Discovery runs a deterministic pipeline per discovered agent:

    DISCOVERED → PENDING_REVIEW → risk assessment → policy evaluation → QUARANTINED

when the rogue rule fires (risk_score >= 80 AND financial_capability AND no approval
gate). Quarantine/activation are privileged actions (PLATFORM_ADMIN or
SECURITY_OFFICER). Every step emits an append-only audit event.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.audit_service import record_event
from app.application.discovery import AgentDiscoveryProvider
from app.application.risk_service import assess_agent
from app.domain.enums import AgentStatus, AuditActorType, PolicyAction, Role
from app.domain.policy_engine import evaluate_policies
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.events import AGENT_DISCOVERED, AGENT_QUARANTINED, DomainEvent

_PRIVILEGED_ROLES = frozenset({Role.PLATFORM_ADMIN, Role.SECURITY_OFFICER})


class LifecycleAgentNotFound(Exception):
    pass


class NotAuthorized(Exception):
    """Actor lacks a privileged role for this lifecycle action."""


@dataclass(frozen=True)
class DiscoveryResult:
    agent_id: str
    name: str
    from_status: str
    to_status: str
    risk_score: int
    quarantined: bool
    reason: str
    already_processed: bool


def _governance_context(container: RepositoryContainer, agent_id: str, version_label: str,
                        risk_score: int) -> dict:
    financial, gate = False, True
    for v in container.agent_versions.list_for_agent(agent_id):
        if v.version == version_label:
            financial = bool(v.configuration.get("financial_capability", False))
            gate = bool(v.configuration.get("approval_gate", True))
            break
    return {"risk_score": risk_score, "financial_capability": financial, "approval_gate": gate}


async def run_discovery(
    container: RepositoryContainer, provider: AgentDiscoveryProvider
) -> list[DiscoveryResult]:
    results: list[DiscoveryResult] = []
    for discovered in await provider.discover_agents():
        agent = container.agents.get(discovered.agent_id)
        if agent is None:
            continue

        # Duplicate discovery is safe: an already-quarantined agent is left as-is.
        if agent.status is AgentStatus.QUARANTINED:
            results.append(DiscoveryResult(
                agent_id=agent.id, name=agent.name, from_status="QUARANTINED",
                to_status="QUARANTINED", risk_score=agent.risk_score, quarantined=True,
                reason=agent.quarantine_reason or "already quarantined", already_processed=True,
            ))
            continue

        origin = agent.status.value
        _set_status(container, agent.id, AgentStatus.DISCOVERED)
        record_event(container, action="agent.discovered", resource_type="agent",
                     resource_id=agent.id, reason=discovered.note)
        container.event_bus.publish(DomainEvent(AGENT_DISCOVERED, {"agent_id": agent.id}))
        _set_status(container, agent.id, AgentStatus.PENDING_REVIEW)
        record_event(container, action="agent.pending_review", resource_type="agent",
                     resource_id=agent.id)

        assessment = assess_agent(container, agent.id)
        record_event(container, action="risk.assessed", resource_type="agent", resource_id=agent.id,
                     decision=assessment.severity.value, reason=f"score {assessment.overall_score}",
                     metadata={"score": assessment.overall_score})

        agent = container.agents.get(agent.id)  # refresh (risk_score updated)
        assert agent is not None
        context = _governance_context(container, agent.id, agent.current_version, assessment.overall_score)
        decision = evaluate_policies(list(container.policies.list()), context)
        record_event(container, action="policy.evaluated", resource_type="agent", resource_id=agent.id,
                     decision=decision.action.value, reason=decision.reason)

        quarantined = decision.action is PolicyAction.QUARANTINE
        if quarantined:
            reason = f"{decision.reason} (risk {assessment.overall_score}/100)"
            agent.status = AgentStatus.QUARANTINED
            agent.quarantine_reason = reason
            container.agents.update(agent)
            record_event(container, action="agent.quarantined", resource_type="agent",
                         resource_id=agent.id, decision="QUARANTINE", reason=reason)
            container.event_bus.publish(DomainEvent(
                AGENT_QUARANTINED, {"agent_id": agent.id, "reason": reason}))
            to_status = "QUARANTINED"
        else:
            _set_status(container, agent.id, AgentStatus.APPROVED)
            record_event(container, action="agent.approved", resource_type="agent", resource_id=agent.id)
            reason = "passed governance review"
            to_status = "APPROVED"

        results.append(DiscoveryResult(
            agent_id=agent.id, name=agent.name, from_status=origin, to_status=to_status,
            risk_score=assessment.overall_score, quarantined=quarantined, reason=reason,
            already_processed=False,
        ))
    return results


def _set_status(container: RepositoryContainer, agent_id: str, status: AgentStatus) -> None:
    agent = container.agents.get(agent_id)
    if agent is not None:
        agent.status = status
        container.agents.update(agent)


def _require_privileged(container: RepositoryContainer, actor_user_id: str) -> None:
    user = container.users.get(actor_user_id)
    if user is None or user.role not in _PRIVILEGED_ROLES:
        raise NotAuthorized(
            f"Actor '{actor_user_id}' is not authorized; requires PLATFORM_ADMIN or SECURITY_OFFICER"
        )


def quarantine_agent(container: RepositoryContainer, agent_id: str, actor_user_id: str, reason: str):
    _require_privileged(container, actor_user_id)
    agent = container.agents.get(agent_id)
    if agent is None:
        raise LifecycleAgentNotFound(agent_id)
    agent.status = AgentStatus.QUARANTINED
    agent.quarantine_reason = reason or "manually quarantined"
    container.agents.update(agent)
    record_event(container, action="agent.quarantined", resource_type="agent", resource_id=agent_id,
                 actor_type=AuditActorType.USER, actor_id=actor_user_id, decision="QUARANTINE",
                 reason=agent.quarantine_reason)
    container.event_bus.publish(DomainEvent(
        AGENT_QUARANTINED, {"agent_id": agent_id, "reason": agent.quarantine_reason}))
    return agent


def activate_agent(container: RepositoryContainer, agent_id: str, actor_user_id: str):
    _require_privileged(container, actor_user_id)
    agent = container.agents.get(agent_id)
    if agent is None:
        raise LifecycleAgentNotFound(agent_id)
    agent.status = AgentStatus.ACTIVE
    agent.quarantine_reason = None
    container.agents.update(agent)
    record_event(container, action="agent.activated", resource_type="agent", resource_id=agent_id,
                 actor_type=AuditActorType.USER, actor_id=actor_user_id, decision="ACTIVATE")
    return agent
