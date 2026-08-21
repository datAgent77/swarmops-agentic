"""Repository CRUD and query coverage against the SQLite implementation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import (
    AgentStatus,
    AutonomyLevel,
    DependencyTargetType,
    Relationship,
    RiskLevel,
    Role,
    ToolType,
)
from app.domain.models import Agent, AgentDependency, AgentVersion, Tool, User
from app.domain.repositories import AgentQuery
from app.infrastructure.container import RepositoryContainer

NOW = datetime(2026, 2, 1, tzinfo=UTC)


def _agent(aid: str, **overrides) -> Agent:
    base = dict(
        id=aid, organization_id="org-acmecorp", name=f"Agent {aid}", description="d",
        owner_id="user-dana-dev", department="Finance", status=AgentStatus.ACTIVE,
        autonomy_level=AutonomyLevel.MEDIUM, risk_score=10, current_version="v1",
        runtime="Cloud Run", framework="Google ADK", model_provider="Google",
        model_name="gemini-3.5-flash", created_at=NOW, updated_at=NOW,
    )
    base.update(overrides)
    return Agent(**base)


def test_agent_crud_roundtrip(container: RepositoryContainer) -> None:
    container.agents.add(_agent("agent-test-1", name="Zephyr", risk_score=91))
    fetched = container.agents.get("agent-test-1")
    assert fetched is not None
    assert fetched.name == "Zephyr"
    assert fetched.severity is RiskLevel.CRITICAL  # computed from risk_score 91

    # Update via upsert.
    container.agents.update(_agent("agent-test-1", name="Zephyr", risk_score=10))
    assert container.agents.get("agent-test-1").risk_score == 10
    assert container.agents.get("missing") is None


def test_agent_filters(container: RepositoryContainer) -> None:
    quarantined = container.agents.list(AgentQuery(status="QUARANTINED"))
    assert len(quarantined) == 3
    assert all(a.status is AgentStatus.QUARANTINED for a in quarantined)

    high = container.agents.list(AgentQuery(risk=RiskLevel.HIGH))
    assert len(high) == 9
    assert all(a.risk_score >= 50 for a in high)

    refund = container.agents.list(AgentQuery(search="refund"))
    assert any(a.id == "agent-customer-refund" for a in refund)

    finance = container.agents.list(AgentQuery(department="Finance"))
    assert finance and all(a.department == "Finance" for a in finance)

    limited = container.agents.list(AgentQuery(limit=5))
    assert len(limited) == 5


def test_user_repository(container: RepositoryContainer) -> None:
    users = container.users.list()
    assert len(users) == 5
    roles = {u.role for u in users}
    assert Role.PLATFORM_ADMIN in roles and Role.FINANCE_APPROVER in roles

    container.users.add(User(id="user-x", organization_id="org-acmecorp", name="X",
                             email="x@acme.example", role=Role.DEVELOPER, created_at=NOW))
    assert container.users.get("user-x") is not None


def test_version_and_dependency_repositories(container: RepositoryContainer) -> None:
    versions = container.agent_versions.list_for_agent("agent-customer-refund")
    assert len(versions) == 1
    assert versions[0].configuration["approval_gate"] is False
    assert "tool-stripe" in versions[0].tools

    deps = container.dependencies.list_for_agent("agent-customer-refund")
    assert len(deps) == 5
    assert any(d.target_id == "tool-stripe" and d.relationship is Relationship.EXECUTE for d in deps)

    container.agent_versions.add(AgentVersion(
        id="ver-x", agent_id="agent-x", version="v1", system_prompt_hash="h",
        system_prompt_summary="s", tools=["t"], permissions=["p"], data_sources=["d"],
        model="gemini-3.5-flash", configuration={"k": 1}, created_by="user-dana-dev", created_at=NOW,
    ))
    assert container.agent_versions.get("ver-x").configuration == {"k": 1}


def test_tool_repository(container: RepositoryContainer) -> None:
    tools = container.tools.list()
    assert len(tools) == 6
    stripe = container.tools.get("tool-stripe")
    assert stripe is not None
    assert stripe.type is ToolType.SAAS
    assert stripe.risk_level is RiskLevel.CRITICAL

    container.tools.add(Tool(id="tool-x", name="X", type=ToolType.API, risk_level=RiskLevel.LOW,
                             description="d", endpoint=None, permissions=[], metadata={"a": 1}))
    assert container.tools.get("tool-x").metadata == {"a": 1}


def test_dependency_add(container: RepositoryContainer) -> None:
    container.dependencies.add(AgentDependency(
        id="dep-x", source_agent_id="agent-y", target_type=DependencyTargetType.MODEL,
        target_id="gemini", relationship=Relationship.CALL, risk_level=RiskLevel.LOW,
    ))
    deps = container.dependencies.list_for_agent("agent-y")
    assert len(deps) == 1 and deps[0].target_type is DependencyTargetType.MODEL


def test_reset_is_deterministic(container: RepositoryContainer) -> None:
    before = [a.id for a in container.agents.list()]
    container.reset()
    after = [a.id for a in container.agents.list()]
    assert before == after
    assert container.agents.count_total() == 127
