"use client";

import { useCallback, useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SystemStatus } from "@/components/overview/system-status";
import { fetchOrgCurrent, resetDemo, type OrgCurrent } from "@/lib/api";

const TILES: { key: keyof OrgCurrent["stats"]; label: string; hint: string }[] = [
  { key: "total_agents", label: "Agents", hint: "Fleet total" },
  { key: "active", label: "Active", hint: "Currently running" },
  { key: "high_risk", label: "High Risk", hint: "Severity HIGH+" },
  { key: "quarantined", label: "Quarantined", hint: "Governance holds" },
];

export default function OverviewPage() {
  const [org, setOrg] = useState<OrgCurrent | null>(null);
  const [error, setError] = useState(false);
  const [resetting, setResetting] = useState(false);

  const load = useCallback(() => {
    fetchOrgCurrent()
      .then((data) => {
        setOrg(data);
        setError(false);
      })
      .catch(() => setError(true));
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
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {org ? `${org.name} — fleet-wide governance posture.` : "Loading fleet posture…"}
        </p>
        <Button variant="outline" size="sm" onClick={onReset} disabled={resetting}>
          <RotateCcw className={resetting ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          Reset Demo
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {TILES.map((tile) => (
          <Card key={tile.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-3xl tabular-nums">
                {error ? "—" : (org?.stats[tile.key] ?? "…")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">{tile.label}</div>
              <div className="text-xs text-muted-foreground">{tile.hint}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <SystemStatus />
    </div>
  );
}
