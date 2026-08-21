"""Deterministic version diff + self-evolving governance rule."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import ProposalDecision
from app.domain.models import AgentVersion
from app.domain.version_intelligence import compute_diff, evaluate_change

NOW = datetime(2026, 2, 1, tzinfo=UTC)


def _version(**cfg) -> AgentVersion:
    return AgentVersion(
        id="v", agent_id="a", version=cfg.get("version", "v1"),
        system_prompt_hash=cfg.get("hash", "h"), system_prompt_summary="s",
        tools=cfg.get("tools", []), permissions=cfg.get("permissions", []),
        data_sources=cfg.get("data_sources", []), model=cfg.get("model", "gemini-3.5-flash"),
        configuration=cfg.get("configuration", {}), created_by="u", created_at=NOW,
    )


def test_diff_detects_changes() -> None:
    base = _version(hash="h1", permissions=["a"], model="gemini-3.5-flash",
                    configuration={"autonomy": "MEDIUM"}, data_sources=["crm"])
    candidate = _version(hash="h2", permissions=["a", "b"], model="gemini-3.5-pro",
                         configuration={"autonomy": "HIGH"}, data_sources=["crm", "ext"])
    changes = set(compute_diff(base, candidate))
    assert changes == {"prompt", "permissions", "model", "autonomy", "data_access"}


def test_compliance_regression_rejected() -> None:
    decision, reason = evaluate_change(71, 82, 94, 70, allowed_regression=5)
    assert decision is ProposalDecision.REJECTED
    assert reason == "Performance improvement does not justify compliance regression."


def test_small_regression_accepted() -> None:
    decision, _ = evaluate_change(71, 82, 94, 90, allowed_regression=5)  # drop 4 <= 5
    assert decision is ProposalDecision.ACCEPTED


def test_performance_regression_rejected() -> None:
    decision, _ = evaluate_change(82, 71, 90, 90, allowed_regression=5)
    assert decision is ProposalDecision.REJECTED


def test_threshold_controls_decision() -> None:
    # The same candidate is accepted once the allowed regression covers the drop.
    assert evaluate_change(71, 82, 94, 70, allowed_regression=30)[0] is ProposalDecision.ACCEPTED
