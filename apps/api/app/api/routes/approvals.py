"""Human approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_container
from app.api.schemas import ApprovalActionRequest, ApprovalListResponse
from app.application.approval_service import ApprovalNotFound, WrongRole, approve, reject
from app.domain.models import ApprovalRequest
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    status: str | None = Query(default=None, description="Filter by ApprovalStatus."),
    container: RepositoryContainer = Depends(get_container),
) -> ApprovalListResponse:
    return ApprovalListResponse(items=list(container.approvals.list(status=status)))


@router.get("/{approval_id}", response_model=ApprovalRequest)
async def get_approval(
    approval_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> ApprovalRequest:
    approval = container.approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")
    return approval


def _act(fn, container: RepositoryContainer, approval_id: str, actor_user_id: str) -> ApprovalRequest:
    try:
        return fn(container, approval_id, actor_user_id)
    except ApprovalNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found") from exc
    except WrongRole as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{approval_id}/approve", response_model=ApprovalRequest)
async def approve_request(
    approval_id: str,
    body: ApprovalActionRequest,
    container: RepositoryContainer = Depends(get_container),
) -> ApprovalRequest:
    return _act(approve, container, approval_id, body.actor_user_id)


@router.post("/{approval_id}/reject", response_model=ApprovalRequest)
async def reject_request(
    approval_id: str,
    body: ApprovalActionRequest,
    container: RepositoryContainer = Depends(get_container),
) -> ApprovalRequest:
    return _act(reject, container, approval_id, body.actor_user_id)
