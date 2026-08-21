"""Deterministic risk engine: scoring, boundaries, and key scenarios."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import AutonomyLevel, RecommendedAction, RiskLevel
from app.domain.models import Agent, AgentVersion
from app.domain.risk_engine import RiskInput, assess
from app.domain.severity import severity_from_score
from app.infrastructure.container import RepositoryContainer

NOW = datetime(2026, 2, 1, tzinfo=UTC)


def _agent(autonomy: AutonomyLevel = AutonomyLevel.LOW) -> Agent:
    return Agent(
        id="a", organization_id="org", name="A", description="d", owner_id="u",
        department="Finance", status="ACTIVE", autonomy_level=autonomy, risk_score=0,
        current_version="v1", runtime="Cloud Run", framework="Google ADK",
        model_provider="Google", model_name="gemini-3.5-flash", created_at=NOW, updated_at=NOW,
    )


def _version(**cfg) -> AgentVersion:
    return AgentVersion(
        id="v", agent_id="a", version="v1", system_prompt_hash="h", system_prompt_summary="s",
        tools=cfg.get("tools", []), permissions=cfg.get("permissions", []),
        data_sources=cfg.get("data_sources", []), model="gemini-3.5-flash",
        configuration=cfg.get("configuration", {}), created_by="u", created_at=NOW,
    )


def test_severity_boundaries() -> None:
    assert severity_from_score(24) is RiskLevel.LOW
    assert severity_from_score(25) is RiskLevel.MODERATE
    assert severity_from_score(49) is RiskLevel.MODERATE
    assert severity_from_score(50) is RiskLevel.HIGH
    assert severity_from_score(74) is RiskLevel.HIGH
    assert severity_from_score(75) is RiskLevel.CRITICAL


def test_low_risk_agent_stays_low() -> None:
    result = assess(RiskInput(agent=_agent(AutonomyLevel.LOW), version=_version()))
    assert result.severity is RiskLevel.LOW
    assert result.total < 25
    assert result.recommended_action is RecommendedAction.ALLOW


def test_missing_approval_increases_risk() -> None:
    perms = ["production:write"]
    gated = assess(RiskInput(agent=_agent(), version=_version(
        permissions=perms, configuration={"approval_gate": True})))
    ungated = assess(RiskInput(agent=_agent(), version=_version(
        permissions=perms, configuration={"approval_gate": False})))
    assert ungated.total == gated.total + 10
    assert ungated.approval_gap == 10 and gated.approval_gap == 0


def test_refund_agent_scores_87(container: RepositoryContainer) -> None:
    agent = container.agents.get("agent-customer-refund")
    version = container.agent_versions.list_for_agent("agent-customer-refund")[0]
    deps = list(container.dependencies.list_for_agent("agent-customer-refund"))

    result = assess(RiskInput(agent=agent, version=version, dependencies=deps))

    assert result.total == 87
    assert result.severity is RiskLevel.CRITICAL
    assert result.recommended_action is RecommendedAction.QUARANTINE
    # Explainable breakdown that sums to the total.
    assert (result.pii, result.financial, result.production_write) == (16, 20, 15)
    assert (result.external_tools, result.autonomy, result.approval_gap, result.prompt_security) == (8, 15, 10, 3)
    assert "Can execute financial transactions" in result.drivers
    assert "No human approval configured" in result.drivers
