"""API coverage for agents, users, organization, and demo reset."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_agents_and_total(client: TestClient) -> None:
    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 127
    assert len(body["items"]) == 127
    # Computed severity is exposed on each agent.
    assert "severity" in body["items"][0]


def test_agent_filters_over_api(client: TestClient) -> None:
    assert client.get("/api/v1/agents", params={"status": "QUARANTINED"}).json()["total"] == 3
    assert client.get("/api/v1/agents", params={"risk": "HIGH"}).json()["total"] == 9
    assert client.get("/api/v1/agents", params={"status": "ACTIVE"}).json()["total"] == 43

    search = client.get("/api/v1/agents", params={"search": "refund"}).json()
    assert any(a["id"] == "agent-customer-refund" for a in search["items"])


def test_agent_detail(client: TestClient) -> None:
    resp = client.get("/api/v1/agents/agent-customer-refund")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"]["name"] == "CustomerRefundAgent"
    assert len(body["versions"]) == 1
    assert len(body["dependencies"]) == 5

    assert client.get("/api/v1/agents/does-not-exist").status_code == 404


def test_organization_current_stats(client: TestClient) -> None:
    body = client.get("/api/v1/organizations/current").json()
    assert body["name"] == "AcmeCorp"
    stats = body["stats"]
    assert stats["total_agents"] == 127
    assert stats["active"] == 43
    assert stats["high_risk"] == 9
    assert stats["quarantined"] == 3
    # Severity + status breakdowns for the Overview dashboard.
    assert sum(stats["by_severity"].values()) == 127
    assert stats["by_severity"]["CRITICAL"] == 3
    assert stats["by_status"]["ACTIVE"] == 43
    assert sum(stats["by_status"].values()) == 127


def test_users_endpoint(client: TestClient) -> None:
    body = client.get("/api/v1/users").json()
    assert len(body["items"]) == 5


def test_demo_reset(client: TestClient) -> None:
    body = client.post("/api/v1/demo/reset").json()
    assert body["status"] == "reset"
    assert body["total_agents"] == 127
    # Metrics unchanged after a deterministic reset.
    assert client.get("/api/v1/organizations/current").json()["stats"]["active"] == 43
