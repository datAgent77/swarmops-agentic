# ADR-005 — Google Integration Adapter Pattern

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P13

## Context

SwarmOps must integrate with Google's enterprise agent platform (Agent Registry,
Runtime, Memory Bank, Gateway, Model Armor, Observability) without recreating that
infrastructure, and without live credentials during development or judging. It must
also **never misrepresent** a simulated capability as live.

## Decision

Define a provider interface per capability (`AgentRegistryProvider`,
`AgentRuntimeProvider`, `MemoryProvider`, `AgentGatewayProvider`, `ModelArmorProvider`,
`ObservabilityProvider`). Each `describe(settings)` returns an `IntegrationInfo` with a
truthful `IntegrationStatus`:

- `CONNECTED` — a genuine live Google integration is active.
- `DEMO_MODE` — SwarmOps provides a working local substitute.
- `NOT_CONFIGURED` — the capability is off.
- `ERROR` — configured but failing.

Demo implementations (`Demo*Provider`) back the capabilities today; real integrations
slot in behind the same interfaces. Status is computed from actual signals — installed
client, credentials, config, and the Cloud Run `K_SERVICE` env — so it cannot drift from
reality. Governance metadata (owner, risk, approval, policy, cost center, incidents)
stays authoritative in SwarmOps even when Google's Registry catalogs the agent.

## Consequences

- **Positive:** honest, verifiable status for judging; live integrations require no
  caller changes; SwarmOps never duplicates Google infrastructure.
- **Trade-off:** the demo providers are substitutes, not the real services; the
  Integrations page makes that explicit rather than hiding it.
- **Rejected:** hard-coding "connected" for the demo — it would misrepresent the system
  and violate the project's honesty invariant (see also ADR-002 and the Model Armor adapter).
