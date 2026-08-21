"""Discovery + governance lifecycle: quarantine, reactivation, audit events."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.infrastructure.container import RepositoryContainer

ADMIN = "user-alex-admin"        # PLATFORM_ADMIN (privileged)
SECURITY = "user-sam-security"   # SECURITY_OFFICER (privileged)
DEV = "user-dana-dev"            # DEVELOPER (not privileged)
REFUND = "agent-customer-refund"


def test_discovery_quarantines_rogue(client: TestClient) -> None:
    body = client.post("/api/v1/agents/discover").json()
    result = body["discovered"][0]
    assert result["agent_id"] == REFUND
    assert result["risk_score"] == 87
    assert result["quarantined"] is True
    assert result["to_status"] == "QUARANTINED"

    agent = client.get(f"/api/v1/agents/{REFUND}").json()["agent"]
    assert agent["status"] == "QUARANTINED"
    assert agent["quarantine_reason"]


def test_duplicate_discovery_is_safe(client: TestClient) -> None:
    client.post("/api/v1/agents/discover")
    second = client.post("/api/v1/agents/discover").json()["discovered"][0]
    assert second["already_processed"] is True
    assert second["quarantined"] is True
    # Still exactly the original quarantine — no double processing.
    assert client.get(f"/api/v1/agents/{REFUND}").json()["agent"]["status"] == "QUARANTINED"


def test_quarantined_agent_cannot_execute(client: TestClient) -> None:
    client.post("/api/v1/agents/discover")
    resp = client.post("/api/v1/executions", json={
        "agent_id": REFUND, "input_summary": "should be blocked", "tool_calls": [],
    })
    assert resp.status_code == 409


def test_privileged_reactivation(client: TestClient) -> None:
    client.post("/api/v1/agents/discover")
    # Non-privileged cannot reactivate.
    assert client.post(f"/api/v1/agents/{REFUND}/activate",
                       json={"actor_user_id": DEV}).status_code == 403
    # Platform admin can.
    ok = client.post(f"/api/v1/agents/{REFUND}/activate", json={"actor_user_id": ADMIN})
    assert ok.status_code == 200
    assert ok.json()["status"] == "ACTIVE"
    assert ok.json()["quarantine_reason"] is None


def test_manual_quarantine_requires_privilege(client: TestClient) -> None:
    assert client.post("/api/v1/agents/agent-lead-qualification/quarantine",
                       json={"actor_user_id": DEV, "reason": "test"}).status_code == 403
    ok = client.post("/api/v1/agents/agent-lead-qualification/quarantine",
                     json={"actor_user_id": SECURITY, "reason": "manual hold"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "QUARANTINED"
    assert ok.json()["quarantine_reason"] == "manual hold"


def test_audit_events_generated(client: TestClient, container: RepositoryContainer) -> None:
    client.post("/api/v1/agents/discover")
    events = container.audit_events.list_for_resource("agent", REFUND)
    actions = [e.action for e in events]
    for expected in ("agent.discovered", "risk.assessed", "policy.evaluated", "agent.quarantined"):
        assert expected in actions
    quarantine_event = next(e for e in events if e.action == "agent.quarantined")
    assert quarantine_event.decision == "QUARANTINE"
