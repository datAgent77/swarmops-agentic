"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchPolicies, type Policy, type PolicyAction, API_URL } from "@/lib/api";

const ACTION_VARIANT: Record<PolicyAction, React.ComponentProps<typeof Badge>["variant"]> = {
  ALLOW: "low",
  LOG_ONLY: "secondary",
  REDACT: "secondary",
  REQUIRE_APPROVAL: "moderate",
  DENY: "critical",
  QUARANTINE: "critical",
};

function roles(p: Policy): string[] {
  const r = (p.parameters as { roles?: string[] }).roles;
  return Array.isArray(r) ? r : [];
}

export function PoliciesList() {
  const [policies, setPolicies] = useState<Policy[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchPolicies()
      .then(setPolicies)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }
  if (!policies) return <p className="text-sm text-muted-foreground">Loading policies…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Deterministic governance rules, evaluated in priority order. No LLM, no{" "}
          <code>eval()</code> — conditions are declarative JSON.
        </p>
        <div className="text-sm text-muted-foreground">{policies.length} policies</div>
      </div>

      {policies.map((p) => (
        <Card key={p.id}>
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">{p.name}</CardTitle>
              <Badge variant={ACTION_VARIANT[p.action]}>{p.action.replace("_", " ")}</Badge>
              <Badge variant="outline">priority {p.priority}</Badge>
              <Badge variant="secondary">{p.scope}</Badge>
              <Badge variant={p.enabled ? "low" : "outline"}>
                {p.enabled ? "enabled" : "disabled"}
              </Badge>
              {roles(p).map((r) => (
                <Badge key={r} variant="moderate">{r}</Badge>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">{p.description}</p>
          </CardHeader>
          <CardContent>
            <div className="text-xs uppercase text-muted-foreground">Condition</div>
            <pre className="mt-1 overflow-x-auto rounded-md bg-muted/50 p-3 text-xs">
              <code>{JSON.stringify(p.condition, null, 2)}</code>
            </pre>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
