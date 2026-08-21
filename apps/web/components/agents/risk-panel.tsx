"use client";

import { useEffect, useState } from "react";
import { Bot, ShieldAlert, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge } from "@/components/ui/status-badge";
import {
  assessRisk,
  fetchRisk,
  runGovernanceAnalysis,
  type GovernanceAnalysis,
  type RiskAssessment,
} from "@/lib/api";

// Dimension → assessment field + cap. Labels match the engine's weighting.
const DIMENSIONS: { label: string; key: keyof RiskAssessment; cap: number }[] = [
  { label: "PII access", key: "pii_score", cap: 20 },
  { label: "Financial capabilities", key: "financial_score", cap: 20 },
  { label: "Production write access", key: "privilege_score", cap: 15 },
  { label: "Agent autonomy", key: "autonomy_score", cap: 15 },
  { label: "External tools", key: "external_tool_score", cap: 10 },
  { label: "Missing approval gates", key: "data_score", cap: 10 },
  { label: "Prompt / tool security", key: "prompt_score", cap: 10 },
];

function Bar({ value, cap }: { value: number; cap: number }) {
  const pct = Math.round((value / cap) * 100);
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function RiskPanel({ agentId }: { agentId: string }) {
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [gov, setGov] = useState<GovernanceAnalysis | null>(null);
  const [govBusy, setGovBusy] = useState(false);

  useEffect(() => {
    fetchRisk(agentId)
      .then(setRisk)
      .catch(() => setRisk(null))
      .finally(() => setLoaded(true));
  }, [agentId]);

  const runAssessment = async () => {
    setBusy(true);
    try {
      setRisk(await assessRisk(agentId));
    } finally {
      setBusy(false);
    }
  };

  const runGovernance = async () => {
    setGovBusy(true);
    try {
      const result = await runGovernanceAnalysis(agentId);
      setGov(result);
      setRisk(result.risk); // analysis also (re)computes the deterministic assessment
    } finally {
      setGovBusy(false);
    }
  };

  if (!loaded) return <div className="text-sm text-muted-foreground">Loading risk…</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Deterministic Risk Decision</span> —
          computed by the engine. The Gemini explanation below never changes it.
        </div>
        <Button size="sm" variant={risk ? "outline" : "default"} onClick={runAssessment} disabled={busy}>
          <ShieldAlert className={busy ? "h-4 w-4 animate-pulse" : "h-4 w-4"} />
          {risk ? "Re-assess" : "Run risk assessment"}
        </Button>
      </div>

      {!risk ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No deterministic assessment yet. Run one to compute the 0–100 score.
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-5xl tabular-nums">{risk.overall_score}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-xs text-muted-foreground">out of 100</div>
                <SeverityBadge severity={risk.severity} />
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Recommended action</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Badge variant={risk.recommended_action === "QUARANTINE" ? "critical" : "moderate"}>
                  {risk.recommended_action.replace("_", " ")}
                </Badge>
                <ul className="space-y-1 text-sm">
                  {risk.drivers.map((d) => (
                    <li key={d} className="flex items-center gap-2 text-muted-foreground">
                      <span className="h-1.5 w-1.5 rounded-full bg-severity-high" />
                      {d}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Score breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {DIMENSIONS.map((dim) => {
                const value = risk[dim.key] as number;
                return (
                  <div key={dim.label} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span>{dim.label}</span>
                      <span className="tabular-nums text-muted-foreground">
                        {value} / {dim.cap}
                      </span>
                    </div>
                    <Bar value={value} cap={dim.cap} />
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <div className="flex items-center gap-2 rounded-md border border-dashed p-3 text-xs text-muted-foreground">
            <Sparkles className="h-4 w-4 shrink-0" />
            The score above is computed by a deterministic engine with no LLM in the loop.
            The Gemini explanation below is layered on top and can never override this decision.
          </div>
        </>
      )}

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Bot className="h-4 w-4" /> Gemini Governance Explanation
            </CardTitle>
            {gov && (
              <Badge variant={gov.explanation.model_status === "LIVE" ? "low" : "secondary"}>
                {gov.explanation.model_status === "LIVE"
                  ? `Gemini: LIVE (${gov.explanation.model_name})`
                  : "Security scanner: LOCAL DEMO"}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {gov ? (
            <>
              <p className="text-sm text-muted-foreground">{gov.explanation.text}</p>
              <div className="text-xs text-muted-foreground">
                Provider: {gov.explanation.provider} · Deterministic action stands:{" "}
                <span className="font-medium text-foreground">{gov.policy.action}</span>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Ask the GovernanceAgent to explain the deterministic decision in natural language.
            </p>
          )}
          <Button size="sm" variant={gov ? "outline" : "default"} onClick={runGovernance} disabled={govBusy}>
            <Bot className={govBusy ? "h-4 w-4 animate-pulse" : "h-4 w-4"} />
            {gov ? "Re-run analysis" : "Explain with Gemini"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
