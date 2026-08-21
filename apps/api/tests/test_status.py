"""Status endpoint contract."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_status_shape(client: TestClient) -> None:
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    body = resp.json()

    assert body["service"] == "swarmops-api"
    assert body["category"] == "Fortified Enterprise Fleet"
    assert body["tagline"] == "Discover. Govern. Orchestrate. Observe."
    # Foundational fields are present and typed as expected.
    assert isinstance(body["demo_mode"], bool)
    assert isinstance(body["version"], str)
    assert isinstance(body["environment"], str)
