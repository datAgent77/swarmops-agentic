"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Check, ShieldQuestion, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import {
  approveRequest,
  fetchApprovals,
  fetchUsers,
  rejectRequest,
  type ApprovalRequest,
  type Persona,
  API_URL,
} from "@/lib/api";

export function ApprovalQueue() {
  const [approvals, setApprovals] = useState<ApprovalRequest[] | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [actor, setActor] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(() => {
    fetchApprovals("PENDING")
      .then((d) => setApprovals(d.items))
      .catch(() => setError(`Could not reach the backend at ${API_URL}.`));
  }, []);

  useEffect(() => {
    load();
    fetchUsers().then((d) => {
      setPersonas(d.items);
      setActor(d.items[0]?.id ?? "");
    });
  }, [load]);

  const act = async (id: string, kind: "approve" | "reject") => {
    setBusy(id + kind);
    setError(null);
    try {
      const fn = kind === "approve" ? approveRequest : rejectRequest;
      await fn(id, actor);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(null);
    }
  };

  if (error && !approvals) return <p className="text-sm text-severity-critical">{error}</p>;
  if (!approvals) return <p className="text-sm text-muted-foreground">Loading approvals…</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Durable human-in-the-loop approvals. The backend validates that the acting persona
          truly holds the required role.
        </p>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Acting as</span>
          <div className="w-56">
            <Select value={actor} onChange={(e) => setActor(e.target.value)}>
              {personas.map((p) => (
                <option key={p.id} value={p.id}>{p.name} · {p.role}</option>
              ))}
            </Select>
          </div>
        </div>
      </div>

      {error && <p className="text-sm text-severity-critical">{error}</p>}

      {approvals.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            <ShieldQuestion className="mx-auto mb-2 h-6 w-6" />
            No pending approvals. Trigger a $500+ refund to see the governed flow.
          </CardContent>
        </Card>
      )}

      {approvals.map((a) => (
        <Card key={a.id}>
          <CardHeader className="pb-2">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">
                {typeof a.context.refund === "number" ? `$${a.context.refund} Refund` : "Approval required"}
              </CardTitle>
              <Badge variant="moderate">{a.requested_from_role}</Badge>
              <Badge variant="outline">step {a.sequence}</Badge>
              <Badge variant="secondary">{a.status}</Badge>
            </div>
            <p className="text-sm text-muted-foreground">{a.reason}</p>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span>
                Execution:{" "}
                <Link href={`/executions/${a.execution_id}`} className="font-mono hover:text-primary">
                  {a.execution_id}
                </Link>
              </span>
              {a.policy_id && <span>Policy: <span className="font-mono">{a.policy_id}</span></span>}
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={() => act(a.id, "approve")} disabled={busy !== null}>
                <Check className="h-4 w-4" /> Approve
              </Button>
              <Button size="sm" variant="destructive" onClick={() => act(a.id, "reject")} disabled={busy !== null}>
                <X className="h-4 w-4" /> Reject
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
