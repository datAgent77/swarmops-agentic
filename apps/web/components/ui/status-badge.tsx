import { Badge } from "@/components/ui/badge";
import type { AgentStatus, ExecutionStatus, Severity } from "@/lib/api";

const STATUS_VARIANT: Record<AgentStatus, React.ComponentProps<typeof Badge>["variant"]> = {
  ACTIVE: "low",
  APPROVED: "default",
  DISCOVERED: "secondary",
  PENDING_REVIEW: "moderate",
  SUSPENDED: "high",
  QUARANTINED: "critical",
  RETIRED: "outline",
};

export function StatusBadge({ status }: { status: AgentStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{status.replace("_", " ")}</Badge>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <Badge variant={severity.toLowerCase() as "low" | "moderate" | "high" | "critical"}>
      {severity}
    </Badge>
  );
}

const EXEC_VARIANT: Record<ExecutionStatus, React.ComponentProps<typeof Badge>["variant"]> = {
  QUEUED: "secondary",
  RUNNING: "default",
  WAITING_APPROVAL: "moderate",
  BLOCKED: "critical",
  FAILED: "critical",
  COMPLETED: "low",
  CANCELLED: "outline",
};

export function ExecStatusBadge({ status }: { status: ExecutionStatus }) {
  return <Badge variant={EXEC_VARIANT[status]}>{status.replace("_", " ")}</Badge>;
}
