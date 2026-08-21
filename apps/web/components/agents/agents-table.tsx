"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Radar, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { SeverityBadge, StatusBadge } from "@/components/ui/status-badge";
import {
  discoverAgents,
  fetchAgents,
  type Agent,
  type AgentFilters,
  type Severity,
  API_URL,
} from "@/lib/api";

const STATUSES = [
  "DISCOVERED", "PENDING_REVIEW", "APPROVED", "ACTIVE",
  "SUSPENDED", "QUARANTINED", "RETIRED",
];
const RISKS: Severity[] = ["LOW", "MODERATE", "HIGH", "CRITICAL"];

type OwnerMap = Record<string, string>;

function useOwners(): OwnerMap {
  const [owners, setOwners] = useState<OwnerMap>({});
  useEffect(() => {
    fetch(`${API_URL}/api/v1/users`)
      .then((r) => (r.ok ? r.json() : { items: [] }))
      .then((data: { items: { id: string; name: string }[] }) => {
        const map: OwnerMap = {};
        for (const u of data.items) map[u.id] = u.name;
        setOwners(map);
      })
      .catch(() => setOwners({}));
  }, []);
  return owners;
}

export function AgentsTable() {
  const [filters, setFilters] = useState<AgentFilters>({});
  const [agents, setAgents] = useState<Agent[] | null>(null);
  const [total, setTotal] = useState(0);
  const [departments, setDepartments] = useState<string[]>([]);
  const [error, setError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [discovering, setDiscovering] = useState(false);
  const [discoverMsg, setDiscoverMsg] = useState<string | null>(null);
  const owners = useOwners();

  // One-time unfiltered load to populate the department dropdown.
  useEffect(() => {
    fetchAgents()
      .then((data) => {
        setDepartments([...new Set(data.items.map((a) => a.department))].sort());
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    let active = true;
    fetchAgents(filters)
      .then((data) => {
        if (!active) return;
        setAgents(data.items);
        setTotal(data.total);
        setError(false);
      })
      .catch(() => active && setError(true));
    return () => {
      active = false;
    };
  }, [filters, reloadToken]);

  const update = (patch: AgentFilters) => setFilters((f) => ({ ...f, ...patch }));

  const onDiscover = async () => {
    setDiscovering(true);
    setDiscoverMsg(null);
    try {
      const { discovered } = await discoverAgents();
      const q = discovered.filter((d) => d.quarantined);
      setDiscoverMsg(
        q.length
          ? `Discovered ${discovered.length} agent(s); quarantined ${q[0].name} at risk ${q[0].risk_score}/100.`
          : `Discovered ${discovered.length} agent(s); none required quarantine.`,
      );
      setReloadToken((t) => t + 1);
    } catch {
      setDiscoverMsg("Discovery failed — is the backend running?");
    } finally {
      setDiscovering(false);
    }
  };

  const rows = useMemo(() => agents ?? [], [agents]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search agents…"
            className="pl-8"
            value={filters.search ?? ""}
            onChange={(e) => update({ search: e.target.value || undefined })}
          />
        </div>
        <div className="w-40">
          <Select
            value={filters.status ?? ""}
            onChange={(e) => update({ status: e.target.value || undefined })}
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </Select>
        </div>
        <div className="w-48">
          <Select
            value={filters.department ?? ""}
            onChange={(e) => update({ department: e.target.value || undefined })}
          >
            <option value="">All departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </Select>
        </div>
        <div className="w-40">
          <Select
            value={filters.risk ?? ""}
            onChange={(e) => update({ risk: (e.target.value || undefined) as Severity | undefined })}
          >
            <option value="">Any risk</option>
            {RISKS.map((r) => (
              <option key={r} value={r}>{r}+</option>
            ))}
          </Select>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{total} agents</span>
          <Button size="sm" variant="outline" onClick={onDiscover} disabled={discovering}>
            <Radar className={discovering ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            Discover Agents
          </Button>
        </div>
      </div>

      {discoverMsg && (
        <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
          {discoverMsg}
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Department</th>
                <th className="px-4 py-3 font-medium">Owner</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Risk</th>
                <th className="px-4 py-3 font-medium">Model</th>
                <th className="px-4 py-3 font-medium">Runtime</th>
                <th className="px-4 py-3 font-medium">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rows.map((a) => (
                <tr key={a.id} className="hover:bg-accent/40">
                  <td className="px-4 py-3">
                    <Link href={`/agents/${a.id}`} className="font-medium text-foreground hover:text-primary">
                      {a.name}
                    </Link>
                    <div className="text-xs text-muted-foreground">
                      {a.framework} · {a.current_version}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{a.department}</td>
                  <td className="px-4 py-3 text-muted-foreground">{owners[a.owner_id] ?? a.owner_id}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="tabular-nums">{a.risk_score}</span>
                      <SeverityBadge severity={a.severity} />
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{a.model_name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{a.runtime}</td>
                  <td className="px-4 py-3 text-muted-foreground">{a.updated_at.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {error && (
          <div className="p-6 text-sm text-severity-critical">
            Could not reach the backend at {API_URL}. Start it with{" "}
            <code className="font-mono">make dev</code>.
          </div>
        )}
        {!error && agents === null && (
          <div className="p-6 text-sm text-muted-foreground">Loading agents…</div>
        )}
        {!error && agents?.length === 0 && (
          <div className="p-6 text-sm text-muted-foreground">No agents match these filters.</div>
        )}
      </Card>
    </div>
  );
}
