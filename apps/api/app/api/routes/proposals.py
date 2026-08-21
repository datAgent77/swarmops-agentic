"""Agent change proposals + self-evolving governance endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import (
    ChangeProposalCreate,
    ChangeProposalListResponse,
    ChangeProposalResponse,
    ExplanationOut,
    ProposalEvaluateRequest,
)
from app.application.version_service import (
    NoCandidateVersion,
    ProposalNotFound,
    VersionAgentNotFound,
    create_proposal,
    deltas,
    evaluate_proposal,
    explain_proposal,
)
from app.config import get_settings
from app.domain.models import AgentChangeProposal
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1", tags=["version-intelligence"])


def _response(proposal: AgentChangeProposal) -> ChangeProposalResponse:
    d = deltas(proposal)
    explanation = explain_proposal(get_settings(), proposal)
    return ChangeProposalResponse(
        proposal=proposal,
        performance_delta_pct=d.performance_delta_pct,
        compliance_delta_pct=d.compliance_delta_pct,
        explanation=ExplanationOut(
            text=explanation.text, model_status=explanation.model_status,
            model_name=explanation.model_name, provider=explanation.provider,
        ),
    )


@router.post("/agents/{agent_id}/change-proposals", response_model=ChangeProposalResponse, status_code=201)
async def propose_change(
    agent_id: str,
    body: ChangeProposalCreate = Body(default=ChangeProposalCreate()),
    container: RepositoryContainer = Depends(get_container),
) -> ChangeProposalResponse:
    try:
        proposal = create_proposal(container, agent_id, body.candidate_version, body.allowed_regression)
    except VersionAgentNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc
    except NoCandidateVersion as exc:
        raise HTTPException(status_code=400, detail="No candidate version to compare") from exc
    return _response(proposal)


@router.get("/agents/{agent_id}/change-proposals", response_model=ChangeProposalListResponse)
async def list_proposals(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> ChangeProposalListResponse:
    items = list(container.change_proposals.list_for_agent(agent_id))
    return ChangeProposalListResponse(total=len(items), items=items)


@router.post("/change-proposals/{proposal_id}/evaluate", response_model=ChangeProposalResponse)
async def evaluate(
    proposal_id: str,
    body: ProposalEvaluateRequest = Body(default=ProposalEvaluateRequest()),
    container: RepositoryContainer = Depends(get_container),
) -> ChangeProposalResponse:
    try:
        proposal = evaluate_proposal(container, proposal_id, body.allowed_regression)
    except ProposalNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found") from exc
    return _response(proposal)
