# Execution Sequence — governed $650 refund

The end-to-end sequence for the flagship demo: a $650 refund that pauses for two-stage
human approval and resumes to execute **exactly once**. Every step appends a
trace-correlated audit event.

```mermaid
sequenceDiagram
    actor Op as Operator / UI
    participant API as FastAPI
    participant EX as Execution Service
    participant SM as State Machine
    participant POL as Policy Engine (deterministic)
    participant AP as Approval Service
    participant TL as Safe Tool Layer (mock)
    participant AUD as Audit + Events

    Op->>API: POST /executions (refund $650)
    API->>EX: start_execution
    EX->>SM: QUEUED → RUNNING
    EX->>AUD: execution.started
    EX->>POL: evaluate(refund=650)
    POL-->>EX: REQUIRE_APPROVAL [BUSINESS, FINANCE]
    EX->>AP: open approvals (2)
    EX->>SM: RUNNING → WAITING_APPROVAL
    EX->>AUD: policy.evaluated, approval.requested×2, waiting_approval
    API-->>Op: 201 WAITING_APPROVAL

    Op->>API: approve (Manager, BUSINESS_APPROVER)
    API->>AP: approve
    AP->>AP: role check OK; 1 of 2 granted
    AP->>AUD: approval.granted
    Note over AP: still WAITING_APPROVAL

    Op->>API: approve (Finance, FINANCE_APPROVER)
    API->>AP: approve
    AP->>AP: all granted → resume
    AP->>EX: resume_execution (guarded: exactly once)
    EX->>SM: WAITING_APPROVAL → RUNNING
    EX->>TL: execute_refund (idempotency key)
    TL-->>EX: demo_refund_… (no Stripe, ever)
    EX->>SM: RUNNING → COMPLETED
    EX->>AUD: resumed, tool_call.completed, execution.completed
    API-->>Op: COMPLETED

    Op->>API: GET /observability/traces/{trace_id}
    API-->>Op: full reasoning chain
```

## Invariants enforced

- **No LLM in the path** — the policy decision is deterministic; Gemini only explains.
- **Exactly once** — `resume_execution` is guarded on `WAITING_APPROVAL`, and the tool
  layer replays on a seen idempotency key. A second approve is a no-op.
- **Role authority** — the backend validates the persona's role; the UI is not the
  source of truth.
- **Auditable** — every transition is an append-only, trace-correlated event.
