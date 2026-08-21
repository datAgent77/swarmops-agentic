"""Audit trail emission + observability overview + trace reconstruction."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _small_refund(client: TestClient) -> dict:
    return client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-refund",
        "input_summary": "Refund $50",
        "tool_calls": [{"tool": "execute_refund", "arguments": {"amount": 50}}],
    }).json()["execution"]


def _governed_refund(client: TestClient) -> dict:
    return client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-refund",
        "input_summary": "Refund $650",
        "tool_calls": [{"tool": "execute_refund", "arguments": {"amount": 650}}],
    }).json()["execution"]


def test_execution_emits_audit_events(client: TestClient) -> None:
    _small_refund(client)
    actions = [e["action"] for e in client.get("/api/v1/audit").json()["items"]]
    for expected in ("execution.started", "policy.evaluated", "tool_call.completed", "execution.completed"):
        assert expected in actions


def test_audit_events_are_trace_correlated(client: TestClient) -> None:
    execution = _small_refund(client)
    trace_id = execution["trace_id"]
    audit = client.get("/api/v1/audit").json()["items"]
    trace_events = [e for e in audit if e["trace_id"] == trace_id]
    assert {"execution.started", "execution.completed"} <= {e["action"] for e in trace_events}


def test_full_governed_flow_audit(client: TestClient) -> None:
    execution = _governed_refund(client)
    approvals = client.get("/api/v1/approvals").json()["items"]
    for a in [x for x in approvals if x["execution_id"] == execution["id"]]:
        # Approve with the matching role persona.
        role = a["requested_from_role"]
        persona = {"BUSINESS_APPROVER": "user-blair-business",
                   "FINANCE_APPROVER": "user-morgan-finance"}[role]
        client.post(f"/api/v1/approvals/{a['id']}/approve", json={"actor_user_id": persona})

    actions = [e["action"] for e in client.get("/api/v1/audit").json()["items"]]
    for expected in ("execution.waiting_approval", "approval.requested", "approval.granted",
                     "execution.resumed", "execution.completed"):
        assert expected in actions


def test_observability_overview_shape(client: TestClient) -> None:
    _small_refund(client)
    ov = client.get("/api/v1/observability/overview").json()
    assert ov["total_executions"] >= 1
    assert ov["completed"] >= 1
    assert 0.0 <= ov["error_rate"] <= 1.0
    assert ov["estimated_spend"] > 0
    assert ov["token_usage"] is None  # honestly unavailable
    assert ov["telemetry_backend"] == "local"


def test_trace_reconstruction(client: TestClient) -> None:
    execution = _small_refund(client)
    trace = client.get(f"/api/v1/observability/traces/{execution['trace_id']}").json()
    assert trace["execution_id"] == execution["id"]
    names = [s["name"] for s in trace["steps"]]
    assert names[0] == "execution"  # root
    assert "tool_call.completed" in names
    assert "execution.completed" in names
