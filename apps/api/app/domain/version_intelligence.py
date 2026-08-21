"""Deterministic version diff + self-evolving governance rule.

Compares a base agent version to a candidate and decides whether the change may be
adopted — purely from numbers, no LLM. A compliance regression beyond the allowed
threshold is rejected even when performance improves: self-evolving agents require
self-evolving governance.
"""

from __future__ import annotations

from app.domain.enums import ProposalDecision
from app.domain.models import AgentVersion

# Maximum tolerated compliance-score drop for an otherwise-improving candidate.
DEFAULT_ALLOWED_REGRESSION = 5


def compute_diff(base: AgentVersion, candidate: AgentVersion) -> list[str]:
    """Return the list of aspects that changed between two versions."""
    changes: list[str] = []
    if base.system_prompt_hash != candidate.system_prompt_hash:
        changes.append("prompt")
    if set(base.tools) != set(candidate.tools):
        changes.append("tools")
    if set(base.permissions) != set(candidate.permissions):
        changes.append("permissions")
    if base.model != candidate.model:
        changes.append("model")
    if base.configuration.get("autonomy") != candidate.configuration.get("autonomy"):
        changes.append("autonomy")
    if set(base.data_sources) != set(candidate.data_sources):
        changes.append("data_access")
    return changes


def evaluate_change(
    performance_before: int,
    performance_after: int,
    compliance_before: int,
    compliance_after: int,
    allowed_regression: int = DEFAULT_ALLOWED_REGRESSION,
) -> tuple[ProposalDecision, str]:
    """Deterministic accept/reject. Compliance is protected first."""
    compliance_drop = compliance_before - compliance_after
    if compliance_drop > allowed_regression:
        return (
            ProposalDecision.REJECTED,
            "Performance improvement does not justify compliance regression.",
        )
    if performance_after < performance_before:
        return (
            ProposalDecision.REJECTED,
            "Candidate regresses performance without a compliance gain.",
        )
    return (
        ProposalDecision.ACCEPTED,
        "Improves performance without an unacceptable compliance regression.",
    )
