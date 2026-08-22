# SwarmOps — 4-Minute Demo Script

Run the flow from the live Cloud Run deployment. Hit **RESET DEMO** (Overview or Settings)
first for a deterministic starting state.

**Thesis:** The problem is no longer how to *build* AI agents — it's how to *control* them.
SwarmOps turns agent sprawl into a governed AI workforce. Every autonomous agent should
have an owner, identity, policy, risk profile, trace, and kill switch.

## Before you record (required proof)

The Official Rules require the video to **demonstrate the backend running on Google Cloud**,
and Gemini must be genuinely leveraged. Set this up first:

1. **Record on the deployed `https://…run.app` URL** so the browser address bar is itself
   Google Cloud proof. (Backend + web are both on Cloud Run; Gemini 3.5 is live on Vertex AI.)
2. **Open two Google Cloud Console tabs** ready to cut to: the **Cloud Run** service
   dashboard (`swarmops-api` / `swarmops-web`) and **Vertex AI** request logs.
3. Confirm **Integrations** shows Gemini / Vertex AI / Google ADK **CONNECTED**.

Google Cloud proof appears three times: the `.run.app` address bar throughout, the Vertex
AI logs during the governance step, and the Cloud Run dashboard at the close.

---

**0:00–0:30 — The problem (agent sprawl).**
Open on the **Agents** page — SaitALCorp runs **127 agents** across departments, tools, and
models, each with an owner and a risk score. Say it plainly: *"Companies are deploying
hundreds of AI agents. The problem is no longer how to build them — it's how to control
them."* Nobody owns the fleet; one over-privileged agent with a path to PII and a payment
API is a breach waiting to happen.

**0:30–1:05 — Dependency graph and blast radius.**
Open **CustomerRefundAgent → Dependencies**: the graph shows Customer DB, Salesforce,
Stripe, Refund API, Email, and the model. Blast radius flags — all deterministic —
**PII reachable, financial action reachable, production-write path, external exfiltration
path.** This is exactly the agent you cannot let run unguarded.

**1:05–1:40 — Discover the rogue and auto-quarantine.**
**Guided Demo → Discover Rogue Agent.** CustomerRefundAgent v2 is pulled into review, the
deterministic engine scores it **87/100 CRITICAL**, and policy **quarantines it
automatically**. *Run Risk Assessment* shows the breakdown and the **Gemini** explanation
(live on Vertex AI) — Gemini explains and recommends, it never decides. *(Cut to the Vertex
AI logs to show the real Gemini request.)*

**1:40–2:25 — Trigger a $650 governed refund.**
*Apply Refund Governance* reactivates the agent under policy (privileged operator). *Trigger
$650 Refund* starts an execution that immediately goes **WAITING_APPROVAL** — the Large
Refund policy requires two approvers.

**2:25–2:55 — Two-stage approval, exactly once.**
*Manager Approves* (Business) — still waiting. *Finance Approves* — the execution **resumes
and completes**, and the refund executes **exactly once** (`demo_refund_…`, never Stripe).
Idempotency guarantees no duplicate.

**2:55–3:20 — Audit and observability.**
*View Audit Trace*: the full reasoning chain — started → policy.evaluated →
waiting_approval → approval.requested/granted ×2 → resumed → tool_call.completed →
completed. Every step append-only. Show **Observability** (throughput, latency, spend,
approval wait; telemetry backend **cloud_trace**).

**3:20–3:40 — Self-evolving governance.**
Open **LeadQualificationAgent → Versions**: candidate **v17** improves performance
**71 → 82 (+15.5%)** but regresses compliance **94 → 70 (−25.5%)** → **REJECTED**:
*"Performance improvement does not justify compliance regression."* Self-evolving agents
require self-evolving governance.

**3:40–4:00 — Google Cloud architecture and close.**
Open **Integrations**: truthful status — **9 CONNECTED** (Gemini, Vertex AI, Google ADK,
Cloud Run, Firestore, Pub/Sub, Cloud Trace, Observability, Agent Runtime); the rest honestly
DEMO MODE. **Cut to the Cloud Run dashboard** (`swarmops-api` + `swarmops-web` live). Flash
the architecture diagram.

**Closing line:** *SwarmOps turns agent sprawl into a governed AI workforce.*

---

## Rules compliance shown in this cut

- **Gemini 3.5** genuinely leveraged (Vertex AI logs during the governance step).
- **Google Agent Framework** — Google ADK GovernanceAgent (constrained tools).
- **Google Cloud infra** — Cloud Run (dashboard), Firestore, Pub/Sub, Cloud Trace.
- **Autonomous action, long-running pause/resume, persistence, multi-agent fleet,
  governance, security, human approval, observability, auditability** — all on screen.
- **< 4 minutes**, recorded on the live `.run.app` deployment.
