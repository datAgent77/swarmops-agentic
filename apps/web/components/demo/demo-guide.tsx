"use client";

import { useState } from "react";
import { CheckCircle2, Circle, Loader2, Play, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  activateAgent,
  approveRequest,
  createExecution,
  discoverAgents,
  fetchAgent,
  fetchApprovals,
  fetchExecution,
  fetchTrace,
  resetDemo,
  runGovernanceAnalysis,
} from "@/lib/api";

const REFUND = "agent-customer-refund";
const ADMIN = "user-alex-admin";
const MANAGER = "user-blair-business"; // BUSINESS_APPROVER
const FINANCE = "user-morgan-finance"; // FINANCE_APPROVER

type Ctx = { executionId?: string; traceId?: string };

type Step = {
  label: string;
  run: (ctx: Ctx) => Promise<string>;
};

const STEPS: Step[] = [
  {
    label: "Discover Rogue Agent",
    run: async () => {
      const d = (await discoverAgents()).discovered[0];
      return `Discovered ${d.name} → ${d.to_status} at risk ${d.risk_score}/100.`;
    },
  },
  {
    label: "Run Risk Assessment",
    run: async () => {
      const g = await runGovernanceAnalysis(REFUND);
      return `Deterministic ${g.risk.overall_score}/100 ${g.risk.severity} → ${g.policy.action}. ` +
        `Gemini (${g.explanation.model_status === "LIVE" ? "live" : "local template"}) explains, never decides.`;
    },
  },
  {
    label: "Review Quarantine",
    run: async () => {
      const a = (await fetchAgent(REFUND)).agent;
      return `Status ${a.status} — ${a.quarantine_reason ?? "held under governance"}.`;
    },
  },
  {
    label: "Apply Refund Governance (reactivate)",
    run: async () => {
      const a = await activateAgent(REFUND, ADMIN);
      return `Reactivated by platform admin under governance → ${a.status}.`;
    },
  },
  {
    label: "Trigger $650 Refund",
    run: async (ctx) => {
      const d = await createExecution(REFUND, "Refund order #4471 for $650", [
        { tool: "execute_refund", arguments: { amount: 650 }, idempotency_key: "order-4471" },
      ]);
      ctx.executionId = d.execution.id;
      ctx.traceId = d.execution.trace_id;
      return `Execution ${d.execution.id} → ${d.execution.status} (policy requires two approvers).`;
    },
  },
  {
    label: "Manager Approves",
    run: async (ctx) => {
      const appr = (await fetchApprovals()).items.filter(
        (a) => a.execution_id === ctx.executionId && a.requested_from_role === "BUSINESS_APPROVER",
      );
      await approveRequest(appr[0].id, MANAGER);
      const status = (await fetchExecution(ctx.executionId!)).execution.status;
      return `Manager approved. Execution still ${status} — Finance approval outstanding.`;
    },
  },
  {
    label: "Finance Approves",
    run: async (ctx) => {
      const appr = (await fetchApprovals()).items.filter(
        (a) => a.execution_id === ctx.executionId && a.requested_from_role === "FINANCE_APPROVER",
      );
      await approveRequest(appr[0].id, FINANCE);
      const d = await fetchExecution(ctx.executionId!);
      const refund = d.tool_calls.find((t) => t.tool_id === "execute_refund");
      return `Finance approved → ${d.execution.status}. Refund executed exactly once: ` +
        `${refund ? JSON.parse(refund.result_summary).transaction_id : "—"}.`;
    },
  },
  {
    label: "View Audit Trace",
    run: async (ctx) => {
      const t = await fetchTrace(ctx.traceId!);
      return t.steps.map((s) => s.name).join("  →  ");
    },
  },
];

export function DemoGuide() {
  const [ctx] = useState<Ctx>({});
  const [current, setCurrent] = useState(0);
  const [results, setResults] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runStep = async (i: number) => {
    setBusy(i);
    setError(null);
    try {
      const msg = await STEPS[i].run(ctx);
      setResults((r) => ({ ...r, [i]: msg }));
      setCurrent(Math.max(current, i + 1));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Step failed");
    } finally {
      setBusy(null);
    }
  };

  const reset = async () => {
    setBusy(-1);
    try {
      await resetDemo();
      setResults({});
      setCurrent(0);
      ctx.executionId = undefined;
      ctx.traceId = undefined;
      setError(null);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Each button calls real backend logic — no fake animation. Run the steps in order.
        </p>
        <Button size="sm" variant="outline" onClick={reset} disabled={busy !== null}>
          <RotateCcw className={busy === -1 ? "h-4 w-4 animate-spin" : "h-4 w-4"} /> RESET DEMO
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-severity-critical/40 bg-severity-critical/5 p-3 text-sm text-severity-critical">
          {error}
        </div>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Guided demo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {STEPS.map((step, i) => {
            const done = i in results;
            const active = i === current;
            return (
              <div
                key={i}
                className={`flex flex-col gap-2 rounded-md border p-3 sm:flex-row sm:items-center ${
                  active ? "border-primary/50" : ""
                }`}
              >
                <div className="flex flex-1 items-center gap-3">
                  {done ? (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-severity-low" />
                  ) : (
                    <Circle className={`h-5 w-5 shrink-0 ${active ? "text-primary" : "text-muted-foreground"}`} />
                  )}
                  <div>
                    <div className="text-sm font-medium">
                      {i + 1}. {step.label}
                    </div>
                    {results[i] && (
                      <div className="mt-0.5 font-mono text-xs text-muted-foreground">{results[i]}</div>
                    )}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant={done ? "outline" : active ? "default" : "ghost"}
                  onClick={() => runStep(i)}
                  disabled={busy !== null || (!active && !done)}
                >
                  {busy === i ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  {done ? "Re-run" : "Run"}
                </Button>
              </div>
            );
          })}
          {current >= STEPS.length && (
            <div className="pt-2">
              <Badge variant="low">Demo complete — refund executed exactly once, fully audited.</Badge>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
