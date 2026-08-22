"""Organization endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import FleetStatsOut, OrganizationCurrentResponse
from app.application.fleet_service import compute_fleet_stats
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("/current", response_model=OrganizationCurrentResponse)
async def current_organization(
    container: RepositoryContainer = Depends(get_container),
) -> OrganizationCurrentResponse:
    org = container.organizations.get_current()
    if org is None:
        raise HTTPException(status_code=404, detail="No organization seeded")
    stats = compute_fleet_stats(container.agents)
    return OrganizationCurrentResponse(
        id=org.id, name=org.name, slug=org.slug, created_at=org.created_at,
        stats=FleetStatsOut(
            total_agents=stats.total_agents, active=stats.active,
            high_risk=stats.high_risk, quarantined=stats.quarantined,
            by_severity=stats.by_severity, by_status=stats.by_status,
        ),
    )
