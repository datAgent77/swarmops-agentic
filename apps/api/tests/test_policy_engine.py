"""Deterministic policy engine: operators, validation, ordering, no code exec."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.enums import PolicyAction
from app.domain.models import Policy
from app.domain.policy_engine import (
    PolicyConditionError,
    evaluate_condition,
    evaluate_policies,
    validate_condition,
)

NOW = datetime(2026, 2, 1, tzinfo=UTC)


def _policy(pid: str, priority: int, condition: dict, action: PolicyAction, **params) -> Policy:
    return Policy(
        id=pid, name=pid, description=pid, scope="test", priority=priority,
        condition=condition, action=action, parameters=params, enabled=True,
        created_by="u", created_at=NOW, updated_at=NOW,
    )


def test_operators() -> None:
    ctx = {"n": 300, "list": ["a", "b"], "flag": True}
    assert evaluate_condition({"field": "n", "op": "gte", "value": 100}, ctx)
    assert evaluate_condition({"field": "n", "op": "lt", "value": 500}, ctx)
    assert not evaluate_condition({"field": "n", "op": "gt", "value": 500}, ctx)
    assert evaluate_condition({"field": "list", "op": "contains", "value": "a"}, ctx)
    assert evaluate_condition({"field": "flag", "op": "eq", "value": True}, ctx)
    assert evaluate_condition({"field": "flag", "op": "exists", "value": True}, ctx)
    assert not evaluate_condition({"field": "missing", "op": "exists", "value": True}, ctx)


def test_all_any_groups() -> None:
    ctx = {"refund": 300}
    cond = {"all": [
        {"field": "refund", "op": "gte", "value": 100},
        {"field": "refund", "op": "lte", "value": 500},
    ]}
    assert evaluate_condition(cond, ctx)
    assert not evaluate_condition({"any": [
        {"field": "refund", "op": "gt", "value": 500},
        {"field": "refund", "op": "lt", "value": 100},
    ]}, ctx)


def test_invalid_operator_rejected() -> None:
    with pytest.raises(PolicyConditionError):
        validate_condition({"field": "x", "op": "regex", "value": ".*"})
    with pytest.raises(PolicyConditionError):
        validate_condition({"all": "not-a-list"})


def test_no_arbitrary_code_execution() -> None:
    # A value that looks like code is compared as inert data, never executed.
    marker = {"ran": False}
    ctx = {"cmd": "__import__('os')"}
    cond = {"field": "cmd", "op": "eq", "value": "__import__('os')"}
    assert evaluate_condition(cond, ctx) is True  # plain string equality
    assert marker["ran"] is False
    # gt/lt against a non-numeric string never raises and never coerces.
    assert evaluate_condition({"field": "cmd", "op": "gt", "value": 0}, ctx) is False


def test_priority_ordering_first_match_wins() -> None:
    ctx = {"risk_score": 90}
    high = _policy("high", 10, {"field": "risk_score", "op": "gte", "value": 80}, PolicyAction.QUARANTINE)
    low = _policy("low", 50, {"field": "risk_score", "op": "gte", "value": 50}, PolicyAction.REQUIRE_APPROVAL)
    decision = evaluate_policies([low, high], ctx)  # unsorted input
    assert decision.policy_id == "high"
    assert decision.action is PolicyAction.QUARANTINE


def test_default_allow_when_no_match() -> None:
    decision = evaluate_policies([], {"anything": 1})
    assert decision.matched is False
    assert decision.action is PolicyAction.ALLOW


def test_disabled_policy_skipped() -> None:
    p = _policy("p", 10, {"field": "x", "op": "eq", "value": 1}, PolicyAction.DENY)
    disabled = p.model_copy(update={"enabled": False})
    assert evaluate_policies([disabled], {"x": 1}).matched is False
