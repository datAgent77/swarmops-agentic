"""Integration status: truthful CONNECTED / DEMO_MODE / NOT_CONFIGURED."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _by_key(client: TestClient) -> dict:
    items = client.get("/api/v1/integrations/status").json()["integrations"]
    return {i["key"]: i for i in items}


def test_all_expected_integrations_present(client: TestClient) -> None:
    keys = set(_by_key(client))
    expected = {
        "gemini", "vertex_ai", "google_adk", "agent_registry", "agent_runtime",
        "memory_bank", "agent_gateway", "model_armor", "cloud_run", "pubsub",
        "firestore", "cloud_trace",
    }
    assert expected <= keys


def test_status_is_truthful_in_local_mode(client: TestClient) -> None:
    integ = _by_key(client)
    # Nothing is falsely reported as CONNECTED without cloud config.
    assert integ["firestore"]["status"] == "DEMO_MODE"        # local SQLite
    assert integ["pubsub"]["status"] == "DEMO_MODE"           # in-memory bus
    assert integ["cloud_trace"]["status"] == "DEMO_MODE"      # local telemetry
    assert integ["model_armor"]["status"] == "DEMO_MODE"      # local scanner
    assert integ["gemini"]["status"] == "NOT_CONFIGURED"      # no credentials
    assert integ["vertex_ai"]["status"] == "NOT_CONFIGURED"
    assert integ["cloud_run"]["status"] == "NOT_CONFIGURED"   # not on Cloud Run


def test_no_demo_provider_is_marked_connected(client: TestClient) -> None:
    integ = _by_key(client)
    for key in ("agent_registry", "memory_bank", "agent_gateway"):
        assert integ[key]["status"] == "DEMO_MODE"
        assert integ[key]["status"] != "CONNECTED"


def test_every_integration_has_enable_docs(client: TestClient) -> None:
    for i in client.get("/api/v1/integrations/status").json()["integrations"]:
        assert i["docs"] and i["detail"]
