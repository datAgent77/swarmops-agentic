"""Audit trail + observability endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_container
from app.api.schemas import (
    AuditListResponse,
    ObservabilityOverviewOut,
    TraceResponse,
    TraceStepOut,
)
from app.application.observability_service import build_trace, compute_overview
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1", tags=["observability"])


@router.get("/audit", response_model=AuditListResponse)
async def audit_log(
    limit: int = Query(default=200, ge=1, le=1000),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    container: RepositoryContainer = Depends(get_container),
) -> AuditListResponse:
    items = list(container.audit_events.list(limit=limit))
    if action:
        items = [e for e in items if e.action == action]
    if resource_type:
        items = [e for e in items if e.resource_type == resource_type]
    return AuditListResponse(total=len(items), items=items)


@router.get("/observability/overview", response_model=ObservabilityOverviewOut)
async def observability_overview(
    container: RepositoryContainer = Depends(get_container),
) -> ObservabilityOverviewOut:
    return ObservabilityOverviewOut(**compute_overview(container).__dict__)


@router.get("/observability/traces/{trace_id}", response_model=TraceResponse)
async def trace(
    trace_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> TraceResponse:
    result = build_trace(container, trace_id)
    return TraceResponse(
        trace_id=result.trace_id, execution_id=result.execution_id, status=result.status,
        duration_ms=result.duration_ms,
        steps=[TraceStepOut(**s.__dict__) for s in result.steps],
    )
