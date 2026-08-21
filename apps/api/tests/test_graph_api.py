"""Dependency graph generation + deterministic blast-radius."""

from __future__ import annotations

from fastapi.testclient import TestClient

REFUND = "agent-customer-refund"


def test_agent_graph_shows_refund_dependencies(client: TestClient) -> None:
    graph = client.get(f"/api/v1/agents/{REFUND}/graph").json()
    labels = {n["label"] for n in graph["nodes"]}
    for expected in ("CustomerRefundAgent", "Customer Database", "Salesforce", "Stripe",
                     "Refund API", "Email"):
        assert expected in labels
    # A model node is derived from the agent's model.
    assert any(n["type"] == "model" for n in graph["nodes"])
    # Nothing is a live integration — all dependency metadata.
    assert all(n["connection"] == "metadata" for n in graph["nodes"])
    # Dangerous edges (HIGH/CRITICAL) are flagged for highlighting.
    assert any(e["dangerous"] for e in graph["edges"])


def test_node_types_are_classified(client: TestClient) -> None:
    graph = client.get(f"/api/v1/agents/{REFUND}/graph").json()
    by_label = {n["label"]: n["type"] for n in graph["nodes"]}
    assert by_label["Customer Database"] == "database"
    assert by_label["Stripe"] == "external_api"
    assert by_label["Refund API"] == "tool"


def test_fleet_graph_is_a_network(client: TestClient) -> None:
    graph = client.get("/api/v1/graph").json()
    agent_nodes = [n for n in graph["nodes"] if n["type"] == "agent"]
    # Refund + the extra seeded agents all appear.
    assert len(agent_nodes) >= 4
    assert len(graph["edges"]) >= 8


def test_blast_radius_flags(client: TestClient) -> None:
    br = client.get(f"/api/v1/agents/{REFUND}/blast-radius").json()
    assert br["pii_reachable"] is True
    assert br["financial_action_reachable"] is True
    assert br["production_write_path"] is True
    assert br["external_exfiltration_path"] is True
    assert br["reachable_nodes"] == 5
    assert "PII reachable" in br["indicators"]


def test_blast_radius_benign_agent(client: TestClient) -> None:
    br = client.get("/api/v1/agents/agent-employee-onboarding/blast-radius").json()
    assert br["pii_reachable"] is False
    assert br["financial_action_reachable"] is False
    assert br["reachable_nodes"] == 0
    assert br["indicators"] == []


def test_blast_radius_unknown_agent_404(client: TestClient) -> None:
    assert client.get("/api/v1/agents/nope/blast-radius").status_code == 404
