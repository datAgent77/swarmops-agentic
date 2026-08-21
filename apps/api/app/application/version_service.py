"""Agent version intelligence: change proposals + self-evolving governance.

A proposal compares the agent's current (base) version to a candidate, runs the
deterministic diff and accept/reject rule, and persists the result. Gemini may
explain the impact (via the explainer), but the decision is always deterministic —
the model never approves a candidate.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.audit_service import record_event
from app.config import Settings
from app.domain.models import AgentChangeProposal, AgentVersion
from app.domain.version_intelligence import (
    DEFAULT_ALLOWED_REGRESSION,
    compute_diff,
    evaluate_change,
)
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.gemini_explainer import GovernanceExplanation, get_explainer


class VersionAgentNotFound(Exception):
    pass


class ProposalNotFound(Exception):
    pass


class NoCandidateVersion(Exception):
    pass


def _metric(version: AgentVersion, key: str) -> int:
    value = version.configuration.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _find_version(container: RepositoryContainer, agent_id: str, label: str) -> AgentVersion | None:
    return next((v for v in container.agent_versions.list_for_agent(agent_id) if v.version == label), None)


def create_proposal(
    container: RepositoryContainer,
    agent_id: str,
    candidate_version: str | None = None,
    allowed_regression: int = DEFAULT_ALLOWED_REGRESSION,
) -> AgentChangeProposal:
    agent = container.agents.get(agent_id)
    if agent is None:
        raise VersionAgentNotFound(agent_id)

    base = _find_version(container, agent_id, agent.current_version)
    if candidate_version:
        candidate = _find_version(container, agent_id, candidate_version)
    else:
        candidate = next(
            (v for v in container.agent_versions.list_for_agent(agent_id) if v.version != agent.current_version),
            None,
        )
    if base is None or candidate is None:
        raise NoCandidateVersion(agent_id)

    changes = compute_diff(base, candidate)
    perf_before, perf_after = _metric(base, "performance"), _metric(candidate, "performance")
    comp_before, comp_after = _metric(base, "compliance"), _metric(candidate, "compliance")
    decision, reason = evaluate_change(perf_before, perf_after, comp_before, comp_after, allowed_regression)

    proposal = AgentChangeProposal(
        id=f"prop-{uuid.uuid4().hex[:12]}", agent_id=agent_id,
        base_version=base.version, candidate_version=candidate.version,
        change_type=",".join(changes) or "no-change", changes=changes,
        old_summary=base.system_prompt_summary, new_summary=candidate.system_prompt_summary,
        performance_before=perf_before, performance_after=perf_after,
        compliance_before=comp_before, compliance_after=comp_after,
        decision=decision, reason=reason, created_at=datetime.now(UTC),
    )
    container.change_proposals.add(proposal)
    record_event(container, action="agent.change_proposed", resource_type="agent",
                 resource_id=agent_id, decision=decision.value, reason=reason,
                 metadata={"candidate": candidate.version, "changes": changes})
    return proposal


def evaluate_proposal(
    container: RepositoryContainer,
    proposal_id: str,
    allowed_regression: int = DEFAULT_ALLOWED_REGRESSION,
) -> AgentChangeProposal:
    proposal = container.change_proposals.get(proposal_id)
    if proposal is None:
        raise ProposalNotFound(proposal_id)
    decision, reason = evaluate_change(
        proposal.performance_before, proposal.performance_after,
        proposal.compliance_before, proposal.compliance_after, allowed_regression,
    )
    proposal.decision = decision
    proposal.reason = reason
    container.change_proposals.update(proposal)
    return proposal


@dataclass
class ProposalMetrics:
    performance_delta_pct: float
    compliance_delta_pct: float


def deltas(proposal: AgentChangeProposal) -> ProposalMetrics:
    def pct(before: int, after: int) -> float:
        return round((after - before) / before * 100, 1) if before else 0.0
    return ProposalMetrics(
        performance_delta_pct=pct(proposal.performance_before, proposal.performance_after),
        compliance_delta_pct=pct(proposal.compliance_before, proposal.compliance_after),
    )


def explain_proposal(settings: Settings, proposal: AgentChangeProposal) -> GovernanceExplanation:
    facts = {
        "agent_name": proposal.agent_id,
        "score": proposal.performance_after,
        "severity": proposal.decision.value,
        "drivers": [f"changed: {c}" for c in proposal.changes],
        "recommended_action": proposal.decision.value,
        "policy_action": proposal.decision.value,
        "policy_name": "self-evolving governance",
    }
    return get_explainer(settings).explain(facts)
