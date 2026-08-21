"""Change proposal API: the LeadQualificationAgent v17 self-evolving demo."""

from __future__ import annotations

from fastapi.testclient import TestClient

LEAD = "agent-lead-qualification"


def test_propose_v17_is_rejected(client: TestClient) -> None:
    resp = client.post(f"/api/v1/agents/{LEAD}/change-proposals", json={})
    assert resp.status_code == 201
    body = resp.json()
    p = body["proposal"]
    assert p["base_version"] == "v16"
    assert p["candidate_version"] == "v17"
    assert (p["performance_before"], p["performance_after"]) == (71, 82)
    assert (p["compliance_before"], p["compliance_after"]) == (94, 70)
    assert p["decision"] == "REJECTED"
    assert p["reason"] == "Performance improvement does not justify compliance regression."
    # Striking deltas for the UI.
    assert body["performance_delta_pct"] > 0
    assert body["compliance_delta_pct"] < 0
    # Deterministic diff surfaced the changed aspects.
    assert "permissions" in p["changes"] and "model" in p["changes"]
    # Gemini explains but does not decide; no creds in tests → local template.
    assert body["explanation"]["model_status"] == "LOCAL_TEMPLATE"


def test_list_proposals(client: TestClient) -> None:
    client.post(f"/api/v1/agents/{LEAD}/change-proposals", json={})
    listing = client.get(f"/api/v1/agents/{LEAD}/change-proposals").json()
    assert listing["total"] >= 1


def test_evaluate_with_higher_threshold_accepts(client: TestClient) -> None:
    pid = client.post(f"/api/v1/agents/{LEAD}/change-proposals", json={}).json()["proposal"]["id"]
    # A permissive threshold flips the deterministic decision — proving it's the rule,
    # not an LLM, that decides.
    re = client.post(f"/api/v1/change-proposals/{pid}/evaluate", json={"allowed_regression": 30})
    assert re.json()["proposal"]["decision"] == "ACCEPTED"


def test_change_proposed_audit_event(client: TestClient) -> None:
    client.post(f"/api/v1/agents/{LEAD}/change-proposals", json={})
    actions = [e["action"] for e in client.get("/api/v1/audit").json()["items"]]
    assert "agent.change_proposed" in actions


def test_unknown_agent_404(client: TestClient) -> None:
    assert client.post("/api/v1/agents/nope/change-proposals", json={}).status_code == 404
