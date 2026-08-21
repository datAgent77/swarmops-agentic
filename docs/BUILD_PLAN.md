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
| P01 | Domain Model, Repositories & Demo Data | ⬜ pending |
| P02 | Deterministic Risk Engine | ⬜ pending |
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
