"""Agent listing and detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_container
from app.api.schemas import AgentDetailResponse, AgentListResponse
from app.domain.enums import RiskLevel
from app.domain.repositories import AgentQuery
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: str | None = Query(default=None, description="Filter by exact AgentStatus."),
    department: str | None = Query(default=None),
    risk: RiskLevel | None = Query(default=None, description="Minimum severity band (e.g. HIGH → HIGH+)."),
    search: str | None = Query(default=None, description="Case-insensitive name/description/department match."),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: RepositoryContainer = Depends(get_container),
) -> AgentListResponse:
    query = AgentQuery(
        status=status, department=department, risk=risk, search=search, limit=limit, offset=offset
    )
    items = container.agents.list(query)
    return AgentListResponse(total=len(items), items=items)


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> AgentDetailResponse:
    agent = container.agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return AgentDetailResponse(
        agent=agent,
        versions=container.agent_versions.list_for_agent(agent_id),
        dependencies=container.dependencies.list_for_agent(agent_id),
    )
