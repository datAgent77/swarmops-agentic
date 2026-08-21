# ADR-003 — Persistence Strategy (SQLite local, Firestore in cloud)

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P12

## Context

Local development must be zero-setup and deterministic, while the cloud deployment
needs a managed, serverless datastore that fits Cloud Run's scale-to-zero model. The
domain already depends only on repository interfaces (ADR-001), so the backend is a
swappable detail.

## Decision

Provide two repository implementations behind the same interfaces, selected by
`PERSISTENCE_BACKEND`:

- **`local`** — SQLite (`Database` + `Sqlite*Repository`). Default; used for dev, tests,
  and the demo. In-memory (`:memory:`) in tests for isolation.
- **`firestore`** — Firestore (`Fs*Repository`), storing each entity as
  `model.model_dump(mode="json")` and reconstructing with `model_validate`. Selected in
  Cloud Run; testable locally against the Firestore emulator.

`RepositoryContainer` wires one backend or the other; nothing above the infrastructure
layer changes. `google-cloud-firestore` is an optional `[gcp]` extra.

## Consequences

- **Positive:** local stays trivial and fast; cloud uses a managed store; the swap is a
  single env var; the uniform dump/validate mapping keeps the Firestore layer small.
- **Trade-off:** Firestore list operations filter/sort in Python (demo-sized data); a
  production build would push hot queries into Firestore indexes.
- **Rejected:** Postgres/Cloud SQL — heavier to operate and doesn't scale to zero as
  cleanly for a bursty demo workload.
