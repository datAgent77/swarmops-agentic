"use client";

import { useEffect, useState } from "react";
import { Activity, GitBranch } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  fetchExecutions,
  fetchObservabilityOverview,
  fetchTrace,
  type Execution,
  type ObservabilityOverview,
  type TraceResponse,
  API_URL,
} from "@/lib/api";

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-2xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm font-medium">{label}</div>
        {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
      </CardContent>
    </Card>
  );
}

export function ObservabilityView() {
  const [ov, setOv] = useState<ObservabilityOverview | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchObservabilityOverview().then(setOv).catch(() => setError(true));
    fetchExecutions().then((d) => setExecutions(d.items)).catch(() => setError(true));
    const param = new URLSearchParams(window.location.search).get("trace");
    if (param) fetchTrace(param).then(setTrace).catch(() => setTrace(null));
  }, []);

  const loadTrace = (traceId: string) => {
    fetchTrace(traceId).then(setTrace).catch(() => setTrace(null));
  };

  if (error && !ov) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile label="Executions" value={String(ov?.total_executions ?? "…")} hint="total" />
        <Tile label="Completed" value={String(ov?.completed ?? "…")} hint={`${ov?.blocked ?? 0} blocked · ${ov?.failed ?? 0} failed`} />
        <Tile label="Error rate" value={ov ? `${(ov.error_rate * 100).toFixed(0)}%` : "…"} hint="blocked + failed" />
        <Tile label="Avg latency" value={ov ? `${ov.avg_latency_ms} ms` : "…"} hint="completed executions" />
        <Tile label="Policy violations" value={String(ov?.policy_violations ?? "…")} hint="DENY / QUARANTINE" />
        <Tile label="Est. spend" value={ov ? `$${ov.estimated_spend.toFixed(4)}` : "…"} hint="tool + model cost" />
        <Tile label="Approval wait" value={ov ? `${ov.avg_approval_wait_ms} ms` : "…"} hint="avg time to resolve" />
        <Tile label="Audit events" value={String(ov?.audit_event_count ?? "…")} hint={`telemetry: ${ov?.telemetry_backend ?? "…"}`} />
      </div>

      {ov?.token_usage == null && (
        <p className="text-xs text-muted-foreground">
          Token usage is not tracked yet (reported honestly as unavailable).
          Telemetry backend: <span className="font-medium">{ov?.telemetry_backend}</span>.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <GitBranch className="h-4 w-4" /> Recent traces
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {executions.length === 0 && (
              <p className="text-sm text-muted-foreground">No executions yet.</p>
            )}
            {executions.slice(0, 12).map((e) => (
              <button
                key={e.id}
                onClick={() => loadTrace(e.trace_id)}
                className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-accent"
              >
                <span className="font-mono text-xs">{e.trace_id.slice(0, 16)}</span>
                <Badge variant="secondary">{e.status}</Badge>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4" /> Execution trace
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!trace ? (
              <p className="text-sm text-muted-foreground">
                Select a trace to see its end-to-end reasoning chain.
              </p>
            ) : (
              <div className="space-y-0">
                <div className="mb-3 text-xs text-muted-foreground">
                  {trace.execution_id} · {trace.status} · {trace.duration_ms ?? "—"} ms
                </div>
                <ol className="relative space-y-4 border-l pl-5">
                  {trace.steps.map((s, i) => (
                    <li key={i} className="relative">
                      <span className="absolute -left-[23px] top-1 h-2.5 w-2.5 rounded-full bg-primary" />
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium">{s.name}</span>
                        {s.decision && <Badge variant="secondary">{s.decision}</Badge>}
                        <span className="text-xs text-muted-foreground">
                          {s.timestamp.slice(11, 19)}
                        </span>
                      </div>
                      {s.reason && <div className="text-xs text-muted-foreground">{s.reason}</div>}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
