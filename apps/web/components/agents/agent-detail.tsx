"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ShieldAlert, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge, StatusBadge } from "@/components/ui/status-badge";
import { Tabs } from "@/components/ui/tabs";
import { RiskPanel } from "@/components/agents/risk-panel";
import { VersionIntelligence } from "@/components/agents/version-intelligence";
import { AgentGraphPanel } from "@/components/graph/agent-graph-panel";
import { activateAgent, fetchAgent, type AgentDetail as Detail } from "@/lib/api";

// The demo reactivation actor is the platform admin persona (privileged).
const ADMIN_PERSONA = "user-alex-admin";

const TABS = [
  "Overview", "Dependencies", "Versions", "Executions",
  "Policies", "Risk", "Security", "Audit",
];

const FUTURE_TAB: Record<string, string> = {
  Executions: "P04", Policies: "P03", Security: "P10", Audit: "P09",
};

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}

export function AgentDetail({ id }: { id: string }) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activating, setActivating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(() => {
    fetchAgent(id).then(setDetail).catch((e) => setError(String(e)));
  }, [id]);

  useEffect(() => load(), [load]);

  const onActivate = async () => {
    setActivating(true);
    setActionError(null);
    try {
      await activateAgent(id, ADMIN_PERSONA);
      load();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Activation failed");
    } finally {
      setActivating(false);
    }
  };

  if (error) {
    return <div className="text-sm text-severity-critical">Agent not found or backend unreachable.</div>;
  }
  if (!detail) {
    return <div className="text-sm text-muted-foreground">Loading agent…</div>;
  }

  const { agent, versions, dependencies } = detail;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/agents" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Agents
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-semibold tracking-tight">{agent.name}</h2>
          <StatusBadge status={agent.status} />
          <SeverityBadge severity={agent.severity} />
          <Badge variant="outline">{agent.current_version}</Badge>
        </div>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{agent.description}</p>
      </div>

      {agent.status === "QUARANTINED" && (
        <Card className="border-severity-critical/40 bg-severity-critical/5">
          <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-severity-critical" />
              <div>
                <div className="font-medium">Why was this agent quarantined?</div>
                <p className="text-sm text-muted-foreground">
                  {agent.quarantine_reason ?? "Held under governance."} New executions are blocked
                  until a privileged operator reactivates it.
                </p>
                {actionError && <p className="mt-1 text-sm text-severity-critical">{actionError}</p>}
              </div>
            </div>
            <Button size="sm" variant="outline" onClick={onActivate} disabled={activating}>
              <ShieldCheck className="h-4 w-4" /> Reactivate
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs tabs={TABS}>
        {(active) => {
          if (active === "Overview") {
            return (
              <Card>
                <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-3">
                  <Field label="Department" value={agent.department} />
                  <Field label="Owner" value={agent.owner_id} />
                  <Field label="Autonomy" value={agent.autonomy_level} />
                  <Field label="Risk Score" value={`${agent.risk_score} / 100`} />
                  <Field label="Framework" value={agent.framework} />
                  <Field label="Runtime" value={agent.runtime} />
                  <Field label="Model" value={`${agent.model_provider} · ${agent.model_name}`} />
                  <Field label="Created" value={agent.created_at.slice(0, 10)} />
                  <Field label="Updated" value={agent.updated_at.slice(0, 10)} />
                </CardContent>
              </Card>
            );
          }
          if (active === "Dependencies") {
            return (
              <div className="space-y-4">
                <AgentGraphPanel agentId={agent.id} />
                {dependencies.length > 0 && (
                  <Card className="overflow-hidden">
                    <table className="w-full text-sm">
                  <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Target</th>
                      <th className="px-4 py-3 font-medium">Type</th>
                      <th className="px-4 py-3 font-medium">Relationship</th>
                      <th className="px-4 py-3 font-medium">Risk</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {dependencies.map((d) => (
                      <tr key={d.id}>
                        <td className="px-4 py-3 font-medium">{d.target_id}</td>
                        <td className="px-4 py-3 text-muted-foreground">{d.target_type}</td>
                        <td className="px-4 py-3 text-muted-foreground">{d.relationship}</td>
                        <td className="px-4 py-3"><SeverityBadge severity={d.risk_level} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                  </Card>
                )}
              </div>
            );
          }
          if (active === "Risk") {
            return <RiskPanel agentId={agent.id} />;
          }
          if (active === "Versions") {
            return (
              <div className="space-y-4">
                <VersionIntelligence agentId={agent.id} />
                {versions.length > 0 && (
                  <div className="space-y-3">
                {versions.map((v) => (
                  <Card key={v.id}>
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center gap-2 text-base">
                        {v.version}
                        <Badge variant="secondary">{v.model}</Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="text-muted-foreground">{v.system_prompt_summary}</div>
                      <Field label="Tools" value={v.tools.join(", ") || "—"} />
                      <Field label="Permissions" value={v.permissions.join(", ") || "—"} />
                      <Field label="Prompt hash" value={<code className="font-mono text-xs">{v.system_prompt_hash}</code>} />
                    </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            );
          }
          return (
            <p className="text-sm text-muted-foreground">
              This tab is populated in {FUTURE_TAB[active] ?? "a later phase"}.
            </p>
          );
        }}
      </Tabs>
    </div>
  );
}
