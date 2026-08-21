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
