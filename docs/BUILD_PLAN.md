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
| P03 | Policy Engine & Governance Rules | ✅ complete |
| P04 | Execution State Machine & Safe Tool Layer | ✅ complete |
| P05 | Human Approval Workflow | ✅ complete |
| P06 | Quarantine, Discovery & Governance Lifecycle | ✅ complete |
| P07 | Google ADK + Gemini Governance Agent | ⬜ pending |
| P08 | Agent Dependency Graph & Blast Radius | ⬜ pending |
| P09 | Audit Trail & OpenTelemetry Observability | ⬜ pending |
| P10 | Security Layer, Prompt Injection & Model Armor | ⬜ pending |
| P11 | Agent Version Intelligence & Self-Evolving Governance | ⬜ pending |
| P12 | Google Cloud Persistence, Pub/Sub & Cloud Run | ⬜ pending |
| P13 | Gemini Enterprise Agent Platform Adapters | ⬜ pending |
| P14 | Demo Hardening, UX Polish & Submission Readiness | ⬜ pending |

## P06 note — keep the demo story in sync with seed data

CustomerRefundAgent is seeded ACTIVE with risk_score 72. The demo narrative needs a
**newly discovered rogue v2** that assesses to ~87 CRITICAL and is auto-quarantined.
In P06, model this explicitly: the discovery flow introduces/《re-discovers》the rogue
v2 (DISCOVERED → PENDING_REVIEW → risk → policy → QUARANTINED) rather than the seed
pre-quarantining it. Keep the seed's initial state distinct from the discovered rogue
state so the demo (`discover → assess → quarantine → govern → execute → pause →
approve → resume exactly once`) stays coherent.

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

## P03 — delivered

- Deterministic policy engine (`domain/policy_engine.py`): JSON conditions with a
  fixed operator whitelist (eq, neq, gt, gte, lt, lte, in, contains, exists) plus
  `all`/`any` groups. **No `eval`/`exec`** — every value is inert data; malformed or
  unknown-operator conditions are rejected up front.
- First-match-by-priority evaluation → `PolicyDecision` (action + required_roles +
  reason); defaults to ALLOW when nothing matches.
- Policy model + repository + table; `parameters` holds action metadata
  (e.g. approval roles). Five seed policies: Small/Medium/Large Refund, PII Export
  (DENY), Rogue Financial Agent (QUARANTINE).
- API: `GET/POST /api/v1/policies`, `PUT /api/v1/policies/{id}`,
  `POST /api/v1/policies/evaluate`. Create/update validate the condition (400 on bad op).
- Frontend: Policies page — human-readable rule, required roles, action/priority/scope
  badges, enabled state, and the underlying condition JSON.
- Tests: 37 backend total (+14): operators, all/any, invalid-operator rejection,
  no-code-execution, priority ordering, refund $50/$300/$650, PII DENY, rogue QUARANTINE,
  CRUD + API validation. ruff + mypy clean; frontend green.

> **Local-dev note:** the SQLite `swarmops.db` only seeds when empty. After pulling a
> new phase, call `POST /api/v1/demo/reset` (or delete `swarmops.db`) to pick up new
> seed data such as the policies added here.

## P04 — delivered

- Execution state machine (`domain/execution_state.py`): explicit transition table over
  QUEUED/RUNNING/WAITING_APPROVAL/BLOCKED/FAILED/COMPLETED/CANCELLED; illegal moves raise
  `InvalidStateTransition`; terminal states are dead-ends.
- Safe demo tool layer (`infrastructure/tool_layer.py`): get_customer, get_order,
  calculate_refund, execute_refund, send_email, get_salesforce_case. Every tool is a mock —
  **`execute_refund` never contacts Stripe**; it returns `demo_refund_<key>`.
- Execution + ToolCall models, repositories, tables. Execution service orchestrates
  QUEUED→RUNNING→(tool calls)→COMPLETED, records tool calls, and finalizes duration/cost.
- **Idempotency:** a state-changing tool call with a previously seen key is replayed from
  the prior result — the tool never executes twice (no duplicate refunds).
