import { Badge } from "@/components/ui/badge";
import type { AgentStatus, Severity } from "@/lib/api";

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
