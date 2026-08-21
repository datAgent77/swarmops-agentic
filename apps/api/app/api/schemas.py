"""Response contracts for the foundational endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import Agent, AgentDependency, AgentVersion, User


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["swarmops-api"])


class StatusResponse(BaseModel):
    service: str
    version: str
    environment: str
    demo_mode: bool
    category: str = Field(description="Primary hackathon category / product framing.")
    tagline: str


class FleetStatsOut(BaseModel):
    total_agents: int
    active: int
    high_risk: int
    quarantined: int


class OrganizationCurrentResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    stats: FleetStatsOut


class AgentListResponse(BaseModel):
    total: int = Field(description="Number of agents matching the filters.")
    items: list[Agent]


class AgentDetailResponse(BaseModel):
    agent: Agent
    versions: list[AgentVersion]
    dependencies: list[AgentDependency]


class UserListResponse(BaseModel):
    items: list[User]
