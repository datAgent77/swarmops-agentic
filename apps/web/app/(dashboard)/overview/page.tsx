import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SystemStatus } from "@/components/overview/system-status";

// Fleet metrics are seed-derived from P01 onward. In P00 they render as clearly
// marked placeholders so the shell is legible without faking business data.
const METRIC_PLACEHOLDERS = [
  { label: "Agents", value: "—", hint: "Fleet total" },
  { label: "Active", value: "—", hint: "Currently running" },
  { label: "High Risk", value: "—", hint: "Severity HIGH+" },
  { label: "Quarantined", value: "—", hint: "Governance holds" },
];

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Fleet-wide posture across discovery, governance, execution, and observability.
        </p>
        <Badge variant="outline">Metrics populate in P01</Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRIC_PLACEHOLDERS.map((m) => (
          <Card key={m.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-3xl tabular-nums">{m.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">{m.label}</div>
              <div className="text-xs text-muted-foreground">{m.hint}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <SystemStatus />
    </div>
  );
}
