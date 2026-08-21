"""Structured status endpoint describing the running service."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.api.schemas import StatusResponse
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/status", response_model=StatusResponse)
async def status(settings: Settings = Depends(get_settings)) -> StatusResponse:
    return StatusResponse(
        service="swarmops-api",
        version=__version__,
        environment=settings.environment,
        demo_mode=settings.demo_mode,
        category="Fortified Enterprise Fleet",
        tagline="Discover. Govern. Orchestrate. Observe.",
    )
