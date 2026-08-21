"""Constrained toolset for the GovernanceAgent.

The AI agent may ONLY call these controlled functions — never the database or the
repositories directly. Critically, the mutating tools re-enforce deterministic rules
inside the tool: the model cannot set an arbitrary authorization. ``set_agent_status``
will refuse to activate an agent the deterministic engine says must be quarantined,
and refuse to quarantine one with no deterministic basis.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.application.audit_service import record_event
from app.application.risk_service import assess_agent
from app.domain.enums import AgentStatus, PolicyAction
from app.domain.policy_engine import evaluate_policies
from app.domain.risk_engine import RiskInput, assess
from app.infrastructure.container import RepositoryContainer

# The complete, fixed set of tools exposed to the GovernanceAgent.
ALLOWED_TOOLS: frozenset[str] = frozenset({
    "get_agent_metadata",
    "get_agent_dependencies",
    "calculate_risk",
    "get_applicable_policies",
    "create_risk_assessment",
    "create_approval_request",
    "record_audit_event",
    "set_agent_status",
})


class GovernanceToolset:
    """Container-bound implementations of the constrained tools."""

    def __init__(self, container: RepositoryContainer) -> None:
        self._c = container

    def tool_names(self) -> frozenset[str]:
        return ALLOWED_TOOLS

    # --- read tools -------------------------------------------------------
    def get_agent_metadata(self, agent_id: str) -> dict[str, Any]:
        agent = self._c.agents.get(agent_id)
        return agent.model_dump(mode="json") if agent else {"error": "not found"}

    def get_agent_dependencies(self, agent_id: str) -> list[dict[str, Any]]:
        return [d.model_dump(mode="json") for d in self._c.dependencies.list_for_agent(agent_id)]

    def _risk_input(self, agent_id: str) -> RiskInput | None:
        agent = self._c.agents.get(agent_id)
        if agent is None:
            return None
        version = next(
            (v for v in self._c.agent_versions.list_for_agent(agent_id) if v.version == agent.current_version),
            None,
        )
        deps = list(self._c.dependencies.list_for_agent(agent_id))
        return RiskInput(agent=agent, version=version, dependencies=deps)

    def calculate_risk(self, agent_id: str) -> dict[str, Any]:
        """Run the deterministic engine (no persistence). Authoritative."""
        inp = self._risk_input(agent_id)
        if inp is None:
            return {"error": "not found"}
        r = assess(inp)
        return {
            "score": r.total, "severity": r.severity.value,
            "recommended_action": r.recommended_action.value, "drivers": r.drivers,
        }

    def _governance_context(self, agent_id: str, score: int) -> dict[str, Any]:
        agent = self._c.agents.get(agent_id)
        financial, gate = False, True
        if agent is not None:
            for v in self._c.agent_versions.list_for_agent(agent_id):
                if v.version == agent.current_version:
                    financial = bool(v.configuration.get("financial_capability", False))
                    gate = bool(v.configuration.get("approval_gate", True))
                    break
        return {"risk_score": score, "financial_capability": financial, "approval_gate": gate}

    def get_applicable_policies(self, agent_id: str) -> dict[str, Any]:
        risk = self.calculate_risk(agent_id)
        if "error" in risk:
            return risk
        decision = evaluate_policies(
            list(self._c.policies.list()), self._governance_context(agent_id, risk["score"])
        )
        return {"action": decision.action.value, "policy_id": decision.policy_id,
                "policy_name": decision.policy_name, "required_roles": decision.required_roles}

    # --- write tools (deterministically guarded) --------------------------
    def create_risk_assessment(self, agent_id: str) -> dict[str, Any]:
        try:
            a = assess_agent(self._c, agent_id)
        except Exception:  # noqa: BLE001
            return {"error": "not found"}
        return {"id": a.id, "score": a.overall_score, "severity": a.severity.value}

    def create_approval_request(self, execution_id: str, role: str, reason: str = "") -> dict[str, Any]:
        from app.domain.enums import ApprovalStatus, Role
        from app.domain.models import ApprovalRequest

        try:
            role_enum = Role(role)
        except ValueError:
            return {"error": f"unknown role '{role}'"}
        approval = ApprovalRequest(
            id=f"appr-{uuid.uuid4().hex[:12]}", execution_id=execution_id, policy_id=None,
            requested_from_role=role_enum, sequence=1, status=ApprovalStatus.PENDING,
            reason=reason, context={}, created_at=datetime.now(UTC),
        )
        self._c.approvals.add(approval)
        return {"id": approval.id, "status": approval.status.value}

    def record_audit_event(self, action: str, resource_id: str, reason: str = "") -> dict[str, Any]:
        event = record_event(self._c, action=action, resource_type="agent",
                             resource_id=resource_id, reason=reason)
        return {"id": event.id, "action": event.action}

    def set_agent_status(self, agent_id: str, status: str) -> dict[str, Any]:
        """GUARDED. The model cannot override the deterministic authorization."""
        agent = self._c.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "reason": "agent not found"}
        try:
            target = AgentStatus(status)
        except ValueError:
            return {"ok": False, "reason": f"invalid status '{status}'"}

        risk = self.calculate_risk(agent_id)
        decision = evaluate_policies(
            list(self._c.policies.list()), self._governance_context(agent_id, risk["score"])
        )
        must_quarantine = decision.action is PolicyAction.QUARANTINE

        if must_quarantine and target is not AgentStatus.QUARANTINED:
            return {"ok": False, "status": agent.status.value,
                    "reason": "deterministic governance requires QUARANTINE; model cannot override"}
        if not must_quarantine and target is AgentStatus.QUARANTINED:
            return {"ok": False, "status": agent.status.value,
                    "reason": "no deterministic basis to quarantine; model cannot override"}

        agent.status = target
        if target is not AgentStatus.QUARANTINED:
            agent.quarantine_reason = None
        self._c.agents.update(agent)
        return {"ok": True, "status": target.value}
