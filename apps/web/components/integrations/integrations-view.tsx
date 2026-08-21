"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchIntegrations, type IntegrationInfo, API_URL } from "@/lib/api";

const STATUS_VARIANT: Record<IntegrationInfo["status"], React.ComponentProps<typeof Badge>["variant"]> = {
  CONNECTED: "low",
  DEMO_MODE: "moderate",
  NOT_CONFIGURED: "outline",
  ERROR: "critical",
};

const STATUS_LABEL: Record<IntegrationInfo["status"], string> = {
  CONNECTED: "CONNECTED",
  DEMO_MODE: "DEMO MODE",
  NOT_CONFIGURED: "NOT CONFIGURED",
  ERROR: "ERROR",
};

// Category display order.
const ORDER = [
  "Model", "Framework", "Discovery & Lifecycle", "Core Execution & State",
  "Security & Governance", "Telemetry", "Infrastructure",
];

export function IntegrationsView() {
  const [items, setItems] = useState<IntegrationInfo[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchIntegrations().then((d) => setItems(d.integrations)).catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }
  if (!items) return <p className="text-sm text-muted-foreground">Loading integrations…</p>;

  const categories = [...new Set(items.map((i) => i.category))].sort(
    (a, b) => ORDER.indexOf(a) - ORDER.indexOf(b),
  );

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Truthful status of every Google integration. A demo provider is never shown as connected —
        <span className="font-medium text-foreground"> DEMO MODE</span> means SwarmOps provides a
        local substitute; <span className="font-medium text-foreground">NOT CONFIGURED</span> means
        the capability is off.
      </p>

      {categories.map((cat) => (
        <div key={cat} className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground">{cat}</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {items.filter((i) => i.category === cat).map((i) => (
              <Card key={i.key}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{i.name}</CardTitle>
                    <Badge variant={STATUS_VARIANT[i.status]}>{STATUS_LABEL[i.status]}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm text-muted-foreground">{i.detail}</p>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">Enable:</span> {i.docs}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
