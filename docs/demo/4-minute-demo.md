# SwarmOps — 4-Minute Demo Script

Run the whole thing from the **Guided Demo** page (`/demo`) — every button calls real
backend logic. Hit **RESET DEMO** first for a deterministic starting state.

**Thesis:** Every autonomous agent should have an owner, identity, policy, risk profile,
trace, and kill switch. SwarmOps turns agent sprawl into a governed AI workforce.

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
nothing faked. Show the Cloud Run deployment (or the deploy files / architecture
diagram).

**Closing line:** *SwarmOps turns agent sprawl into a governed AI workforce.*
