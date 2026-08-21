"""Domain event bus.

An ``EventBus`` decouples producers (services) from consumers (other services, Cloud
Functions, analytics). ``InMemoryEventBus`` is the default and is used in local dev and
tests; ``PubSubEventBus`` publishes to Google Cloud Pub/Sub when configured. Publishing
never breaks a request — a Pub/Sub failure is swallowed so governance still proceeds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# Canonical domain event names.
AGENT_DISCOVERED = "AgentDiscovered"
RISK_ASSESSMENT_COMPLETED = "RiskAssessmentCompleted"
AGENT_QUARANTINED = "AgentQuarantined"
APPROVAL_REQUESTED = "ApprovalRequested"
APPROVAL_GRANTED = "ApprovalGranted"
TOOL_CALL_COMPLETED = "ToolCallCompleted"
EXECUTION_COMPLETED = "ExecutionCompleted"


@dataclass(frozen=True)
class DomainEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...


class InMemoryEventBus(EventBus):
    """Captures events in-process. Handy for local dev, tests, and the demo."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    def names(self) -> list[str]:
        return [e.name for e in self.events]


class PubSubEventBus(EventBus):
    """Publishes each event to a Pub/Sub topic named ``swarmops-<EventName>``.

    Lazily imports the client so ``google-cloud-pubsub`` stays an optional dependency.
    """

    def __init__(self, project: str, prefix: str = "swarmops-") -> None:
        self.project = project
        self.prefix = prefix
        self._publisher = None

    def _client(self):  # pragma: no cover - requires the optional SDK + credentials
        if self._publisher is None:
            from google.cloud import pubsub_v1

            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def publish(self, event: DomainEvent) -> None:  # pragma: no cover - requires Pub/Sub
        import json

        try:
            client = self._client()
            topic = client.topic_path(self.project, f"{self.prefix}{event.name}")
            client.publish(topic, json.dumps(event.payload).encode("utf-8"))
        except Exception:  # noqa: BLE001 — never fail a governed action on telemetry
            pass


def build_event_bus(backend: str, project: str | None) -> EventBus:
    if backend == "pubsub" and project:  # pragma: no cover - requires config
        return PubSubEventBus(project)
    return InMemoryEventBus()
