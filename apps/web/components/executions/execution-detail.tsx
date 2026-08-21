"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExecStatusBadge } from "@/components/ui/status-badge";
import { fetchExecution, type ExecutionDetail as Detail } from "@/lib/api";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}

export function ExecutionDetail({ id }: { id: string }) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchExecution(id).then(setDetail).catch(() => setError(true));
  }, [id]);

  if (error) return <div className="text-sm text-severity-critical">Execution not found.</div>;
  if (!detail) return <div className="text-sm text-muted-foreground">Loading execution…</div>;

  const { execution: e, tool_calls } = detail;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/executions" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Executions
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-mono text-lg font-semibold">{e.id}</h2>
          <ExecStatusBadge status={e.status} />
          <Badge variant="outline">{e.trace_id}</Badge>
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Agent" value={<Link href={`/agents/${e.agent_id}`} className="hover:text-primary">{e.agent_id}</Link>} />
          <Field label="Version" value={e.agent_version_id ?? "—"} />
          <Field label="Risk context" value={e.risk_context ?? "—"} />
          <Field label="Duration" value={e.duration_ms === null ? "—" : `${e.duration_ms} ms`} />
          <Field label="Estimated cost" value={`$${e.estimated_cost.toFixed(4)}`} />
          <Field label="Input" value={e.input_summary} />
          <Field label="Output" value={<code className="text-xs">{e.output_summary ?? "—"}</code>} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Tool calls ({tool_calls.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {tool_calls.length === 0 && <p className="text-sm text-muted-foreground">No tool calls.</p>}
          {tool_calls.map((t) => (
            <div key={t.id} className="rounded-md border p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm font-medium">{t.tool_id}</span>
                {t.policy_decision && <Badge variant="secondary">{t.policy_decision}</Badge>}
                {t.idempotency_key && <Badge variant="outline">key: {t.idempotency_key}</Badge>}
                <span className="ml-auto text-xs text-muted-foreground">{t.duration_ms} ms</span>
              </div>
              <div className="mt-2 grid gap-1 text-xs">
                <div className="text-muted-foreground">args: <code>{t.arguments_summary}</code></div>
                <div className="text-muted-foreground">result: <code>{t.result_summary}</code></div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
