# ADR-001 — Domain-First (Layered) Architecture

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P00

## Context

SwarmOps is a governance control plane whose core value is **trustworthy,
deterministic decisions** about autonomous agents. Judging rewards architectural
discipline: clear decoupling, explicit state, and rules that no model can bypass.
We need a structure that keeps enforcement logic isolated from frameworks, I/O, and
LLMs so it stays testable and provably authoritative.

## Decision

Adopt a **domain-first, layered architecture** in the backend:

```
api             HTTP surface — thin FastAPI handlers, no business logic
application     use-cases / orchestration
domain          pure models + deterministic rules (no framework, no I/O)
infrastructure  adapters: persistence, event bus, Gemini/ADK, Model Armor
```

Dependencies point inward toward `domain`. Infrastructure implements interfaces
declared by the inner layers (dependency inversion). The frontend (`apps/web`) is a
view over backend state and never holds authority.

## Consequences

**Positive**

- The risk and policy engines (P02–P03) live in `domain` with zero LLM or I/O
  coupling, so they are trivially unit-testable and demonstrably deterministic.
- Persistence can move from SQLite (local) to Firestore (P12) by swapping an
  infrastructure adapter — no domain changes.
- Gemini/ADK integration (P07) plugs in at the application/infrastructure edge and
  is structurally unable to override deterministic authorization.

**Negative / trade-offs**

- More upfront boilerplate (interfaces + layers) than a flat FastAPI app.
- Requires discipline to keep route handlers thin.

**Rejected alternatives**

- _Flat FastAPI app_: fastest to start but entangles rules with I/O and framework,
  undermining the "no LLM in the authorization path" guarantee.
- _Framework-driven (Django-style) layout_: heavier ORM coupling, weaker fit for the
  swappable-persistence and adapter requirements of P12–P13.
