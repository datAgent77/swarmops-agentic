"""Risk assessment API: assess, persist, retrieve, and agent sync."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_assess_refund_agent(client: TestClient) -> None:
    resp = client.post("/api/v1/agents/agent-customer-refund/assess-risk")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_score"] == 87
    assert body["severity"] == "CRITICAL"
    assert body["recommended_action"] == "QUARANTINE"
    assert body["data_score"] == 10  # missing-approval-gate dimension


def test_get_risk_requires_prior_assessment(client: TestClient) -> None:
    # No assessment yet → 404.
    assert client.get("/api/v1/agents/agent-customer-support/risk").status_code == 404

    client.post("/api/v1/agents/agent-customer-support/assess-risk")
    got = client.get("/api/v1/agents/agent-customer-support/risk")
    assert got.status_code == 200
    assert got.json()["severity"] == "LOW"


def test_assessment_syncs_agent_risk_score(client: TestClient) -> None:
    client.post("/api/v1/agents/agent-customer-refund/assess-risk")
    agent = client.get("/api/v1/agents/agent-customer-refund").json()["agent"]
    assert agent["risk_score"] == 87
    assert agent["severity"] == "CRITICAL"


def test_assess_unknown_agent_404(client: TestClient) -> None:
    assert client.post("/api/v1/agents/nope/assess-risk").status_code == 404
    assert client.get("/api/v1/agents/nope/risk").status_code == 404
