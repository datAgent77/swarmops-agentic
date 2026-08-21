# SwarmOps — Build Plan

SwarmOps is an **Enterprise Agent Control Plane** — _Discover. Govern. Orchestrate. Observe._
Primary hackathon category: **Fortified Enterprise Fleet** (Google All Things Agentic Hackathon 2026).

This document is the persistent build plan. Each phase continues from the previous
repository state — **preserve working functionality; do not rewrite from scratch.**

## Working agreement (every phase)

1. Inspect the existing repository.
2. Read `README.md` and this `docs/BUILD_PLAN.md`.
3. Inspect existing architecture and tests.
4. Preserve all working functionality.
5. Run tests before starting.
6. Implement only the requested phase plus required fixes.
7. Run tests again.
8. Update documentation if architecture changes.

## Architecture at a glance

- **apps/web** — Next.js (App Router, TS, Tailwind, shadcn/ui). Operational shell.
- **apps/api** — FastAPI, layered `api / application / domain / infrastructure`.
- **agents/** — Google ADK agents (from P07).
- **packages/** — shared contracts/utilities (as needed).
- **infrastructure/** — Terraform / deploy scripts (from P12).
- **docs/** — architecture, ADRs, security, deployment, demo.

## Phase roadmap

| Phase | Title | Status |
|-------|-------|--------|
| P00 | Repository Foundation & Architecture | ✅ complete |
| P01 | Domain Model, Repositories & Demo Data | ✅ complete |
| P02 | Deterministic Risk Engine | ✅ complete |
| P03 | Policy Engine & Governance Rules | ⬜ pending |
| P04 | Execution State Machine & Safe Tool Layer | ⬜ pending |
| P05 | Human Approval Workflow | ⬜ pending |
| P06 | Quarantine, Discovery & Governance Lifecycle | ⬜ pending |
| P07 | Google ADK + Gemini Governance Agent | ⬜ pending |
| P08 | Agent Dependency Graph & Blast Radius | ⬜ pending |
| P09 | Audit Trail & OpenTelemetry Observability | ⬜ pending |
| P10 | Security Layer, Prompt Injection & Model Armor | ⬜ pending |
| P11 | Agent Version Intelligence & Self-Evolving Governance | ⬜ pending |
| P12 | Google Cloud Persistence, Pub/Sub & Cloud Run | ⬜ pending |
| P13 | Gemini Enterprise Agent Platform Adapters | ⬜ pending |
| P14 | Demo Hardening, UX Polish & Submission Readiness | ⬜ pending |

## Non-negotiable principles

- **Deterministic governance decides.** No LLM is in the authorization path.
  Gemini explains; it never overrides a DENY or QUARANTINE.
- **Backend is the source of truth.** All state persists; the UI is a view.
- **Everything is auditable.** Every decision is an append-only event.
- **Truthful integrations.** A demo adapter is never labeled LIVE.

## P00 — delivered

- Monorepo scaffold (`apps/`, `agents/`, `packages/`, `infrastructure/`, `docs/`, `tests/`).
- FastAPI backend with layered architecture; `GET /health`, `GET /api/v1/status`.
- Next.js operational shell with the full navigation set and placeholder pages.
- `make dev|test|lint`, Dockerfiles, `docker-compose.yml`, `.env.example`.
- Architecture doc + `ADR-001-domain-first-architecture.md`.
- Backend tests (pytest) green; ruff + mypy clean.

## P01 — delivered

- Domain models: Organization, User, Agent, AgentVersion, Tool, AgentDependency +
  enums (Role, AgentStatus, AutonomyLevel, ToolType, RiskLevel, DependencyTargetType,
  Relationship). Severity is a derived band shared with P02.
- Repository interfaces (ports) in `domain/repositories.py`; SQLite implementations in
  `infrastructure/` behind a `RepositoryContainer` (Firestore variant lands in P12).
- Deterministic AcmeCorp seed: exactly **127 agents / 43 active / 9 high-risk / 3
  quarantined**, 8 named agents (with versions), 6 tools, and CustomerRefundAgent's
  5 dependencies. No wall-clock/randomness, so `/demo/reset` is byte-stable.
- API: `GET /api/v1/agents` (filters: status, department, risk, search, limit/offset),
  `GET /api/v1/agents/{id}`, `GET /api/v1/users`, `GET /api/v1/organizations/current`
  (with fleet stats), `POST /api/v1/demo/reset`.
- Frontend: Overview tiles from live stats + Reset Demo; Agents table with
  filter/search + owner names; Agent detail with tabs (Overview, Dependencies,
  Versions live; later tabs phase-tagged).
- Tests: 15 backend tests (repository CRUD + API + deterministic reset); ruff + mypy
  clean; frontend typecheck + lint + build green.

## P02 — delivered

- Deterministic risk engine (`domain/risk_engine.py`), pure and LLM-free. Seven
  weighted dimensions summing to 100: PII 20, financial 20, production-write 15,
  external-tools 10, autonomy 15, missing-approval-gate 10, prompt/tool-security 10.
  Severity bands: LOW <25, MODERATE 25–49, HIGH 50–74, CRITICAL 75+.
- **CustomerRefundAgent v2 = 87/100 CRITICAL → QUARANTINE**, from an explainable
  breakdown (16+20+15+8+15+10+3) — not a hard-coded number.
- `RiskAssessment` model + repository + table (`data_score` holds the
  approval-gap dimension per the schema). Assessments are immutable and persisted.
- Application service assembles the engine input from repositories, records the
  assessment, and syncs the agent's `risk_score` to the computed value.
- API: `POST /api/v1/agents/{id}/assess-risk`, `GET /api/v1/agents/{id}/risk`.
- Frontend: Agent detail **Risk** tab — score, severity, recommended action, drivers,
  per-dimension breakdown bars, and an explicit "deterministic score / AI explanation
  is a future layer" note.
- Tests: 23 backend total (+8): severity boundaries (24/25, 49/50, 74/75), refund=87
  breakdown, low-risk stays LOW, missing-approval raises risk, API assess/get/sync/404.
  ruff + mypy clean; frontend green.

> **Invariant reinforced:** the engine is the sole authority on risk. Gemini (P07)
> will explain but never alter a score, severity, or recommended action.
