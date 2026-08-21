"""Execution state machine + safe tool layer unit tests."""

from __future__ import annotations

import pytest

from app.domain.enums import ExecutionStatus as S
from app.domain.execution_state import (
    InvalidStateTransition,
    assert_transition,
    can_transition,
)
from app.infrastructure.tool_layer import run_tool


def test_valid_transitions() -> None:
    assert assert_transition(S.QUEUED, S.RUNNING) is S.RUNNING
    assert assert_transition(S.RUNNING, S.WAITING_APPROVAL) is S.WAITING_APPROVAL
    assert assert_transition(S.WAITING_APPROVAL, S.RUNNING) is S.RUNNING
    assert assert_transition(S.RUNNING, S.COMPLETED) is S.COMPLETED
    assert assert_transition(S.RUNNING, S.BLOCKED) is S.BLOCKED
    assert assert_transition(S.RUNNING, S.FAILED) is S.FAILED


def test_invalid_transitions_rejected() -> None:
    assert not can_transition(S.COMPLETED, S.RUNNING)
    with pytest.raises(InvalidStateTransition):
        assert_transition(S.COMPLETED, S.RUNNING)
    with pytest.raises(InvalidStateTransition):
        assert_transition(S.QUEUED, S.COMPLETED)  # must go through RUNNING
    with pytest.raises(InvalidStateTransition):
        assert_transition(S.BLOCKED, S.RUNNING)  # terminal


def test_refund_demo_tool_never_touches_stripe() -> None:
    result = run_tool("execute_refund", {"amount": 650}, idempotency_key="k1")
    assert result == {"transaction_id": "demo_refund_k1", "status": "completed", "amount": 650}


def test_tool_layer_all_tools() -> None:
    assert run_tool("get_customer", {"customer_id": "c1"})["customer_id"] == "c1"
    assert run_tool("get_order", {"amount": 100})["amount"] == 100
    assert run_tool("calculate_refund", {"amount": 200})["amount"] == 200
    assert run_tool("send_email", {"to": "a@b.com"})["status"] == "sent"
    assert run_tool("get_salesforce_case", {})["status"] == "open"
