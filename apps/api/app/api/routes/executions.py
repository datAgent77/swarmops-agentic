"""Execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_container
from app.api.schemas import ExecutionCreate, ExecutionDetailResponse, ExecutionListResponse
from app.application.execution_service import (
    ExecutionAgentNotFound,
    ExecutionBlocked,
    ToolCallRequest,
    UnknownTool,
    start_execution,
)
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/executions", tags=["executions"])


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    limit: int | None = Query(default=None, ge=1, le=500),
    container: RepositoryContainer = Depends(get_container),
) -> ExecutionListResponse:
    items = list(container.executions.list(limit=limit))
    return ExecutionListResponse(total=len(items), items=items)


@router.post("", response_model=ExecutionDetailResponse, status_code=201)
async def create_execution(
    body: ExecutionCreate,
    container: RepositoryContainer = Depends(get_container),
) -> ExecutionDetailResponse:
    requests = [
        ToolCallRequest(tool=tc.tool, arguments=tc.arguments, idempotency_key=tc.idempotency_key)
        for tc in body.tool_calls
    ]
    try:
        execution = start_execution(container, body.agent_id, body.input_summary, requests)
    except ExecutionAgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{body.agent_id}' not found") from exc
    except ExecutionBlocked as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnknownTool as exc:
        raise HTTPException(status_code=400, detail=f"Unknown tool(s): {exc}") from exc

    return ExecutionDetailResponse(
        execution=execution,
        tool_calls=list(container.tool_calls.list_for_execution(execution.id)),
    )


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> ExecutionDetailResponse:
    execution = container.executions.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
    return ExecutionDetailResponse(
        execution=execution,
        tool_calls=list(container.tool_calls.list_for_execution(execution_id)),
    )
