"""Core domain models.

Pure data + a single derived field (severity). No persistence, framework, or LLM
concerns live here — those belong to the infrastructure and application layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, computed_field

from app.domain.enums import (
    AgentStatus,
    AutonomyLevel,
    DependencyTargetType,
    RecommendedAction,
    Relationship,
    RiskLevel,
    Role,
    ToolType,
)
from app.domain.severity import severity_from_score


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime


class User(BaseModel):
    id: str
    organization_id: str
    name: str
    email: str
    role: Role
    created_at: datetime


class Agent(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str
    owner_id: str
    department: str
    status: AgentStatus
    autonomy_level: AutonomyLevel
    risk_score: int
    current_version: str
    runtime: str
    framework: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity(self) -> RiskLevel:
        """Severity band derived from the current risk score (see P02)."""
        return severity_from_score(self.risk_score)


class AgentVersion(BaseModel):
    id: str
    agent_id: str
    version: str
    system_prompt_hash: str
    system_prompt_summary: str
    tools: list[str]
    permissions: list[str]
    data_sources: list[str]
    model: str
    configuration: dict[str, Any]
    created_by: str
    created_at: datetime


class Tool(BaseModel):
    id: str
    name: str
    type: ToolType
    risk_level: RiskLevel
    description: str
    endpoint: str | None = None
    permissions: list[str]
    metadata: dict[str, Any]


class AgentDependency(BaseModel):
    id: str
    source_agent_id: str
    target_type: DependencyTargetType
    target_id: str
    relationship: Relationship
    risk_level: RiskLevel


class RiskAssessment(BaseModel):
    id: str
    agent_id: str
    agent_version_id: str | None
    overall_score: int
    severity: RiskLevel
    # Per-dimension breakdown. ``data_score`` carries the missing-approval-gate
    # dimension per the RiskAssessment schema (see risk_engine dimension map).
    pii_score: int
    financial_score: int
    external_tool_score: int
    privilege_score: int
    autonomy_score: int
    prompt_score: int
    data_score: int
    drivers: list[str]
    recommended_action: RecommendedAction
    created_at: datetime
