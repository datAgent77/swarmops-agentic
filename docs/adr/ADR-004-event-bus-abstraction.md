# ADR-004 — Event Bus Abstraction

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P12

## Context

Governance produces meaningful domain events (an agent is quarantined, an approval is
granted, an execution completes). Other systems — analytics, notifications, downstream
agents — will want these without coupling to SwarmOps internals. Locally we want the
same events observable in-process for tests and the demo.

## Decision

Introduce an `EventBus` interface with two implementations, selected by `EVENT_BUS`:

- **`InMemoryEventBus`** (default) — captures events in-process; used in dev, tests, and
  the demo (assertable, zero infra).
- **`PubSubEventBus`** — publishes each event to a Pub/Sub topic `swarmops-<EventName>`.

Seven canonical events are published: `AgentDiscovered`, `RiskAssessmentCompleted`,
`AgentQuarantined`, `ApprovalRequested`, `ApprovalGranted`, `ToolCallCompleted`,
`ExecutionCompleted`. Publishing is **best-effort**: a Pub/Sub failure is swallowed so a
governed action never fails on telemetry.

## Consequences

- **Positive:** producers depend only on the interface; consumers can be added out of
  band; tests assert on the in-memory bus; `google-cloud-pubsub` is an optional `[gcp]` extra.
- **Trade-off:** best-effort publish can drop an event under failure; the append-only
  audit trail (ADR-006) remains the durable record, so no governance history is lost.
- **Rejected:** publishing synchronously and failing the request — telemetry must never
  block or break governance.
