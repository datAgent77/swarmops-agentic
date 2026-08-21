# SwarmOps — Enterprise Agent Control Plane

**Discover. Govern. Orchestrate. Observe.**

SwarmOps sits above agent runtimes and control planes to make an AI workforce safe
to run in a real company: agent discovery, deterministic risk & policy enforcement,
human approvals, blast-radius analysis, append-only audit, and observability.

- **Hackathon track:** Fortified Enterprise Fleet
- **Built for:** Google All Things Agentic Hackathon 2026

> **Governance is deterministic.** No LLM sits in the authorization path. Gemini
> (via Google ADK / Vertex AI, from P07) explains and analyzes — it can never
> override a DENY or QUARANTINE.

## Repository structure

```
swarmops-agentic/
├── apps/
│   ├── web/            Next.js console (App Router, Tailwind, shadcn/ui)
│   └── api/            FastAPI backend (api / application / domain / infrastructure)
├── agents/            Google ADK agents (P07+)
├── packages/          Shared contracts/utilities
├── infrastructure/    Terraform / deploy scripts (P12+)
├── docs/              Architecture, ADRs, security, deployment, demo
├── tests/             Cross-cutting / E2E tests (P14)
├── docker-compose.yml
├── Makefile
└── .env.example
```

See [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md) for the phased roadmap (P00–P14) and
[`docs/architecture/system.md`](docs/architecture/system.md) for the architecture.

## Prerequisites

- Python **3.11+** (developed on 3.13)
- Node.js **20+** (developed on 22) and npm
- Optional: Docker + Docker Compose

## Local setup

Copy the environment template:

```bash
cp .env.example .env
```

Install everything (creates the API virtualenv and installs the web deps):

```bash
make install
```

Or install each side individually:

```bash
make install-api
make install-web
```

## Run

Start the backend (`:8080`) and frontend (`:3000`) together:

```bash
make dev
```

Or run them separately:

```bash
make dev-api    # FastAPI on http://localhost:8080
make dev-web    # Next.js on http://localhost:3000
```

Verify the backend:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/status
```

Open the console at **http://localhost:3000** — it redirects to the fleet Overview.
The Overview page shows a live backend-connectivity check.

## With Docker

```bash
make up      # docker compose up --build  (web :3000, api :8080)
make down
```

## Quality

```bash
make test    # backend tests (pytest)
make lint    # ruff + mypy (backend), eslint + tsc (frontend)
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `development` / `production` |
| `DEMO_MODE` | Enables the deterministic demo scenario |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins (API) |
| `NEXT_PUBLIC_API_URL` | Backend base URL used by the web app |
| `GOOGLE_CLOUD_PROJECT` | GCP project (later phases) |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI / GCP region |
| `GOOGLE_GENAI_USE_VERTEXAI` | Route GenAI/ADK through Vertex AI |
| `GEMINI_MODEL` | Gemini model id (e.g. `gemini-3.5-flash`) |

No secrets are committed; `.env` is gitignored.

## Status

Built iteratively in phases (see [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md)).
**Complete through P07** — 65 backend tests green; ruff + mypy clean; web build green.

| Phase | Capability | Done |
|-------|------------|:----:|
| P00 | Monorepo foundation, health/status, operational shell | ✅ |
| P01 | Domain model, repositories, deterministic 127-agent AcmeCorp seed | ✅ |
| P02 | Deterministic risk engine (CustomerRefundAgent = 87/100 CRITICAL) | ✅ |
| P03 | Deterministic policy engine (JSON conditions, no `eval`) | ✅ |
| P04 | Execution state machine + safe (mock) tool layer + idempotency | ✅ |
| P05 | Durable human approval workflow (two-stage $650 refund) | ✅ |
| P06 | Discovery → auto risk/policy → quarantine, privileged reactivation | ✅ |
| P07 | GovernanceAgent (Gemini via GenAI SDK) explains, never overrides | ✅ |
| P08–P14 | Graph/blast-radius, audit/OTel, security, self-evolving, cloud | ⬜ |

**What works today — the full governed arc runs end to end:** discover the rogue
CustomerRefundAgent → it auto-assesses to 87/100 CRITICAL → policy quarantines it →
a privileged operator reactivates it → a $650 refund runs through the state machine →
pauses for two-stage human approval → resumes and executes **exactly once**, with an
append-only audit trail throughout. Browse the 127-agent fleet with live risk
severities, view/evaluate governance policies, and inspect executions and approvals.
No LLM sits in the authorization path — governance is deterministic; Gemini (P07) will
explain, never override.

Built for Google All Things Agentic Hackathon 2026.
