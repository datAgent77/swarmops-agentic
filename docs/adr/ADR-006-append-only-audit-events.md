# ADR-006 — Append-Only Audit Events

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P09

## Context

A governance control plane must be able to prove, after the fact, exactly what happened:
which agent was quarantined and why, who approved a refund, whether a tool ran twice.
That record must be trustworthy and reconstructable into an end-to-end trace.

## Decision

Every critical action emits an **append-only `AuditEvent`** (never updated or deleted):
discovery, risk assessment, policy evaluation, quarantine/activation, execution
start/block/resume/complete, approval requested/granted/rejected, tool-call completion,
security block, and change proposals. Each event carries `actor`, `action`, `resource`,
`decision`, `reason`, `metadata`, and a **`trace_id`** correlated to its execution.

Because events are trace-correlated, the audit trail doubles as the observability trace
(P09): `GET /observability/traces/{trace_id}` reconstructs the reasoning chain from the
persisted events — no external tracing backend required for the demo, with Cloud Trace
export available behind the `[otel]` extra.

## Consequences

- **Positive:** complete, tamper-evident history; the same record powers audit and
  observability; the E2E test asserts the full chain exists.
- **Trade-off:** append-only growth needs retention/archival in production (out of scope
  for the demo).
- **Rejected:** mutable status rows as the only record — they cannot answer "what
  happened and when," and would be trivially rewritten.
