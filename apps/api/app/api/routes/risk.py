"""Deterministic risk assessment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.application.risk_service import AgentNotFound, assess_agent, latest_assessment
from app.domain.models import RiskAssessment
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/agents", tags=["risk"])


@router.post("/{agent_id}/assess-risk", response_model=RiskAssessment)
async def assess_risk(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> RiskAssessment:
    try:
        return assess_agent(container, agent_id)
    except AgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc


@router.get("/{agent_id}/risk", response_model=RiskAssessment)
async def get_risk(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> RiskAssessment:
    try:
        assessment = latest_assessment(container, agent_id)
    except AgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc
    if assessment is None:
        raise HTTPException(status_code=404, detail="No risk assessment yet; run assess-risk first")
    return assessment
