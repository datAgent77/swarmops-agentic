"""Dependency graph + deterministic blast-radius analysis.

Builds node/edge views for an agent or the whole fleet, and computes blast-radius
indicators (what an agent can reach). All indicators are deterministic; nothing here
calls an LLM. Every edge/node is dependency **metadata** — no live integration is
implied (the demo tools are mocks).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import DependencyTargetType, Relationship, RiskLevel
from app.domain.models import AgentDependency
from app.infrastructure.container import RepositoryContainer

_TARGET_GROUP = {
    DependencyTargetType.TOOL: "tool",
    DependencyTargetType.DATABASE: "database",
    DependencyTargetType.EXTERNAL_API: "external_api",
    DependencyTargetType.MODEL: "model",
    DependencyTargetType.MCP: "mcp",
    DependencyTargetType.AGENT: "agent",
}
_DANGEROUS_LEVELS = {RiskLevel.HIGH, RiskLevel.CRITICAL}


@dataclass
class GraphNode:
    id: str
    type: str
    label: str
    risk_level: str | None = None
    connection: str = "metadata"  # never "live" — the demo integrations are mocks
    meta: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    relationship: str
    risk_level: str
    dangerous: bool


@dataclass
class GraphData:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass
class BlastRadius:
    agent_id: str
    pii_reachable: bool
    financial_action_reachable: bool
    production_write_path: bool
    external_exfiltration_path: bool
    privileged_downstream_agents: list[str]
    reachable_nodes: int
    indicators: list[str]


def _target_label(container: RepositoryContainer, dep: AgentDependency) -> tuple[str, str | None, dict]:
    if dep.target_id.startswith("tool-"):
        tool = container.tools.get(dep.target_id)
        if tool is not None:
            return tool.name, tool.risk_level.value, dict(tool.metadata)
    if dep.target_type is DependencyTargetType.AGENT:
        agent = container.agents.get(dep.target_id)
        if agent is not None:
            return agent.name, agent.severity.value, {}
    return dep.target_id, dep.risk_level.value, {}


def _target_node(container: RepositoryContainer, dep: AgentDependency) -> GraphNode:
    label, risk, meta = _target_label(container, dep)
    return GraphNode(
        id=dep.target_id, type=_TARGET_GROUP[dep.target_type], label=label,
        risk_level=risk, connection="metadata", meta=meta,
    )


def _edge(dep: AgentDependency) -> GraphEdge:
    return GraphEdge(
        id=dep.id, source=dep.source_agent_id, target=dep.target_id,
        relationship=dep.relationship.value, risk_level=dep.risk_level.value,
        dangerous=dep.risk_level in _DANGEROUS_LEVELS,
    )


def build_agent_graph(container: RepositoryContainer, agent_id: str) -> GraphData:
    agent = container.agents.get(agent_id)
    if agent is None:
        return GraphData(nodes=[], edges=[])

    nodes: dict[str, GraphNode] = {
        agent.id: GraphNode(id=agent.id, type="agent", label=agent.name,
                            risk_level=agent.severity.value, meta={"status": agent.status.value})
    }
    edges: list[GraphEdge] = []
    for dep in container.dependencies.list_for_agent(agent_id):
        nodes.setdefault(dep.target_id, _target_node(container, dep))
        edges.append(_edge(dep))

    # The agent's model as a derived node/edge (never a live integration).
    model_id = f"model-{agent.model_name}"
    nodes.setdefault(model_id, GraphNode(id=model_id, type="model", label=agent.model_name,
                                         risk_level="LOW", meta={"provider": agent.model_provider}))
    edges.append(GraphEdge(id=f"{agent.id}-model", source=agent.id, target=model_id,
                           relationship=Relationship.CALL.value, risk_level="LOW", dangerous=False))
    return GraphData(nodes=list(nodes.values()), edges=edges)


def build_fleet_graph(container: RepositoryContainer) -> GraphData:
    deps = list(container.dependencies.list_all())
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    for dep in deps:
        if dep.source_agent_id not in nodes:
            agent = container.agents.get(dep.source_agent_id)
            if agent is not None:
                nodes[agent.id] = GraphNode(id=agent.id, type="agent", label=agent.name,
                                            risk_level=agent.severity.value,
                                            meta={"status": agent.status.value})
        nodes.setdefault(dep.target_id, _target_node(container, dep))
        edges.append(_edge(dep))
    return GraphData(nodes=list(nodes.values()), edges=edges)


def compute_blast_radius(container: RepositoryContainer, agent_id: str) -> BlastRadius | None:
    agent = container.agents.get(agent_id)
    if agent is None:
        return None
    deps = list(container.dependencies.list_for_agent(agent_id))
    version = next(
        (v for v in container.agent_versions.list_for_agent(agent_id) if v.version == agent.current_version),
        None,
    )
    permissions = {p.lower() for p in version.permissions} if version else set()

    pii = False
    financial = False
    prod_write = "production:write" in permissions
    has_external = False
    downstream_agents: list[str] = []

    for dep in deps:
        _, _, meta = _target_label(container, dep)
        if meta.get("pii"):
            pii = True
        if meta.get("financial"):
            financial = True
        if meta.get("production_write") or dep.relationship is Relationship.WRITE:
            prod_write = True
        if dep.target_type is DependencyTargetType.EXTERNAL_API:
            has_external = True
        if dep.target_type is DependencyTargetType.AGENT:
            downstream_agents.append(dep.target_id)

    exfiltration = pii and has_external

    indicators: list[str] = []
    if pii:
        indicators.append("PII reachable")
    if financial:
        indicators.append("Financial action reachable")
    if prod_write:
        indicators.append("Production-write path")
    if exfiltration:
        indicators.append("External exfiltration path")
    if downstream_agents:
        indicators.append(f"{len(downstream_agents)} privileged downstream agent(s)")

    return BlastRadius(
        agent_id=agent_id, pii_reachable=pii, financial_action_reachable=financial,
        production_write_path=prod_write, external_exfiltration_path=exfiltration,
        privileged_downstream_agents=downstream_agents, reachable_nodes=len(deps),
        indicators=indicators,
    )
