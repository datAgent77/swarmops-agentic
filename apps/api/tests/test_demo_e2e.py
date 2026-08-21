"""End-to-end demo flow — the complete governed arc in one test.

reset → discover rogue → risk → quarantine → governed activation → $650 execution
→ manager approval → finance approval → refund completes exactly once → audit trace.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

REFUND = "agent-customer-refund"
ADMIN = "user-alex-admin"
MANAGER = "user-blair-business"      # BUSINESS_APPROVER
FINANCE = "user-morgan-finance"     # FINANCE_APPROVER


def test_full_demo_flow(client: TestClient) -> None:
    # 0. Deterministic reset.
    assert client.post("/api/v1/demo/reset").json()["total_agents"] == 127

    # 1. Discover the rogue agent → risk 87 → quarantined.
    discovered = client.post("/api/v1/agents/discover").json()["discovered"][0]
    assert discovered["risk_score"] == 87
    assert discovered["quarantined"] is True

    # 2-3. It is quarantined and cannot execute.
    agent = client.get(f"/api/v1/agents/{REFUND}").json()["agent"]
    assert agent["status"] == "QUARANTINED"
    blocked = client.post("/api/v1/executions", json={
        "agent_id": REFUND, "input_summary": "blocked", "tool_calls": []})
    assert blocked.status_code == 409

    # 4. Governed reactivation by a privileged operator.
    activated = client.post(f"/api/v1/agents/{REFUND}/activate", json={"actor_user_id": ADMIN})
    assert activated.status_code == 200 and activated.json()["status"] == "ACTIVE"

    # 5. Trigger a $650 refund → waits for approval.
    execution = client.post("/api/v1/executions", json={
        "agent_id": REFUND, "input_summary": "Refund order #4471 for $650",
        "tool_calls": [{"tool": "execute_refund",
                        "arguments": {"amount": 650}, "idempotency_key": "order-4471"}],
    }).json()["execution"]
    assert execution["status"] == "WAITING_APPROVAL"
    exec_id, trace_id = execution["id"], execution["trace_id"]

    approvals = [a for a in client.get("/api/v1/approvals").json()["items"]
                 if a["execution_id"] == exec_id]
    assert {a["requested_from_role"] for a in approvals} == {"BUSINESS_APPROVER", "FINANCE_APPROVER"}
    manager_appr = next(a for a in approvals if a["requested_from_role"] == "BUSINESS_APPROVER")
    finance_appr = next(a for a in approvals if a["requested_from_role"] == "FINANCE_APPROVER")

    # 6. Manager approves — still waiting (finance outstanding).
    client.post(f"/api/v1/approvals/{manager_appr['id']}/approve", json={"actor_user_id": MANAGER})
    assert client.get(f"/api/v1/executions/{exec_id}").json()["execution"]["status"] == "WAITING_APPROVAL"

    # 7. Finance approves — execution resumes and completes.
    client.post(f"/api/v1/approvals/{finance_appr['id']}/approve", json={"actor_user_id": FINANCE})
    detail = client.get(f"/api/v1/executions/{exec_id}").json()
    assert detail["execution"]["status"] == "COMPLETED"

    # Refund executed exactly once.
    refund_calls = [t for t in detail["tool_calls"] if t["tool_id"] == "execute_refund"]
    assert len(refund_calls) == 1
    assert "demo_refund_order-4471" in refund_calls[0]["result_summary"]
    assert "idempotent-replay" not in refund_calls[0]["result_summary"]

    # 8. The audit trace shows the full reasoning chain.
    trace = client.get(f"/api/v1/observability/traces/{trace_id}").json()
    names = [s["name"] for s in trace["steps"]]
    for expected in ("execution.started", "policy.evaluated", "execution.waiting_approval",
                     "approval.requested", "approval.granted", "execution.resumed",
                     "tool_call.completed", "execution.completed"):
        assert expected in names

    # Wrong-role approval is rejected (belt and suspenders).
    other = client.post("/api/v1/executions", json={
        "agent_id": REFUND, "input_summary": "Refund $650 again",
        "tool_calls": [{"tool": "execute_refund", "arguments": {"amount": 650}}]}).json()["execution"]
    appr = client.get("/api/v1/approvals").json()["items"]
    pending = next(a for a in appr if a["execution_id"] == other["id"])
    wrong = client.post(f"/api/v1/approvals/{pending['id']}/approve", json={"actor_user_id": FINANCE})
    # Finance cannot approve a BUSINESS_APPROVER step.
    if pending["requested_from_role"] == "BUSINESS_APPROVER":
        assert wrong.status_code == 403
