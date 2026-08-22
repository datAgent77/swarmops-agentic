"use client";

import { useCallback, useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SystemStatus } from "@/components/overview/system-status";
import { fetchAudit, fetchOrgCurrent, resetDemo, type AuditEvent, type OrgCurrent } from "@/lib/api";
import { relativeTime } from "@/lib/utils";

const TILES: { key: keyof OrgCurrent["stats"]; label: string; hint: string }[] = [
  { key: "total_agents", label: "Agents", hint: "Fleet total" },
  { key: "active", label: "Active", hint: "Currently running" },
  { key: "high_risk", label: "High Risk", hint: "Severity HIGH+" },
  { key: "quarantined", label: "Quarantined", hint: "Governance holds" },
];

const SEVERITY_ROWS = [
  { key: "CRITICAL", label: "Critical", color: "hsl(var(--severity-critical))" },
  { key: "HIGH", label: "High", color: "hsl(var(--severity-high))" },
  { key: "MODERATE", label: "Moderate", color: "hsl(var(--severity-moderate))" },
  { key: "LOW", label: "Low", color: "hsl(var(--severity-low))" },
];

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max ? Math.max(3, Math.round((value / max) * 100)) : 0;
  return (
    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

function decisionVariant(d: string | null): React.ComponentProps<typeof Badge>["variant"] {
  if (!d) return "secondary";
  if (["DENY", "QUARANTINE", "REJECTED", "BLOCKED"].includes(d)) return "critical";
  if (["REQUIRE_APPROVAL", "MODERATE"].includes(d)) return "moderate";
  if (["APPROVED", "ALLOW", "ACTIVATE"].includes(d)) return "low";
  return "secondary";
}

export default function OverviewPage() {
  const [org, setOrg] = useState<OrgCurrent | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [error, setError] = useState(false);
  const [resetting, setResetting] = useState(false);

  const load = useCallback(() => {
    fetchOrgCurrent().then((d) => { setOrg(d); setError(false); }).catch(() => setError(true));
    fetchAudit(8).then((d) => setAudit(d.items)).catch(() => setAudit([]));
  }, []);
  useEffect(() => load(), [load]);

  const onReset = async () => {
    setResetting(true);
    try { await resetDemo(); load(); } finally { setResetting(false); }
  };

  const sev = org?.stats.by_severity ?? {};
  const status = org?.stats.by_status ?? {};
  const sevMax = Math.max(1, ...SEVERITY_ROWS.map((r) => sev[r.key] ?? 0));
  const statusRows = [
    { label: "Active", value: status.ACTIVE ?? 0 },
    { label: "Quarantined", value: status.QUARANTINED ?? 0 },
    { label: "In review", value: status.PENDING_REVIEW ?? 0 },
    {
      label: "Other",
      value: (org?.stats.total_agents ?? 0) - (status.ACTIVE ?? 0) - (status.QUARANTINED ?? 0) - (status.PENDING_REVIEW ?? 0),
    },
  ];
  const statusMax = Math.max(1, ...statusRows.map((r) => r.value));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {org ? `${org.name} — fleet-wide governance posture.` : "Loading fleet posture…"}
        </p>
        <Button variant="outline" size="sm" onClick={onReset} disabled={resetting}>
          <RotateCcw className={resetting ? "h-4 w-4 animate-spin" : "h-4 w-4"} /> Reset Demo
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {TILES.map((tile) => (
          <Card key={tile.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-3xl tabular-nums">
                {error ? "—" : (org?.stats[tile.key] as number | undefined) ?? "…"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">{tile.label}</div>
              <div className="text-xs text-muted-foreground">{tile.hint}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Risk posture</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {SEVERITY_ROWS.map((r) => (
              <div key={r.key} className="flex items-center gap-3">
                <span className="w-16 text-sm text-muted-foreground">{r.label}</span>
                <Bar value={sev[r.key] ?? 0} max={sevMax} color={r.color} />
                <span className="w-8 text-right text-sm tabular-nums">{sev[r.key] ?? 0}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Agent status</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {statusRows.map((r) => (
              <div key={r.label} className="flex items-center gap-3">
                <span className="w-24 text-sm text-muted-foreground">{r.label}</span>
                <Bar value={r.value} max={statusMax} color="hsl(var(--primary))" />
                <span className="w-8 text-right text-sm tabular-nums">{r.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Recent governance activity</CardTitle></CardHeader>
        <CardContent className="divide-y">
          {audit.length === 0 && <p className="py-2 text-sm text-muted-foreground">No activity yet.</p>}
          {audit.map((e) => (
            <div key={e.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2 text-sm">
              <span className="w-20 shrink-0 text-xs text-muted-foreground">{relativeTime(e.timestamp)}</span>
              <span className="font-mono text-xs text-muted-foreground">{e.resource_id}</span>
              <span className="font-medium">{e.action}</span>
              {e.decision && <Badge variant={decisionVariant(e.decision)}>{e.decision}</Badge>}
              {e.reason && <span className="text-muted-foreground">— {e.reason}</span>}
            </div>
          ))}
        </CardContent>
      </Card>

      <SystemStatus />
    </div>
  );
}
