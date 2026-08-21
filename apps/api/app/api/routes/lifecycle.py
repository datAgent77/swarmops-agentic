"""Agent discovery and quarantine lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import (
    ActivateRequest,
    DiscoverResponse,
    DiscoveryResultOut,
    QuarantineRequest,
)
from app.application.lifecycle_service import (
    LifecycleAgentNotFound,
    NotAuthorized,
    activate_agent,
    quarantine_agent,
    run_discovery,
)
from app.domain.models import Agent
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.discovery_demo import DemoDiscoveryProvider

router = APIRouter(prefix="/api/v1/agents", tags=["lifecycle"])


@router.post("/discover", response_model=DiscoverResponse)
async def discover(container: RepositoryContainer = Depends(get_container)) -> DiscoverResponse:
    results = await run_discovery(container, DemoDiscoveryProvider())
    return DiscoverResponse(discovered=[DiscoveryResultOut(**r.__dict__) for r in results])


@router.post("/{agent_id}/quarantine", response_model=Agent)
async def quarantine(
    agent_id: str,
    body: QuarantineRequest,
    container: RepositoryContainer = Depends(get_container),
) -> Agent:
    try:
        return quarantine_agent(container, agent_id, body.actor_user_id, body.reason)
    except NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LifecycleAgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc


@router.post("/{agent_id}/activate", response_model=Agent)
async def activate(
    agent_id: str,
    body: ActivateRequest,
    container: RepositoryContainer = Depends(get_container),
) -> Agent:
    try:
        return activate_agent(container, agent_id, body.actor_user_id)
    except NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LifecycleAgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc
