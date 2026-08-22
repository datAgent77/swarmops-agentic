// Typed client for the SwarmOps backend. All calls run in the browser against
// NEXT_PUBLIC_API_URL so the app builds without a running backend.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

export type Severity = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type AgentStatus =
  | "DISCOVERED"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "ACTIVE"
  | "SUSPENDED"
  | "QUARANTINED"
  | "RETIRED";

export type Agent = {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  owner_id: string;
  department: string;
  status: AgentStatus;
  autonomy_level: "LOW" | "MEDIUM" | "HIGH";
  risk_score: number;
  current_version: string;
  runtime: string;
  framework: string;
  model_provider: string;
  model_name: string;
  created_at: string;
  updated_at: string;
  quarantine_reason: string | null;
  severity: Severity;
};

export type DiscoveryResult = {
  agent_id: string;
  name: string;
  from_status: string;
  to_status: string;
  risk_score: number;
  quarantined: boolean;
  reason: string;
  already_processed: boolean;
};

export type AgentVersion = {
  id: string;
  agent_id: string;
  version: string;
  system_prompt_hash: string;
  system_prompt_summary: string;
  tools: string[];
  permissions: string[];
  data_sources: string[];
  model: string;
  configuration: Record<string, unknown>;
  created_by: string;
  created_at: string;
};

export type AgentDependency = {
  id: string;
  source_agent_id: string;
  target_type: string;
  target_id: string;
  relationship: string;
  risk_level: Severity;
};

export type AgentDetail = {
  agent: Agent;
  versions: AgentVersion[];
  dependencies: AgentDependency[];
};

export type RecommendedAction =
  | "ALLOW"
  | "MONITOR"
  | "REQUIRE_APPROVAL"
  | "SUSPEND"
  | "QUARANTINE";

export type RiskAssessment = {
  id: string;
  agent_id: string;
  agent_version_id: string | null;
  overall_score: number;
  severity: Severity;
  pii_score: number;
  financial_score: number;
  external_tool_score: number;
  privilege_score: number;
  autonomy_score: number;
  prompt_score: number;
  data_score: number;
  drivers: string[];
  recommended_action: RecommendedAction;
  created_at: string;
};

export type ExecutionStatus =
  | "QUEUED"
  | "RUNNING"
  | "WAITING_APPROVAL"
  | "BLOCKED"
  | "FAILED"
  | "COMPLETED"
  | "CANCELLED";

export type Execution = {
  id: string;
  agent_id: string;
  agent_version_id: string | null;
  status: ExecutionStatus;
  input_summary: string;
  output_summary: string | null;
  risk_context: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  trace_id: string;
  estimated_cost: number;
};

export type ToolCall = {
  id: string;
  execution_id: string;
  tool_id: string;
  arguments_summary: string;
  result_summary: string;
  policy_decision: string | null;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  idempotency_key: string | null;
};

export type ExecutionDetail = {
  execution: Execution;
  tool_calls: ToolCall[];
};

export type GraphNode = {
  id: string;
  type: string;
  label: string;
  risk_level: string | null;
  connection: string;
  meta: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  relationship: string;
  risk_level: string;
  dangerous: boolean;
};

export type GraphResponse = { nodes: GraphNode[]; edges: GraphEdge[] };

export type BlastRadius = {
  agent_id: string;
  pii_reachable: boolean;
  financial_action_reachable: boolean;
  production_write_path: boolean;
  external_exfiltration_path: boolean;
  privileged_downstream_agents: string[];
  reachable_nodes: number;
  indicators: string[];
};

export type AuditEvent = {
  id: string;
  organization_id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  decision: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
  trace_id: string | null;
  timestamp: string;
};

export type ObservabilityOverview = {
  total_executions: number;
  by_status: Record<string, number>;
  completed: number;
  failed: number;
  blocked: number;
  error_rate: number;
  avg_latency_ms: number;
  policy_violations: number;
  estimated_spend: number;
  token_usage: number | null;
  avg_approval_wait_ms: number;
  audit_event_count: number;
  telemetry_backend: string;
};

export type TraceStep = {
  name: string;
  kind: string;
  decision: string | null;
  reason: string | null;
  timestamp: string;
  metadata: Record<string, unknown>;
};

export type TraceResponse = {
  trace_id: string;
  execution_id: string | null;
  status: string | null;
  duration_ms: number | null;
  steps: TraceStep[];
};

export type SecurityScanResult = {
  verdict: "BLOCK" | "ALLOW";
  severity: string;
  categories: string[];
  findings: { category: string; severity: string; label: string; excerpt: string }[];
  scanner: string;
  scanner_status: "LIVE" | "LOCAL_DEMO";
  incident_id: string | null;
  policy_id: string | null;
};

export type SecurityIncident = {
  id: string;
  source: string;
  agent_id: string | null;
  category: string;
  severity: string;
  action: string;
  input_excerpt: string;
  detected_categories: string[];
  scanner: string;
  scanner_status: string;
  policy_id: string | null;
  resolved: boolean;
  created_at: string;
};

export type SecurityOverview = {
  scanner_status: "LIVE" | "LOCAL_DEMO";
  open_critical_findings: number;
  prompt_injection_attempts: number;
  pii_leakage_attempts: number;
  blocked_tool_calls: number;
  quarantined_agents: number;
  total_incidents: number;
};

export type ChangeProposal = {
  id: string;
  agent_id: string;
  base_version: string;
  candidate_version: string;
  change_type: string;
  changes: string[];
  old_summary: string;
  new_summary: string;
  performance_before: number;
  performance_after: number;
  compliance_before: number;
  compliance_after: number;
  decision: "PENDING" | "ACCEPTED" | "REJECTED";
  reason: string;
  created_at: string;
};

export type ChangeProposalResponse = {
  proposal: ChangeProposal;
  performance_delta_pct: number;
  compliance_delta_pct: number;
  explanation: { text: string; model_status: "LIVE" | "LOCAL_TEMPLATE"; model_name: string; provider: string };
};

export type IntegrationInfo = {
  key: string;
  name: string;
  category: string;
  status: "CONNECTED" | "DEMO_MODE" | "NOT_CONFIGURED" | "ERROR";
  detail: string;
  docs: string;
};

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";

export type ApprovalRequest = {
  id: string;
  execution_id: string;
  policy_id: string | null;
  requested_from_role: string;
  sequence: number;
  status: ApprovalStatus;
  reason: string;
  context: Record<string, unknown>;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
};

export type PolicyAction =
  | "ALLOW"
  | "DENY"
  | "REQUIRE_APPROVAL"
  | "QUARANTINE"
  | "REDACT"
  | "LOG_ONLY";

export type Policy = {
  id: string;
  name: string;
  description: string;
  scope: string;
  priority: number;
  condition: Record<string, unknown>;
  action: PolicyAction;
  parameters: Record<string, unknown>;
  enabled: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type FleetStats = {
  total_agents: number;
  active: number;
  high_risk: number;
  quarantined: number;
};

export type OrgCurrent = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  stats: FleetStats;
};

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export type AgentFilters = {
  status?: string;
  department?: string;
  risk?: Severity;
  search?: string;
};

export type StatusInfo = {
  service: string;
  version: string;
  environment: string;
  demo_mode: boolean;
  category: string;
  tagline: string;
};

export function fetchStatus() {
  return getJSON<StatusInfo>("/api/v1/status");
}

export function fetchOrgCurrent() {
  return getJSON<OrgCurrent>("/api/v1/organizations/current");
}

export function fetchAgents(filters: AgentFilters = {}) {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v) params.set(k, v);
  }
  const qs = params.toString();
  return getJSON<{ total: number; items: Agent[] }>(`/api/v1/agents${qs ? `?${qs}` : ""}`);
}

export function fetchAgent(id: string) {
  return getJSON<AgentDetail>(`/api/v1/agents/${id}`);
}

export function fetchPolicies() {
  return getJSON<Policy[]>("/api/v1/policies");
}

export async function discoverAgents() {
  const res = await fetch(`${API_URL}/api/v1/agents/discover`, { method: "POST" });
  if (!res.ok) throw new Error(`discover → HTTP ${res.status}`);
  return (await res.json()) as { discovered: DiscoveryResult[] };
}

export async function activateAgent(agentId: string, actorUserId: string) {
  const res = await fetch(`${API_URL}/api/v1/agents/${agentId}/activate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ actor_user_id: actorUserId }),
  });
  if (res.status === 403) throw new Error("This persona is not authorized to reactivate agents.");
  if (!res.ok) throw new Error(`activate → HTTP ${res.status}`);
  return (await res.json()) as Agent;
}

export function fetchExecutions() {
  return getJSON<{ total: number; items: Execution[] }>("/api/v1/executions");
}

export function fetchExecution(id: string) {
  return getJSON<ExecutionDetail>(`/api/v1/executions/${id}`);
}

export async function createExecution(
  agentId: string,
  inputSummary: string,
  toolCalls: { tool: string; arguments?: Record<string, unknown>; idempotency_key?: string }[],
): Promise<ExecutionDetail> {
  const res = await fetch(`${API_URL}/api/v1/executions`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ agent_id: agentId, input_summary: inputSummary, tool_calls: toolCalls }),
  });
  if (res.status === 409) throw new Error("Agent is quarantined and cannot execute.");
  if (!res.ok) throw new Error(`execution → HTTP ${res.status}`);
  return res.json() as Promise<ExecutionDetail>;
}

export function fetchFleetGraph() {
  return getJSON<GraphResponse>("/api/v1/graph");
}

export function fetchAgentGraph(agentId: string) {
  return getJSON<GraphResponse>(`/api/v1/agents/${agentId}/graph`);
}

export function fetchBlastRadius(agentId: string) {
  return getJSON<BlastRadius>(`/api/v1/agents/${agentId}/blast-radius`);
}

export function fetchAudit(limit = 200) {
  return getJSON<{ total: number; items: AuditEvent[] }>(`/api/v1/audit?limit=${limit}`);
}

export function fetchObservabilityOverview() {
  return getJSON<ObservabilityOverview>("/api/v1/observability/overview");
}

export function fetchTrace(traceId: string) {
  return getJSON<TraceResponse>(`/api/v1/observability/traces/${traceId}`);
}

export async function scanSecurity(text: string): Promise<SecurityScanResult> {
  const res = await fetch(`${API_URL}/api/v1/security/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`scan → HTTP ${res.status}`);
  return res.json() as Promise<SecurityScanResult>;
}

export function fetchSecurityIncidents() {
  return getJSON<{ total: number; items: SecurityIncident[] }>("/api/v1/security/incidents");
}

export function fetchSecurityOverview() {
  return getJSON<SecurityOverview>("/api/v1/security/overview");
}

export function fetchIntegrations() {
  return getJSON<{ integrations: IntegrationInfo[] }>("/api/v1/integrations/status");
}

export async function proposeChange(agentId: string): Promise<ChangeProposalResponse> {
  const res = await fetch(`${API_URL}/api/v1/agents/${agentId}/change-proposals`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`propose → HTTP ${res.status}`);
  return res.json() as Promise<ChangeProposalResponse>;
}

export function fetchProposals(agentId: string) {
  return getJSON<{ total: number; items: ChangeProposal[] }>(
    `/api/v1/agents/${agentId}/change-proposals`,
  );
}

export type Persona = { id: string; name: string; email: string; role: string };

export function fetchUsers() {
  return getJSON<{ items: Persona[] }>("/api/v1/users");
}

export function fetchApprovals(status?: ApprovalStatus) {
  const qs = status ? `?status=${status}` : "";
  return getJSON<{ items: ApprovalRequest[] }>(`/api/v1/approvals${qs}`);
}

async function approvalAction(id: string, action: "approve" | "reject", actorUserId: string) {
  const res = await fetch(`${API_URL}/api/v1/approvals/${id}/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ actor_user_id: actorUserId }),
  });
  if (res.status === 403) throw new Error("This persona does not hold the required role.");
  if (!res.ok) throw new Error(`${action} → HTTP ${res.status}`);
  return res.json() as Promise<ApprovalRequest>;
}

export const approveRequest = (id: string, actor: string) => approvalAction(id, "approve", actor);
export const rejectRequest = (id: string, actor: string) => approvalAction(id, "reject", actor);

export async function fetchRisk(agentId: string): Promise<RiskAssessment | null> {
  const res = await fetch(`${API_URL}/api/v1/agents/${agentId}/risk`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`risk → HTTP ${res.status}`);
  return res.json() as Promise<RiskAssessment>;
}

export async function assessRisk(agentId: string): Promise<RiskAssessment> {
  const res = await fetch(`${API_URL}/api/v1/agents/${agentId}/assess-risk`, { method: "POST" });
  if (!res.ok) throw new Error(`assess-risk → HTTP ${res.status}`);
  return res.json() as Promise<RiskAssessment>;
}

export type GovernanceAnalysis = {
  risk: RiskAssessment;
  policy: {
    matched: boolean;
    action: PolicyAction;
    policy_id: string | null;
    policy_name: string | null;
    required_roles: string[];
    reason: string;
  };
  explanation: {
    text: string;
    model_status: "LIVE" | "LOCAL_TEMPLATE";
    model_name: string;
    provider: string;
  };
};

export async function runGovernanceAnalysis(agentId: string): Promise<GovernanceAnalysis> {
  const res = await fetch(`${API_URL}/api/v1/agents/${agentId}/governance-analysis`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action_context: {} }),
  });
  if (!res.ok) throw new Error(`governance-analysis → HTTP ${res.status}`);
  return res.json() as Promise<GovernanceAnalysis>;
}

export async function resetDemo() {
  const res = await fetch(`${API_URL}/api/v1/demo/reset`, { method: "POST" });
  if (!res.ok) throw new Error(`reset → HTTP ${res.status}`);
  return res.json() as Promise<{ status: string; total_agents: number }>;
}

// Map a severity band to the Badge variant of the same name.
export function severityVariant(sev: Severity): "low" | "moderate" | "high" | "critical" {
  return sev.toLowerCase() as "low" | "moderate" | "high" | "critical";
}
