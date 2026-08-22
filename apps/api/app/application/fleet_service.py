"""Fleet-level read models derived from the agent repository."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import AgentStatus
from app.domain.repositories import AgentRepository
from app.domain.severity import HIGH_RISK_FLOOR, severity_from_score


@dataclass(frozen=True)
class FleetStats:
    total_agents: int
    active: int
    high_risk: int
    quarantined: int
    by_severity: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)


def compute_fleet_stats(agents: AgentRepository) -> FleetStats:
    """Aggregate the headline Overview metrics + severity/status breakdowns."""
    all_agents = list(agents.list())

    by_severity = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    by_status: dict[str, int] = {s.value: 0 for s in AgentStatus}
    for a in all_agents:
        by_severity[severity_from_score(a.risk_score).value] += 1
        by_status[a.status.value] += 1

    return FleetStats(
        total_agents=len(all_agents),
        active=sum(1 for a in all_agents if a.status is AgentStatus.ACTIVE),
        high_risk=sum(1 for a in all_agents if a.risk_score >= HIGH_RISK_FLOOR),
        quarantined=sum(1 for a in all_agents if a.status is AgentStatus.QUARANTINED),
        by_severity=by_severity,
        by_status=by_status,
    )
