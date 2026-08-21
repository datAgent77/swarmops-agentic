"""Execution API: run tools, idempotency, quarantine block, state lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _refund_execution(client: TestClient, key: str | None) -> dict:
    tc = {"tool": "execute_refund", "arguments": {"amount": 650}}
    if key is not None:
        tc["idempotency_key"] = key
    return client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-refund",
        "input_summary": "Refund order #123 for $650",
        "tool_calls": [tc],
    }).json()


def test_execution_runs_and_completes(client: TestClient) -> None:
    resp = client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-support",
        "input_summary": "Look up a customer",
        "tool_calls": [{"tool": "get_customer", "arguments": {"customer_id": "c9"}}],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["execution"]["status"] == "COMPLETED"
    assert body["execution"]["started_at"] and body["execution"]["completed_at"]
    assert len(body["tool_calls"]) == 1
    assert body["tool_calls"][0]["tool_id"] == "get_customer"


def test_refund_demo_tool_completes(client: TestClient) -> None:
    body = _refund_execution(client, key="order-123")
    assert body["execution"]["status"] == "COMPLETED"
    result = body["tool_calls"][0]["result_summary"]
    assert "demo_refund_order-123" in result


def test_idempotent_refund_not_issued_twice(client: TestClient) -> None:
    first = _refund_execution(client, key="order-999")
    second = _refund_execution(client, key="order-999")

    assert "idempotent-replay" not in first["tool_calls"][0]["result_summary"]
    # Second call with the same key is a replay — the tool did not execute again.
    assert "idempotent-replay" in second["tool_calls"][0]["result_summary"]
    # Same transaction id both times → no duplicate refund.
    assert "demo_refund_order-999" in first["tool_calls"][0]["result_summary"]
    assert "demo_refund_order-999" in second["tool_calls"][0]["result_summary"]


def test_quarantined_agent_cannot_start(client: TestClient) -> None:
    # The 3 seeded quarantined agents cannot start executions.
    quarantined = client.get("/api/v1/agents", params={"status": "QUARANTINED"}).json()["items"]
    agent_id = quarantined[0]["id"]
    resp = client.post("/api/v1/executions", json={
        "agent_id": agent_id, "input_summary": "should be blocked", "tool_calls": [],
    })
    assert resp.status_code == 409
    assert "quarantined" in resp.json()["detail"].lower()


def test_unknown_tool_rejected(client: TestClient) -> None:
    resp = client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-support", "input_summary": "x",
        "tool_calls": [{"tool": "rm_rf_prod", "arguments": {}}],
    })
    assert resp.status_code == 400


def test_list_and_get_execution(client: TestClient) -> None:
    created = _refund_execution(client, key="order-777")["execution"]["id"]
    listing = client.get("/api/v1/executions").json()
    assert listing["total"] >= 1
    detail = client.get(f"/api/v1/executions/{created}").json()
    assert detail["execution"]["id"] == created
    assert client.get("/api/v1/executions/nope").status_code == 404
