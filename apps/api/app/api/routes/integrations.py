"""Integration status endpoint (truthful CONNECTED / DEMO_MODE / NOT_CONFIGURED)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas import IntegrationInfoOut, IntegrationStatusResponse
from app.application.integrations import describe_integrations
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/status", response_model=IntegrationStatusResponse)
async def integrations_status(
    settings: Settings = Depends(get_settings),
) -> IntegrationStatusResponse:
    infos = describe_integrations(settings)
    return IntegrationStatusResponse(
        integrations=[
            IntegrationInfoOut(
                key=i.key, name=i.name, category=i.category, status=i.status.value,
                detail=i.detail, docs=i.docs,
            )
            for i in infos
        ]
    )
