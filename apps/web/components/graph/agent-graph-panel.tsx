"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { GraphView } from "@/components/graph/graph-view";
import {
  fetchAgentGraph,
  fetchBlastRadius,
  type BlastRadius,
  type GraphResponse,
} from "@/lib/api";

const FLAGS: { key: keyof BlastRadius; label: string }[] = [
  { key: "pii_reachable", label: "PII reachable" },
  { key: "financial_action_reachable", label: "Financial action reachable" },
  { key: "production_write_path", label: "Production-write path" },
  { key: "external_exfiltration_path", label: "External exfiltration path" },
];

export function AgentGraphPanel({ agentId }: { agentId: string }) {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [blast, setBlast] = useState<BlastRadius | null>(null);

  useEffect(() => {
    fetchAgentGraph(agentId).then(setGraph).catch(() => setGraph({ nodes: [], edges: [] }));
    fetchBlastRadius(agentId).then(setBlast).catch(() => setBlast(null));
  }, [agentId]);

  return (
    <div className="space-y-4">
      {blast && (
        <div className="rounded-md border p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium">
            <AlertTriangle className="h-4 w-4 text-severity-high" /> Blast radius
            <span className="text-xs font-normal text-muted-foreground">
              ({blast.reachable_nodes} reachable dependencies)
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {FLAGS.map((f) => (
              <Badge key={f.key} variant={blast[f.key] ? "critical" : "secondary"}>
                {blast[f.key] ? "⚠ " : "✓ "}
                {f.label}
              </Badge>
            ))}
            {blast.privileged_downstream_agents.length > 0 && (
              <Badge variant="high">
                {blast.privileged_downstream_agents.length} downstream agent(s)
              </Badge>
            )}
          </div>
        </div>
      )}
      {graph && <GraphView graph={graph} />}
    </div>
  );
}
