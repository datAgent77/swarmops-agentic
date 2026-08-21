"""Response contracts for the foundational endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import PolicyAction
from app.domain.models import Agent, AgentDependency, AgentVersion, Execution, ToolCall, User


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


class PolicyCreate(BaseModel):
    name: str
    description: str = ""
    scope: str = "global"
    priority: int = 100
    condition: dict[str, Any]
    action: PolicyAction
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_by: str = "user-alex-admin"


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    scope: str | None = None
    priority: int | None = None
    condition: dict[str, Any] | None = None
    action: PolicyAction | None = None
    parameters: dict[str, Any] | None = None
    enabled: bool | None = None


class EvaluateRequest(BaseModel):
    context: dict[str, Any]


class PolicyDecisionOut(BaseModel):
    matched: bool
    action: PolicyAction
    policy_id: str | None
    policy_name: str | None
    required_roles: list[str]
    reason: str


class ToolCallRequestIn(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class ExecutionCreate(BaseModel):
    agent_id: str
    input_summary: str = ""
    tool_calls: list[ToolCallRequestIn] = Field(default_factory=list)


class ExecutionListResponse(BaseModel):
    total: int
    items: list[Execution]


class ExecutionDetailResponse(BaseModel):
    execution: Execution
    tool_calls: list[ToolCall]
