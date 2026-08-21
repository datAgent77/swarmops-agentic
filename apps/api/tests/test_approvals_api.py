"""Human approval workflow: the $650 governed refund end to end."""

from __future__ import annotations

from fastapi.testclient import TestClient

BUSINESS = "user-blair-business"   # BUSINESS_APPROVER
FINANCE = "user-morgan-finance"    # FINANCE_APPROVER
DEV = "user-dana-dev"              # DEVELOPER (wrong role)


def _start_650_refund(client: TestClient) -> dict:
    return client.post("/api/v1/executions", json={
        "agent_id": "agent-customer-refund",
        "input_summary": "Refund order #999 for $650",
        "tool_calls": [{"tool": "execute_refund", "arguments": {"amount": 650},
                        "idempotency_key": "order-999"}],
    }).json()


def _pending(client: TestClient, execution_id: str) -> list[dict]:
    approvals = client.get("/api/v1/approvals").json()["items"]
    return [a for a in approvals if a["execution_id"] == execution_id]


def test_650_refund_waits_for_two_approvals(client: TestClient) -> None:
    body = _start_650_refund(client)
    assert body["execution"]["status"] == "WAITING_APPROVAL"
    # No tool call executed yet.
    assert body["tool_calls"] == []
    approvals = _pending(client, body["execution"]["id"])
    roles = sorted(a["requested_from_role"] for a in approvals)
    assert roles == ["BUSINESS_APPROVER", "FINANCE_APPROVER"]
    assert all(a["status"] == "PENDING" for a in approvals)


def test_business_alone_does_not_execute(client: TestClient) -> None:
    body = _start_650_refund(client)
    exec_id = body["execution"]["id"]
    biz = next(a for a in _pending(client, exec_id) if a["requested_from_role"] == "BUSINESS_APPROVER")

    client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": BUSINESS})
    still = client.get(f"/api/v1/executions/{exec_id}").json()
    assert still["execution"]["status"] == "WAITING_APPROVAL"
    assert still["tool_calls"] == []


def test_both_approvals_complete_and_execute_once(client: TestClient) -> None:
    body = _start_650_refund(client)
    exec_id = body["execution"]["id"]
    approvals = _pending(client, exec_id)
    biz = next(a for a in approvals if a["requested_from_role"] == "BUSINESS_APPROVER")
    fin = next(a for a in approvals if a["requested_from_role"] == "FINANCE_APPROVER")

    client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": BUSINESS})
    client.post(f"/api/v1/approvals/{fin['id']}/approve", json={"actor_user_id": FINANCE})

    detail = client.get(f"/api/v1/executions/{exec_id}").json()
    assert detail["execution"]["status"] == "COMPLETED"
    refund_calls = [t for t in detail["tool_calls"] if t["tool_id"] == "execute_refund"]
    assert len(refund_calls) == 1  # refund executed exactly once
    assert "demo_refund_order-999" in refund_calls[0]["result_summary"]


def test_wrong_role_cannot_approve(client: TestClient) -> None:
    body = _start_650_refund(client)
    biz = next(a for a in _pending(client, body["execution"]["id"])
               if a["requested_from_role"] == "BUSINESS_APPROVER")
    # Developer persona cannot approve a business approval.
    resp = client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": DEV})
    assert resp.status_code == 403
    # And a finance persona cannot stand in for the business approver either.
    resp2 = client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": FINANCE})
    assert resp2.status_code == 403


def test_rejection_blocks_workflow(client: TestClient) -> None:
    body = _start_650_refund(client)
    exec_id = body["execution"]["id"]
    biz = next(a for a in _pending(client, exec_id) if a["requested_from_role"] == "BUSINESS_APPROVER")

    client.post(f"/api/v1/approvals/{biz['id']}/reject", json={"actor_user_id": BUSINESS})
    detail = client.get(f"/api/v1/executions/{exec_id}").json()
    assert detail["execution"]["status"] == "BLOCKED"
    assert [t for t in detail["tool_calls"] if t["tool_id"] == "execute_refund"] == []


def test_double_approval_is_safe(client: TestClient) -> None:
    body = _start_650_refund(client)
    exec_id = body["execution"]["id"]
    approvals = _pending(client, exec_id)
    biz = next(a for a in approvals if a["requested_from_role"] == "BUSINESS_APPROVER")
    fin = next(a for a in approvals if a["requested_from_role"] == "FINANCE_APPROVER")

    # Approve business twice — the second is a no-op.
    client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": BUSINESS})
    again = client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": BUSINESS})
    assert again.json()["status"] == "APPROVED"

    client.post(f"/api/v1/approvals/{fin['id']}/approve", json={"actor_user_id": FINANCE})
    # Approve business a third time after completion — still safe, no re-execution.
    client.post(f"/api/v1/approvals/{biz['id']}/approve", json={"actor_user_id": BUSINESS})

    detail = client.get(f"/api/v1/executions/{exec_id}").json()
    assert detail["execution"]["status"] == "COMPLETED"
    assert len([t for t in detail["tool_calls"] if t["tool_id"] == "execute_refund"]) == 1
