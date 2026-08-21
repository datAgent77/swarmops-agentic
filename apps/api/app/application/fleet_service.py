"""Fleet-level read models derived from the agent repository."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import AgentStatus
from app.domain.repositories import AgentRepository
from app.domain.severity import HIGH_RISK_FLOOR


@dataclass(frozen=True)
class FleetStats:
    total_agents: int
    active: int
    high_risk: int
    quarantined: int


def compute_fleet_stats(agents: AgentRepository) -> FleetStats:
    """Aggregate the four headline Overview metrics over the whole fleet."""
    all_agents = agents.list()
    return FleetStats(
        total_agents=len(all_agents),
        active=sum(1 for a in all_agents if a.status is AgentStatus.ACTIVE),
        high_risk=sum(1 for a in all_agents if a.risk_score >= HIGH_RISK_FLOOR),
        quarantined=sum(1 for a in all_agents if a.status is AgentStatus.QUARANTINED),
    )
