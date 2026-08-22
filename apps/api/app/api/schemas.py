"""Response contracts for the foundational endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import PolicyAction
from app.domain.models import (
    Agent,
    AgentChangeProposal,
    AgentDependency,
    AgentVersion,
    ApprovalRequest,
    AuditEvent,
    Execution,
    RiskAssessment,
    SecurityIncident,
    ToolCall,
    User,
)


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
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)


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


class ApprovalListResponse(BaseModel):
    items: list[ApprovalRequest]


class ApprovalActionRequest(BaseModel):
    actor_user_id: str = Field(description="Persona acting; the backend validates its role.")


class DiscoveryResultOut(BaseModel):
    agent_id: str
    name: str
    from_status: str
    to_status: str
    risk_score: int
    quarantined: bool
    reason: str
    already_processed: bool


class DiscoverResponse(BaseModel):
    discovered: list[DiscoveryResultOut]


class QuarantineRequest(BaseModel):
    actor_user_id: str
    reason: str = "manually quarantined"


class ActivateRequest(BaseModel):
    actor_user_id: str


class GovernanceAnalysisRequest(BaseModel):
    # Optional extra policy context (e.g. a proposed action) merged into evaluation.
    action_context: dict[str, Any] = Field(default_factory=dict)


class ExplanationOut(BaseModel):
    text: str
    model_status: str
    model_name: str
    provider: str


class GovernanceAnalysisResponse(BaseModel):
    risk: RiskAssessment
    policy: PolicyDecisionOut
    explanation: ExplanationOut


class GraphNodeOut(BaseModel):
    id: str
    type: str
    label: str
    risk_level: str | None = None
    connection: str = "metadata"
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    risk_level: str
    dangerous: bool


class GraphResponse(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


class BlastRadiusResponse(BaseModel):
    agent_id: str
    pii_reachable: bool
    financial_action_reachable: bool
    production_write_path: bool
    external_exfiltration_path: bool
    privileged_downstream_agents: list[str]
    reachable_nodes: int
    indicators: list[str]


class AuditListResponse(BaseModel):
    total: int
    items: list[AuditEvent]


class ObservabilityOverviewOut(BaseModel):
    total_executions: int
    by_status: dict[str, int]
    completed: int
    failed: int
    blocked: int
    error_rate: float
    avg_latency_ms: float
    policy_violations: int
    estimated_spend: float
    token_usage: int | None
    avg_approval_wait_ms: float
    audit_event_count: int
    telemetry_backend: str


class TraceStepOut(BaseModel):
    name: str
    kind: str
    decision: str | None
    reason: str | None
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceResponse(BaseModel):
    trace_id: str
    execution_id: str | None
    status: str | None
    duration_ms: int | None
    steps: list[TraceStepOut]


class SecurityScanRequest(BaseModel):
    text: str
    source: str = "manual"
    agent_id: str | None = None


class SecurityScanResponse(BaseModel):
    verdict: str
    severity: str
    categories: list[str]
    findings: list[dict[str, Any]]
    scanner: str
    scanner_status: str
    incident_id: str | None
    policy_id: str | None


class SecurityIncidentListResponse(BaseModel):
    total: int
    items: list[SecurityIncident]


class SecurityOverviewOut(BaseModel):
    scanner_status: str
    open_critical_findings: int
    prompt_injection_attempts: int
    pii_leakage_attempts: int
    blocked_tool_calls: int
    quarantined_agents: int
    total_incidents: int


class ChangeProposalCreate(BaseModel):
    candidate_version: str | None = None
    allowed_regression: int = 5


class ProposalEvaluateRequest(BaseModel):
    allowed_regression: int = 5


class ChangeProposalResponse(BaseModel):
    proposal: AgentChangeProposal
    performance_delta_pct: float
    compliance_delta_pct: float
    explanation: ExplanationOut


class ChangeProposalListResponse(BaseModel):
    total: int
    items: list[AgentChangeProposal]


class IntegrationInfoOut(BaseModel):
    key: str
    name: str
    category: str
    status: str
    detail: str
    docs: str


class IntegrationStatusResponse(BaseModel):
    integrations: list[IntegrationInfoOut]
