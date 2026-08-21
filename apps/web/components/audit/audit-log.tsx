"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchAudit, type AuditEvent, API_URL } from "@/lib/api";

function decisionVariant(d: string | null): React.ComponentProps<typeof Badge>["variant"] {
  if (!d) return "secondary";
  if (["DENY", "QUARANTINE", "REJECTED", "BLOCKED"].includes(d)) return "critical";
  if (["REQUIRE_APPROVAL"].includes(d)) return "moderate";
  if (["APPROVED", "ALLOW", "ACTIVATE"].includes(d)) return "low";
  return "secondary";
}

export function AuditLog() {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState(false);

  const load = () => {
    fetchAudit(300).then((d) => setEvents(d.items)).catch(() => setError(true));
  };
  useEffect(load, []);

  if (error) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Append-only record of every governance decision, approval, and tool call.
        </p>
        <Button size="sm" variant="outline" onClick={load}>
          <RotateCcw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Timestamp</th>
                <th className="px-4 py-3 font-medium">Actor</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Resource</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">Reason</th>
                <th className="px-4 py-3 font-medium">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {(events ?? []).map((e) => (
                <tr key={e.id} className="hover:bg-accent/40">
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {e.timestamp.slice(0, 19).replace("T", " ")}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {e.actor_id ?? e.actor_type}
                  </td>
                  <td className="px-4 py-3 font-medium">{e.action}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {e.resource_type}:{e.resource_id.slice(0, 18)}
                  </td>
                  <td className="px-4 py-3">
                    {e.decision ? <Badge variant={decisionVariant(e.decision)}>{e.decision}</Badge> : "—"}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-muted-foreground">{e.reason ?? "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {e.trace_id ? (
                      <Link href={`/observability?trace=${e.trace_id}`} className="text-primary hover:underline">
                        {e.trace_id.slice(0, 12)}
                      </Link>
                    ) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {events === null && <div className="p-6 text-sm text-muted-foreground">Loading audit log…</div>}
        {events?.length === 0 && (
          <div className="p-6 text-sm text-muted-foreground">
            No audit events yet. Run an execution or discover an agent to generate some.
          </div>
        )}
      </Card>
    </div>
  );
}
