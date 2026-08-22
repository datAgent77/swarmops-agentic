"""Demo lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_container
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


class ResetResponse(BaseModel):
    status: str
    total_agents: int


@router.post("/reset", response_model=ResetResponse)
async def reset_demo(
    container: RepositoryContainer = Depends(get_container),
) -> ResetResponse:
    """Wipe and deterministically recreate the SaitALCorp demo dataset."""
    container.reset()
    return ResetResponse(status="reset", total_agents=container.agents.count_total())
