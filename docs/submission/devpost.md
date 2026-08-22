# SwarmOps — Devpost Submission

**Enterprise Agent Control Plane — Discover. Govern. Orchestrate. Observe.**
Category: **Fortified Enterprise Fleet** · Built for the Google All Things Agentic Hackathon 2026.

- **Live demo (Cloud Run):** https://swarmops-web-540436584629.us-central1.run.app
- **API (Cloud Run):** https://swarmops-api-540436584629.us-central1.run.app
- **Code:** https://github.com/datAgent77/swarmops-agentic

---

## Inspiration

Autonomous agents are entering the enterprise faster than governance can adapt. Companies
are deploying **hundreds** of agents that can deploy code, move money, and touch customer
data — with none of the controls they demand of human employees. The problem is no longer
how to *build* agents; it's how to **control** them. One over-privileged agent with a path
to PII and a payment API is a breach waiting to happen. SwarmOps is the control plane that
governs an AI workforce with the same rigor used for people.

## What it does

SwarmOps sits **above** agent runtimes and control planes and makes an AI workforce safe to
run. Its core invariant: **governance is deterministic — no LLM sits in the authorization
path.** Gemini explains and recommends; it can never override a DENY or QUARANTINE (proven
by tests that feed a hostile explainer and assert the decision stands).

The flagship end-to-end arc, all driven from a **Guided Demo** page against real backend logic:

- **Discover → auto-govern → quarantine.** Discovery pulls a rogue CustomerRefundAgent v2
  into review; the deterministic risk engine scores it **87/100 CRITICAL**; policy
  **quarantines** it automatically. Quarantined agents cannot execute.
- **Governed action, human-in-the-loop.** A privileged operator reactivates it under policy;
  a **$650 refund** runs through an execution state machine, **pauses for two-stage human
  approval** (Business + Finance, roles enforced by the backend), then **resumes and executes
  exactly once** (idempotent — never a duplicate refund, and never a real Stripe call).
- **Self-evolving governance.** A candidate agent version (LeadQualificationAgent v17) that
  improves performance **71→82** but regresses compliance **94→70** is **REJECTED** —
  self-evolving agents require self-evolving governance.

Supporting capabilities (every screen is production-ready):

- **Fleet & risk:** 127-agent SaitALCorp fleet with a deterministic, explainable 0–100 risk
  engine (7 weighted dimensions) and a SOC-style Overview (risk posture + status + recent activity).
- **Dependency graph & blast radius** (React Flow): every tool/DB/API/model an agent reaches,
  with dangerous-path highlighting and deterministic blast-radius indicators.
- **Deterministic policy engine** (JSON conditions, whitelisted operators, **no `eval`**).
- **Security scanner + Model Armor adapter:** blocks prompt injection / PII export / tool
  poisoning; the demo attack maps to a DENY policy + a security incident + an audit event.
- **Append-only audit trail + observability:** every decision/approval/tool call is
  trace-correlated; the audit trail doubles as an end-to-end reasoning-chain trace.
- **Truthful integrations:** an Integrations page reports **CONNECTED / DEMO_MODE /
  NOT_CONFIGURED** from real signals — a demo provider is never shown as live.

## How we built it (technologies used)

**Google technologies (all live on the deployment — Integrations shows 9 CONNECTED):**

- **Gemini 3.5 Flash** via **Vertex AI** (global endpoint) — the GovernanceAgent's explanation layer.
- **Google ADK** — the GovernanceAgent is a real `google.adk.agents.LlmAgent` exposing a
  fixed, constrained governance toolset (with a Google GenAI SDK fallback). Either is a
  Google Agent Framework.
- **Cloud Run** — API + web, scale-to-zero.
- **Firestore** — persistence behind the repository interfaces.
- **Pub/Sub** — domain event bus (seven canonical events).
- **Cloud Trace** — OpenTelemetry export of execution traces.
- **Secret Manager, Artifact Registry, IAM** — provisioned by Terraform.
- **Model Armor / Agent Registry / Runtime / Memory Bank / Gateway** — adapter seams with
  honest status (the demo providers stay DEMO_MODE).

**Stack:** FastAPI (Python 3.13), layered `api / application / domain / infrastructure`;
Next.js 14 (App Router, Tailwind, shadcn-style, React Flow); SQLite (local) / Firestore
(cloud) behind one repository interface; in-memory / Pub/Sub event bus; Terraform + a
gcloud `deploy.sh`; 103 backend tests (pytest), ruff + mypy clean.

## Data sources

The demo runs on a **deterministic seed** (SaitALCorp: 127 agents · 43 active · 9 high-risk ·
3 quarantined) so every run is reproducible. The mock tool layer (customer/order/refund/
email/Salesforce) is entirely simulated — `execute_refund` never contacts Stripe. No real
customer or third-party data is used.

## Findings & learnings

- **Determinism is the trust anchor.** Keeping the risk and policy engines free of any LLM —
  and making the AI layer *structurally* unable to override a decision — is what turns a demo
  into something an enterprise could actually trust. We enforce it in code and in tests.
- **Idempotency is a governance feature, not a footnote.** A pause/resume approval flow is
  only safe if the deferred action runs exactly once; the E2E test asserts a single refund.
- **Honesty scales trust.** Reporting integrations as DEMO_MODE / NOT_CONFIGURED instead of
  faking "connected" made the Google-native story stronger, not weaker.
- **Vertex AI Gemini 3.5 lives on the `global` endpoint** — regional endpoints didn't serve
  the 3.5 models; `GOOGLE_CLOUD_LOCATION=global` was the fix.
- **Next.js `NEXT_PUBLIC_*` is build-time**, so the API URL must be baked as a Docker build
  arg for a hosted frontend — a small but real deployment gotcha.

## Accomplishments

A complete, deterministic-by-design agent control plane, deployed live on Google Cloud with
Gemini 3.5 + Google ADK + Firestore + Pub/Sub + Cloud Trace all genuinely CONNECTED, a
full governed demo that runs end to end in under four minutes, and 103 green tests including
a full E2E flow.

## What's next

Bind the adapter seams to live Google Agent Registry / Runtime / Memory Bank / Gateway;
multi-turn ADK orchestration for the GovernanceAgent (keeping the no-override guarantee);
console authentication + per-tenant isolation; and live evaluators that derive performance/
compliance from execution history.

## Spin-up / reproducibility

`README.md` has full local setup (`make install && make dev`) and cloud deployment
(`./infrastructure/deploy.sh` or Terraform). See `docs/architecture/system.md` for the
architecture diagram and `docs/deployment/google-cloud.md` for the deploy walkthrough.

*Newly built during the submission period (August 2026); no pre-existing code incorporated;
built with standard frameworks and AI coding assistants, as permitted by the Official Rules.*
