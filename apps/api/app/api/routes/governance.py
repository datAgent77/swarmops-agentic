"""GovernanceAgent analysis endpoint (deterministic decision + Gemini explanation)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from app.agents.governance_agent import GovernanceAgent, GovernanceAgentError
from app.api.dependencies import get_container
from app.api.schemas import (
    ExplanationOut,
    GovernanceAnalysisRequest,
    GovernanceAnalysisResponse,
    PolicyDecisionOut,
)
from app.config import get_settings
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/agents", tags=["governance"])


@router.post("/{agent_id}/governance-analysis", response_model=GovernanceAnalysisResponse)
async def governance_analysis(
    agent_id: str,
    body: GovernanceAnalysisRequest = Body(default=GovernanceAnalysisRequest()),
    container: RepositoryContainer = Depends(get_container),
) -> GovernanceAnalysisResponse:
    agent = GovernanceAgent(container, get_settings())
    try:
        result = agent.analyze(agent_id, action_context=body.action_context or None)
    except GovernanceAgentError as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc

    d = result.policy
    return GovernanceAnalysisResponse(
        risk=result.assessment,
        policy=PolicyDecisionOut(
            matched=d.matched, action=d.action, policy_id=d.policy_id,
            policy_name=d.policy_name, required_roles=d.required_roles, reason=d.reason,
        ),
        explanation=ExplanationOut(
            text=result.explanation.text, model_status=result.explanation.model_status,
            model_name=result.explanation.model_name, provider=result.explanation.provider,
        ),
    )
