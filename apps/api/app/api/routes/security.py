"""Security scanning + incident endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.api.schemas import (
    SecurityIncidentListResponse,
    SecurityOverviewOut,
    SecurityScanRequest,
    SecurityScanResponse,
)
from app.application.security_service import scan, security_overview
from app.config import get_settings
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/security", tags=["security"])


@router.post("/scan", response_model=SecurityScanResponse)
async def security_scan(
    body: SecurityScanRequest,
    container: RepositoryContainer = Depends(get_container),
) -> SecurityScanResponse:
    outcome = scan(container, get_settings(), body.text, source=body.source, agent_id=body.agent_id)
    return SecurityScanResponse(**outcome.__dict__)


@router.get("/incidents", response_model=SecurityIncidentListResponse)
async def list_incidents(
    container: RepositoryContainer = Depends(get_container),
) -> SecurityIncidentListResponse:
    items = list(container.security_incidents.list())
    return SecurityIncidentListResponse(total=len(items), items=items)


@router.get("/overview", response_model=SecurityOverviewOut)
async def overview(
    container: RepositoryContainer = Depends(get_container),
) -> SecurityOverviewOut:
    return SecurityOverviewOut(**security_overview(container, get_settings()).__dict__)
