# SwarmOps — System Architecture

_Enterprise Agent Control Plane · Discover. Govern. Orchestrate. Observe._

## Overview

SwarmOps sits **above** agent runtimes and control planes. It does not replace the
LLM, the agent framework, or the runtime — it is the management layer that makes an
AI workforce safe to run: identity, risk, policy, approvals, audit, and observability.

The system is a monorepo with a Next.js operational console and a layered FastAPI
backend. Authorization is **deterministic**; Gemini (via Google ADK / Vertex AI,
from P07) provides explanation and analysis only — never enforcement.

## Component diagram (P00 foundation)

```mermaid
flowchart TB
    subgraph Client["apps/web — Next.js Console"]
        UI["Operational Shell\n(Overview, Agents, Graph, Executions,\nApprovals, Policies, Security,\nObservability, Audit, Integrations)"]
    end

    subgraph API["apps/api — FastAPI"]
        direction TB
        A["api\n(thin route handlers)"]
        APP["application\n(use-cases)"]
        DOM["domain\n(models + deterministic rules)"]
        INFRA["infrastructure\n(persistence, external adapters)"]
        A --> APP --> DOM
        APP --> INFRA
        INFRA -.implements interfaces from.-> DOM
    end

    UI -->|"HTTP /api/v1/*"| A
    A --> H["/health/"]
    A --> S["/api/v1/status/"]

    subgraph Future["Later phases (P07+)"]
        ADK["agents/ — Google ADK\nGovernanceAgent"]
        GEM["Gemini via Vertex AI"]
        GCP["Cloud Run · Firestore · Pub/Sub\nModel Armor · Cloud Trace"]
    end

    APP -.P07.-> ADK -.P07.-> GEM
    INFRA -.P12.-> GCP
```

## Layering rules

- **api** — HTTP only. Validates input, calls the application layer, shapes responses.
  No business logic.
- **application** — orchestrates use-cases (risk assessment, policy evaluation,
  approvals, discovery lifecycle). Depends on domain + infrastructure interfaces.
- **domain** — pure models and deterministic rules. No framework or I/O imports.
- **infrastructure** — concrete adapters (SQLite/Firestore repositories, event bus,
  Gemini/ADK, Model Armor). Implements interfaces declared by the domain/application.

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
