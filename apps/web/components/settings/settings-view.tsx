"use client";

import { useCallback, useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  fetchOrgCurrent,
  fetchStatus,
  fetchUsers,
  resetDemo,
  type OrgCurrent,
  type Persona,
  type StatusInfo,
} from "@/lib/api";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}

const ROLE_VARIANT: Record<string, React.ComponentProps<typeof Badge>["variant"]> = {
  PLATFORM_ADMIN: "default",
  SECURITY_OFFICER: "high",
  BUSINESS_APPROVER: "moderate",
  FINANCE_APPROVER: "moderate",
  DEVELOPER: "secondary",
};

export function SettingsView() {
  const [org, setOrg] = useState<OrgCurrent | null>(null);
  const [status, setStatus] = useState<StatusInfo | null>(null);
  const [users, setUsers] = useState<Persona[]>([]);
  const [resetting, setResetting] = useState(false);

  const load = useCallback(() => {
    fetchOrgCurrent().then(setOrg).catch(() => setOrg(null));
    fetchStatus().then(setStatus).catch(() => setStatus(null));
    fetchUsers().then((d) => setUsers(d.items)).catch(() => setUsers([]));
  }, []);
  useEffect(() => load(), [load]);

  const onReset = async () => {
    setResetting(true);
    try {
      await resetDemo();
      load();
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Organization, personas, runtime configuration, and demo controls.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Organization</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Name" value={org?.name ?? "…"} />
            <Field label="Slug" value={org?.slug ?? "…"} />
            <Field label="Fleet size" value={org ? `${org.stats.total_agents} agents` : "…"} />
            <Field label="Created" value={org?.created_at?.slice(0, 10) ?? "…"} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Runtime configuration</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Environment" value={status?.environment ?? "…"} />
            <Field label="Service" value={status ? `${status.service} v${status.version}` : "…"} />
            <Field label="Category" value={status?.category ?? "…"} />
            <Field
              label="Demo mode"
              value={status ? (status.demo_mode ? "On" : "Off") : "…"}
            />
            <div className="sm:col-span-2 text-xs text-muted-foreground">
              Live Google Cloud backend status (Gemini, Vertex AI, ADK, Firestore, Pub/Sub,
              Cloud Trace…) is on the <span className="font-medium text-foreground">Integrations</span> page.
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Personas ({users.length})</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {users.map((u) => (
            <div key={u.id} className="rounded-md border p-3">
              <div className="text-sm font-medium">{u.name}</div>
              <div className="text-xs text-muted-foreground">{u.email}</div>
              <div className="mt-2">
                <Badge variant={ROLE_VARIANT[u.role] ?? "secondary"}>{u.role.replace("_", " ")}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Demo controls</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <Button variant="outline" size="sm" onClick={onReset} disabled={resetting}>
            <RotateCcw className={resetting ? "h-4 w-4 animate-spin" : "h-4 w-4"} /> Reset demo
          </Button>
          <span className="text-sm text-muted-foreground">
            Restores the deterministic SaitALCorp dataset (127 agents · 43 active · 9 high-risk · 3 quarantined).
          </span>
        </CardContent>
      </Card>
    </div>
  );
}
