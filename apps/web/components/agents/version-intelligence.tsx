"use client";

import { useState } from "react";
import { ArrowRight, GitCompare, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { proposeChange, type ChangeProposalResponse } from "@/lib/api";

function Delta({ label, before, after, pct, good }: {
  label: string; before: number; after: number; pct: number; good: boolean;
}) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="flex items-center gap-2 text-lg font-semibold">
        <span className="text-muted-foreground">{before}</span>
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
        <span>{after}</span>
        <span className={good ? "text-sm text-severity-low" : "text-sm text-severity-critical"}>
          {pct > 0 ? "+" : ""}{pct}%
        </span>
      </div>
    </div>
  );
}

export function VersionIntelligence({ agentId }: { agentId: string }) {
  const [result, setResult] = useState<ChangeProposalResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await proposeChange(agentId));
    } catch {
      setError("No candidate version to evaluate for this agent.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <GitCompare className="h-4 w-4" /> Self-evolving governance
          </CardTitle>
          <Button size="sm" variant={result ? "outline" : "default"} onClick={run} disabled={busy}>
            {busy ? "Evaluating…" : result ? "Re-evaluate candidate" : "Evaluate candidate version"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-muted-foreground">{error}</p>}

        {!result && !error && (
          <p className="text-sm text-muted-foreground">
            Compare the current version to a proposed candidate. A compliance regression is
            rejected deterministically, even when performance improves.
          </p>
        )}

        {result && (
          <>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="outline">{result.proposal.base_version}</Badge>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              <Badge variant="secondary">{result.proposal.candidate_version}</Badge>
              <span className="text-muted-foreground">
                changed: {result.proposal.changes.join(", ") || "nothing"}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <Delta
                label="Performance"
                before={result.proposal.performance_before}
                after={result.proposal.performance_after}
                pct={result.performance_delta_pct}
                good={result.performance_delta_pct >= 0}
              />
              <Delta
                label="Compliance"
                before={result.proposal.compliance_before}
                after={result.proposal.compliance_after}
                pct={result.compliance_delta_pct}
                good={result.compliance_delta_pct >= 0}
              />
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Badge variant={result.proposal.decision === "REJECTED" ? "critical" : "low"}>
                {result.proposal.decision}
              </Badge>
              <span className="text-sm text-muted-foreground">{result.proposal.reason}</span>
            </div>

            <div className="flex items-start gap-2 rounded-md border border-dashed p-3 text-xs text-muted-foreground">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                <span className="font-medium text-foreground">
                  Gemini ({result.explanation.model_status === "LIVE" ? "LIVE" : "local template"}):
                </span>{" "}
                {result.explanation.text} Gemini explains the impact but never approves the change —
                the decision above is deterministic.
              </span>
            </div>

            <p className="text-sm font-medium">Self-evolving agents require self-evolving governance.</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
