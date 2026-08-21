"""Policy API: seeded policies, refund scenarios, PII/rogue, CRUD, validation."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _evaluate(client: TestClient, context: dict) -> dict:
    return client.post("/api/v1/policies/evaluate", json={"context": context}).json()


def test_seed_policies_present(client: TestClient) -> None:
    policies = client.get("/api/v1/policies").json()
    assert len(policies) == 5
    # Returned in priority order.
    assert [p["priority"] for p in policies] == sorted(p["priority"] for p in policies)


def test_refund_scenarios(client: TestClient) -> None:
    small = _evaluate(client, {"refund": 50})
    assert small["action"] == "ALLOW"

    medium = _evaluate(client, {"refund": 300})
    assert medium["action"] == "REQUIRE_APPROVAL"
    assert medium["required_roles"] == ["BUSINESS_APPROVER"]

    large = _evaluate(client, {"refund": 650})
    assert large["action"] == "REQUIRE_APPROVAL"
    assert large["required_roles"] == ["BUSINESS_APPROVER", "FINANCE_APPROVER"]


def test_pii_export_denied(client: TestClient) -> None:
    decision = _evaluate(client, {"external_data_export": True, "contains_pii": True})
    assert decision["action"] == "DENY"
    assert decision["policy_id"] == "policy-pii-export"


def test_rogue_financial_agent_quarantined(client: TestClient) -> None:
    decision = _evaluate(client, {
        "risk_score": 87, "financial_capability": True, "approval_gate": False,
    })
    assert decision["action"] == "QUARANTINE"
    assert decision["policy_id"] == "policy-rogue-financial-agent"


def test_no_match_defaults_allow(client: TestClient) -> None:
    decision = _evaluate(client, {"unrelated": 1})
    assert decision["matched"] is False
    assert decision["action"] == "ALLOW"


def test_create_and_update_policy(client: TestClient) -> None:
    created = client.post("/api/v1/policies", json={
        "name": "Block Weekend Deploys",
        "description": "No production writes on weekends.",
        "scope": "deploy", "priority": 5,
        "condition": {"field": "is_weekend", "op": "eq", "value": True},
        "action": "DENY",
    })
    assert created.status_code == 201
    pid = created.json()["id"]
    assert pid == "policy-block-weekend-deploys"

    # It now participates in evaluation at its priority.
    assert _evaluate(client, {"is_weekend": True})["policy_id"] == pid

    updated = client.put(f"/api/v1/policies/{pid}", json={"enabled": False})
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert _evaluate(client, {"is_weekend": True})["policy_id"] != pid


def test_invalid_operator_rejected_by_api(client: TestClient) -> None:
    resp = client.post("/api/v1/policies", json={
        "name": "Bad", "condition": {"field": "x", "op": "regex", "value": ".*"}, "action": "DENY",
    })
    assert resp.status_code == 400
