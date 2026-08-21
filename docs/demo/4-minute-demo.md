# SwarmOps — 4-Minute Demo Script

Run the whole thing from the **Guided Demo** page (`/demo`) — every button calls real
backend logic. Hit **RESET DEMO** first for a deterministic starting state.

**Thesis:** Every autonomous agent should have an owner, identity, policy, risk profile,
trace, and kill switch. SwarmOps turns agent sprawl into a governed AI workforce.

## Before you record (required proof)

The Official Rules require the video to **demonstrate the backend running on Google
Cloud**, and Gemini must be genuinely leveraged. Set this up first:

1. **Deploy to Cloud Run** — `PROJECT_ID=… REGION=… ./infrastructure/deploy.sh`. Record
   the demo **on the deployed `https://swarmops-web-*.run.app` URL** so the browser
   address bar is itself Google Cloud proof.
2. **Enable live Gemini** — set `GEMINI_API_KEY` (or `GOOGLE_GENAI_USE_VERTEXAI=true` +
   project). The Integrations page should then show **Google ADK / Gemini: CONNECTED**
   and the governance explanation is a real Gemini response (not the local template).
3. **Open two Google Cloud Console tabs** ready to cut to: the **Cloud Run** service
   dashboard (`swarmops-api` / `swarmops-web`) and **Vertex AI** (or the Gemini API)
   request logs.

**Google Cloud proof appears three times in the cut:** the `.run.app` address bar
throughout, the Cloud Run dashboard at the close, and the Vertex AI / Gemini logs when
the governance explanation runs.

---

**0:00–0:25 — The problem (agent sprawl).**
Open **Overview**: AcmeCorp runs **127 agents · 43 active · 9 high-risk · 3 quarantined**.
Companies are wiring up autonomous agents that can move money and touch customer data
with none of the controls they demand of human employees.

**0:25–1:00 — Discover a rogue agent and quarantine it.**
Guided Demo → *Discover Rogue Agent*: CustomerRefundAgent v2 is pulled into review, the
deterministic engine scores it **87/100 CRITICAL**, and policy **quarantines** it
automatically. *Review Quarantine* shows the reason. Note the Gemini explanation — it
explains, it never decides.

*(As the risk assessment runs, briefly cut to the **Vertex AI / Gemini logs** tab to show
a real Gemini request — proof the model is genuinely leveraged.)*

**1:00–1:35 — Dependency graph and blast radius.**
Open the agent's **Dependencies** tab: the graph shows Customer DB, Salesforce, Stripe,
Refund API, Email, and the model. Blast radius flags **PII reachable, financial action
reachable, production-write path, external exfiltration path** — all deterministic.

**1:35–2:20 — Trigger a $650 governed refund.**
Guided Demo → *Apply Refund Governance* reactivates the agent under policy. *Trigger
$650 Refund* starts an execution that immediately goes **WAITING_APPROVAL** — the
Large Refund policy requires two approvers.

**2:20–2:50 — Two-stage approval and execution.**
*Manager Approves* (Business) — still waiting. *Finance Approves* — the execution
**resumes and completes**, and the refund executes **exactly once** (`demo_refund_…`,
never Stripe). Idempotency guarantees no duplicate.

**2:50–3:20 — Audit / observability trace.**
*View Audit Trace* (or Observability → the trace): the full reasoning chain —
execution.started → policy.evaluated → waiting_approval → approval.requested/granted ×2
→ resumed → tool_call.completed → execution.completed. Every step append-only.

**3:20–3:45 — Self-evolving governance.**
Open **LeadQualificationAgent → Versions**: candidate **v17** improves performance
**71 → 82 (+15.5%)** but regresses compliance **94 → 70 (−25.5%)** → **REJECTED**:
*"Performance improvement does not justify compliance regression."* Self-evolving agents
require self-evolving governance.

**3:45–4:00 — Google Cloud architecture and close.**
Open **Integrations**: truthful status for Gemini, Vertex AI, ADK, Agent Registry /
Runtime / Memory / Gateway, Model Armor, Cloud Run, Pub/Sub, Firestore, Cloud Trace —
nothing faked. **Cut to the Cloud Run dashboard** showing `swarmops-api` + `swarmops-web`
live (URLs, revisions, region) — the required proof the backend runs on Google Cloud.
Flash the architecture diagram.

**Closing line:** *SwarmOps turns agent sprawl into a governed AI workforce.*

---

## Rules compliance shown in this cut

- **Gemini 3.5** genuinely leveraged (Vertex AI / Gemini logs during the governance step).
- **Google Agent Framework** — Google ADK GovernanceAgent (constrained tools).
- **Google Cloud infra** — Cloud Run (dashboard), Firestore, Pub/Sub, Cloud Trace.
- **Autonomous action, long-running pause/resume, persistence, multi-agent fleet,
  governance, security, human approval, observability, auditability** — all on screen.
- **< 4 minutes**, recorded on the live `.run.app` deployment.
