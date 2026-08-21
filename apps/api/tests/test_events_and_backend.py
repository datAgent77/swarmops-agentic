"""Domain event bus wiring + persistence-backend selection."""

from __future__ import annotations

import importlib.util

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.container import RepositoryContainer
from app.infrastructure.events import (
    InMemoryEventBus,
    PubSubEventBus,
    build_event_bus,
)


def test_build_event_bus_selection() -> None:
    assert isinstance(build_event_bus("inmemory", None), InMemoryEventBus)
    assert isinstance(build_event_bus("pubsub", None), InMemoryEventBus)  # no project → local
    assert isinstance(build_event_bus("pubsub", "my-project"), PubSubEventBus)


def test_local_backend_is_default() -> None:
    assert RepositoryContainer(":memory:").backend == "local"


def _firestore_installed() -> bool:
    try:
        return importlib.util.find_spec("google.cloud.firestore") is not None
    except ModuleNotFoundError:
        return False


def test_firestore_backend_is_optional() -> None:
    if _firestore_installed():
        pytest.skip("google-cloud-firestore is installed; live path available")
    with pytest.raises(ModuleNotFoundError):
        RepositoryContainer(backend="firestore", project="demo")


def test_governed_flow_publishes_events(client: TestClient, container: RepositoryContainer) -> None:
    bus = container.event_bus
    assert isinstance(bus, InMemoryEventBus)

    client.post("/api/v1/agents/discover")
    execution = client.post("/api/v1/executions", json={
        "agent_id": "agent-invoice-processing",
        "input_summary": "Refund $650",
        "tool_calls": [{"tool": "execute_refund", "arguments": {"amount": 650}}],
    }).json()["execution"]

    approvals = client.get("/api/v1/approvals").json()["items"]
    for a in [x for x in approvals if x["execution_id"] == execution["id"]]:
        persona = {"BUSINESS_APPROVER": "user-blair-business",
                   "FINANCE_APPROVER": "user-morgan-finance"}[a["requested_from_role"]]
        client.post(f"/api/v1/approvals/{a['id']}/approve", json={"actor_user_id": persona})

    names = set(bus.names())
    assert {"AgentDiscovered", "AgentQuarantined", "RiskAssessmentCompleted",
            "ApprovalRequested", "ApprovalGranted", "ToolCallCompleted",
            "ExecutionCompleted"} <= names