- **Quarantine guard:** a QUARANTINED agent cannot start an execution (409).
- API: `GET /api/v1/executions`, `POST /api/v1/executions`, `GET /api/v1/executions/{id}`.
- Frontend: Executions table (Execution/Agent/Status/Started/Duration/Risk/Trace) + execution
  detail page with tool-call breakdown.
- Tests: 47 backend total (+10): valid/invalid transitions, refund demo tool, all tools,
  run+complete, idempotent replay, quarantine block, unknown tool, list/get. ruff + mypy + web green.

> Policy-gated approvals (RUNNING→WAITING_APPROVAL and back) arrive in P05; the state
> machine and the WAITING_APPROVAL state are already in place.

## P05 — delivered

- Executions are now **governed**: `POST /executions` evaluates policy on the tool-call
  context. ALLOW runs immediately; DENY/QUARANTINE → BLOCKED; REQUIRE_APPROVAL →
  WAITING_APPROVAL with the tool calls deferred (`pending_actions`).
- ApprovalRequest model + repository + table (PENDING/APPROVED/REJECTED/EXPIRED). One
  request per required role, sequenced. Durable (SQLite) → survives restart.
- The **$650 refund flow**: RUNNING → policy (Large Refund) → WAITING_APPROVAL →
  Business Approver → Finance Approver → RUNNING → demo refund → COMPLETED.
- **Role enforcement is server-side**: the acting persona must actually hold the
  required role (looked up in the users table); the UI switcher is not the authority.
- **Exactly-once + idempotent**: the deferred refund runs once when all approvals land;
  a rejection blocks the execution and expires remaining approvals; re-approving a
  resolved request is a safe no-op.
- API: `GET /api/v1/approvals`, `GET /api/v1/approvals/{id}`,
  `POST /api/v1/approvals/{id}/approve|reject` (body: `actor_user_id`).
- Frontend: Approval Queue — pending items with amount/role/step, an "acting as" persona
  switcher, and Approve/Reject wired to the backend (403 surfaced on wrong role).
- Tests: 53 backend total (+6): $650 waits, business-alone doesn't execute, both approvals
  complete + execute once, wrong role 403, rejection blocks, double approval safe.
  P04 refund API tests moved to $50 (ALLOW) to keep testing the immediate path.
  ruff + mypy + web build green.

## P06 — delivered

- Discovery port (`application/discovery.py`) + `DemoDiscoveryProvider`. The seed keeps
  CustomerRefundAgent benign (ACTIVE, risk 72); **discovery** is what pulls the rogue v2
  into review — the seed never pre-quarantines it (per the P06 note above).
- Deterministic lifecycle (`application/lifecycle_service.py`):
  DISCOVERED → PENDING_REVIEW → risk assessment (→ 87) → policy evaluation (Rogue
  Financial Agent) → **QUARANTINED**, with a persisted reason. Duplicate discovery is safe.
- Quarantine behavior: new executions blocked (409); reason persisted + shown in the UI;
  audit events emitted; only a privileged operator can reactivate.
- Privileged quarantine/activate (PLATFORM_ADMIN or SECURITY_OFFICER); others get 403.
- Append-only audit foundation: `AuditEvent` model + repository + table + `record_event`
  helper. Lifecycle emits agent.discovered / pending_review / risk.assessed /
  policy.evaluated / agent.quarantined / agent.activated. (Full OTel + query endpoints: P09.)
- API: `POST /api/v1/agents/discover`, `POST /api/v1/agents/{id}/quarantine`,
  `POST /api/v1/agents/{id}/activate`.
- Frontend: "Discover Agents" action on the Agents page (with a result line) and a
  quarantine banner on agent detail ("Why was this agent quarantined?") with Reactivate.
- Tests: 59 backend total (+6): discovery quarantines the rogue (87), duplicate-safe,
  quarantined-cannot-execute, privileged reactivation (403 for non-privileged), manual
  quarantine privilege, audit events generated. ruff + mypy + web build green.

> The full demo arc now runs end to end:
> **discover → assess → quarantine → (reactivate under governance) → execute → pause →
> approve → resume exactly once.**
