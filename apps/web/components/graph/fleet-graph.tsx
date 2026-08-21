"use client";

import { useEffect, useState } from "react";

import { GraphView } from "@/components/graph/graph-view";
import { fetchFleetGraph, type GraphResponse, API_URL } from "@/lib/api";

export function FleetGraph() {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchFleetGraph().then(setGraph).catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <p className="text-sm text-severity-critical">
        Could not reach the backend at {API_URL}. Start it with <code>make dev</code>.
      </p>
    );
  }
  if (!graph) return <p className="text-sm text-muted-foreground">Loading graph…</p>;

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Agents and the tools, databases, external APIs, and models they depend on. Edges are
        dependency metadata (no live integration); HIGH/CRITICAL paths are highlighted.
      </p>
      <GraphView graph={graph} height={560} />
    </div>
  );
}
