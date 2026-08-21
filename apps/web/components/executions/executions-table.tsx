"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/card";
import { ExecStatusBadge } from "@/components/ui/status-badge";
import { fetchExecutions, type Execution, API_URL } from "@/lib/api";

function duration(ms: number | null): string {
  if (ms === null) return "—";
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function ExecutionsTable() {
  const [rows, setRows] = useState<Execution[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchExecutions()
      .then((d) => setRows(d.items))
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }
  if (!rows) return <p className="text-sm text-muted-foreground">Loading executions…</p>;

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Execution</th>
              <th className="px-4 py-3 font-medium">Agent</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Started</th>
              <th className="px-4 py-3 font-medium">Duration</th>
              <th className="px-4 py-3 font-medium">Risk</th>
              <th className="px-4 py-3 font-medium">Trace</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((e) => (
              <tr key={e.id} className="hover:bg-accent/40">
                <td className="px-4 py-3">
                  <Link href={`/executions/${e.id}`} className="font-medium hover:text-primary">
                    {e.id}
                  </Link>
                  <div className="max-w-xs truncate text-xs text-muted-foreground">{e.input_summary}</div>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{e.agent_id}</td>
                <td className="px-4 py-3"><ExecStatusBadge status={e.status} /></td>
                <td className="px-4 py-3 text-muted-foreground">
                  {e.started_at ? e.started_at.slice(0, 19).replace("T", " ") : "—"}
                </td>
                <td className="px-4 py-3 tabular-nums text-muted-foreground">{duration(e.duration_ms)}</td>
                <td className="px-4 py-3 text-muted-foreground">{e.risk_context ?? "—"}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{e.trace_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <div className="p-6 text-sm text-muted-foreground">
          No executions yet. They appear here once an agent runs. The guided demo (P14) triggers
          the full governed refund flow.
        </div>
      )}
    </Card>
  );
}
