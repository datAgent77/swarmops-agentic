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
  severity: Severity;
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

export async function resetDemo() {
  const res = await fetch(`${API_URL}/api/v1/demo/reset`, { method: "POST" });
  if (!res.ok) throw new Error(`reset → HTTP ${res.status}`);
  return res.json() as Promise<{ status: string; total_agents: number }>;
}

// Map a severity band to the Badge variant of the same name.
export function severityVariant(sev: Severity): "low" | "moderate" | "high" | "critical" {
  return sev.toLowerCase() as "low" | "moderate" | "high" | "critical";
}
