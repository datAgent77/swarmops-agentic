# SwarmOps — System Architecture

_Enterprise Agent Control Plane · Discover. Govern. Orchestrate. Observe._

## Overview

SwarmOps sits **above** agent runtimes and control planes. It does not replace the
LLM, the agent framework, or the runtime — it is the management layer that makes an
AI workforce safe to run: identity, risk, policy, approvals, audit, and observability.

The system is a monorepo with a Next.js operational console and a layered FastAPI
backend. Authorization is **deterministic**; the GovernanceAgent (Google **ADK** with
Gemini via the GenAI SDK / Vertex AI) provides explanation and analysis only — never
enforcement.

## Component diagram (final, P00–P14)

```mermaid
flowchart TB
    UI["SwarmOps Web Console (Next.js on Cloud Run)"]
    UI -->|"HTTP /api/v1/*"| API["FastAPI Control Plane (layered: api / application / domain / infrastructure)"]

    subgraph Governance["Deterministic governance (no LLM in the authorization path)"]
        RISK["Risk Engine"]
        POL["Policy Engine"]
        EXEC["Execution State Machine + Safe Tools"]
        HUM["Human Approval Engine"]
        SEC["Security Scanner / Model Armor"]
    end

    subgraph AI["AI layer (explains, never decides)"]
        GA["GovernanceAgent — Google ADK LlmAgent"]
        GEM["Gemini (GenAI SDK / Vertex AI)"]
        GA --> GEM
    end

    API --> RISK --> POL
    POL -->|"REQUIRE_APPROVAL"| HUM
    POL -->|"DENY / QUARANTINE"| EXEC
    API --> EXEC
    API --> SEC
    GA -. annotates .-> POL

    subgraph Cloud["Google Cloud"]
        FS[("Firestore")]
        PS(("Pub/Sub"))
        CT["Cloud Trace"]
        SM["Secret Manager"]
    end

    API --> AUD["Append-only Audit + Traces"]
    API --> FS
    API --> PS
    AUD --> CT
    API -.secrets.-> SM
```

## Layering rules

- **api** — HTTP only. Validates input, calls the application layer, shapes responses.
  No business logic.
- **application** — orchestrates use-cases (risk assessment, policy evaluation,
  approvals, discovery lifecycle). Depends on domain + infrastructure interfaces.
- **domain** — pure models and deterministic rules. No framework or I/O imports.
- **infrastructure** — concrete adapters (SQLite/Firestore repositories, in-memory/
  Pub/Sub event bus, Gemini/ADK, Model Armor, telemetry). Implements interfaces declared
  by the domain/application.

The dependency arrow always points **inward** toward the domain.

## Governance principle

```mermaid
flowchart LR
    Req["Proposed action"] --> Risk["Deterministic Risk Engine\n(P02)"]
    Risk --> Policy["Deterministic Policy Engine\n(P03)"]
    Policy -->|"REQUIRE_APPROVAL"| Human["Human Approval\n(P05)"]
    Policy -->|"DENY / QUARANTINE"| Block["Blocked + Audited"]
    Human --> Exec["Execution / Tool Layer\n(P04)"]
    Gemini["Gemini explanation (P07)"] -. annotates, never overrides .-> Policy
    Exec --> Audit["Append-only Audit + Traces\n(P09)"]
```

Gemini's output can **annotate** a decision but can never flip a DENY or QUARANTINE.
That invariant is enforced in code and tested from P07 onward.
