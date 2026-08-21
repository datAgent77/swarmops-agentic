"""Core domain models.

Pure data + a single derived field (severity). No persistence, framework, or LLM
concerns live here — those belong to the infrastructure and application layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.domain.enums import (
    AgentStatus,
    ApprovalStatus,
    AuditActorType,
    AutonomyLevel,
    DependencyTargetType,
    ExecutionStatus,
    PolicyAction,
    ProposalDecision,
    RecommendedAction,
    Relationship,
    RiskLevel,
    Role,
    SecurityCategory,
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
    # Set when the agent is QUARANTINED; cleared on reactivation.
    quarantine_reason: str | None = None

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


class Execution(BaseModel):
    id: str
    agent_id: str
    agent_version_id: str | None
    status: ExecutionStatus
    input_summary: str
    output_summary: str | None = None
    risk_context: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    trace_id: str
    estimated_cost: float = 0.0
    # Tool calls deferred while the execution waits for approval (run on resume).
    pending_actions: list[dict[str, Any]] = Field(default_factory=list)


class ToolCall(BaseModel):
    id: str
    execution_id: str
    tool_id: str
    arguments_summary: str
    result_summary: str
    policy_decision: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    idempotency_key: str | None = None


class ApprovalRequest(BaseModel):
    id: str
    execution_id: str
    policy_id: str | None
    requested_from_role: Role
    sequence: int
    status: ApprovalStatus
    reason: str
    context: dict[str, Any]
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class AuditEvent(BaseModel):
    id: str
    organization_id: str
    actor_type: AuditActorType
    actor_id: str | None = None
    action: str
    resource_type: str
    resource_id: str
    decision: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    timestamp: datetime


class AgentChangeProposal(BaseModel):
    id: str
    agent_id: str
    base_version: str
    candidate_version: str
    change_type: str
    changes: list[str]                # deterministic diff (aspects that changed)
    old_summary: str
    new_summary: str
    performance_before: int
    performance_after: int
    compliance_before: int
    compliance_after: int
    decision: ProposalDecision
    reason: str
    created_at: datetime


class SecurityIncident(BaseModel):
    id: str
    organization_id: str
    source: str
    agent_id: str | None = None
    category: SecurityCategory
    severity: RiskLevel
    action: str                       # "BLOCKED" | "FLAGGED"
    input_excerpt: str
    detected_categories: list[str]
    scanner: str
    scanner_status: str               # "LIVE" | "LOCAL_DEMO"
    policy_id: str | None = None      # policy violated, when applicable
    resolved: bool = False
    created_at: datetime


class Policy(BaseModel):
    id: str
    name: str
    description: str
    scope: str
    priority: int
    condition: dict[str, Any]
    action: PolicyAction
    # Action metadata (e.g. {"roles": ["BUSINESS_APPROVER"]} for REQUIRE_APPROVAL).
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime
