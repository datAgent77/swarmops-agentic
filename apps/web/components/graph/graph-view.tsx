"use client";

import { useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

import type { GraphResponse } from "@/lib/api";

// Node group → accent color (CSS vars from the theme).
const GROUP_COLOR: Record<string, string> = {
  agent: "hsl(var(--primary))",
  database: "hsl(var(--severity-critical))",
  external_api: "hsl(var(--severity-high))",
  tool: "hsl(var(--muted-foreground))",
  model: "hsl(var(--severity-low))",
  mcp: "hsl(var(--severity-moderate))",
};

const COLUMN_ORDER = ["database", "external_api", "tool", "mcp", "model", "agent"];

function layout(graph: GraphResponse): Node[] {
  const agents = graph.nodes.filter((n) => n.type === "agent");
  const others = graph.nodes.filter((n) => n.type !== "agent");
  const colCount: Record<string, number> = {};

  const agentNodes: Node[] = agents.map((n, i) => ({
    id: n.id,
    position: { x: 0, y: 40 + i * 120 },
    data: { label: `${n.label}${n.risk_level ? ` · ${n.risk_level}` : ""}` },
    style: nodeStyle(n.type),
  }));

  const otherNodes: Node[] = others.map((n) => {
    const col = Math.max(0, COLUMN_ORDER.indexOf(n.type));
    const row = colCount[n.type] ?? 0;
    colCount[n.type] = row + 1;
    return {
      id: n.id,
      position: { x: 300 + col * 210, y: 20 + row * 90 },
      data: { label: `${n.label}${n.risk_level ? ` · ${n.risk_level}` : ""}` },
      style: nodeStyle(n.type),
    };
  });

  return [...agentNodes, ...otherNodes];
}

function nodeStyle(type: string): React.CSSProperties {
  return {
    background: "hsl(var(--card))",
    color: "hsl(var(--card-foreground))",
    border: `2px solid ${GROUP_COLOR[type] ?? "hsl(var(--border))"}`,
    borderRadius: 8,
    fontSize: 12,
    padding: "6px 10px",
    width: 170,
  };
}

export function GraphView({ graph, height = 460 }: { graph: GraphResponse; height?: number }) {
  const [selected, setSelected] = useState<GraphResponse["nodes"][number] | null>(null);

  const nodes = useMemo(() => layout(graph), [graph]);
  const edges: Edge[] = useMemo(
    () =>
      graph.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relationship,
        animated: e.dangerous,
        style: {
          stroke: e.dangerous ? "hsl(var(--severity-critical))" : "hsl(var(--border))",
          strokeWidth: e.dangerous ? 2 : 1,
        },
        labelStyle: { fontSize: 10, fill: "hsl(var(--muted-foreground))" },
      })),
    [graph],
  );

  if (graph.nodes.length === 0) {
    return <p className="text-sm text-muted-foreground">No dependency graph for this scope.</p>;
  }

  return (
    <div className="space-y-3">
      <div
        style={{ height }}
        className="overflow-hidden rounded-lg border bg-background"
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          proOptions={{ hideAttribution: true }}
          onNodeClick={(_, node) =>
            setSelected(graph.nodes.find((n) => n.id === node.id) ?? null)
          }
        >
          <Background gap={16} />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable className="!bg-card" />
        </ReactFlow>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        {Object.entries(GROUP_COLOR).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: color }} />
            {type.replace("_", " ")}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4" style={{ background: "hsl(var(--severity-critical))" }} />
          dangerous path
        </span>
      </div>

      {selected && (
        <div className="rounded-md border p-3 text-sm">
          <div className="font-medium">{selected.label}</div>
          <div className="text-xs text-muted-foreground">
            type: {selected.type} · risk: {selected.risk_level ?? "—"} · connection:{" "}
            {selected.connection}
            {Object.keys(selected.meta).length > 0 && (
              <> · {Object.entries(selected.meta).map(([k, v]) => `${k}=${String(v)}`).join(", ")}</>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
