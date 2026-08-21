"""Dependency graph + blast-radius endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import (
    BlastRadiusResponse,
    GraphEdgeOut,
    GraphNodeOut,
    GraphResponse,
)
from app.application.graph_service import (
    GraphData,
    build_agent_graph,
    build_fleet_graph,
    compute_blast_radius,
)
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1", tags=["graph"])


def _to_response(graph: GraphData) -> GraphResponse:
    return GraphResponse(
        nodes=[GraphNodeOut(**n.__dict__) for n in graph.nodes],
        edges=[GraphEdgeOut(**e.__dict__) for e in graph.edges],
    )


@router.get("/graph", response_model=GraphResponse)
async def fleet_graph(container: RepositoryContainer = Depends(get_container)) -> GraphResponse:
    return _to_response(build_fleet_graph(container))


@router.get("/agents/{agent_id}/graph", response_model=GraphResponse)
async def agent_graph(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> GraphResponse:
    return _to_response(build_agent_graph(container, agent_id))


@router.get("/agents/{agent_id}/blast-radius", response_model=BlastRadiusResponse)
async def blast_radius(
    agent_id: str,
    container: RepositoryContainer = Depends(get_container),
) -> BlastRadiusResponse:
    result = compute_blast_radius(container, agent_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return BlastRadiusResponse(**result.__dict__)
