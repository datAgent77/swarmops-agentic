# SwarmOps — Threat Model

SwarmOps governs an autonomous agent fleet. Its security posture rests on one
invariant: **deterministic governance decides; no LLM is in the authorization path.**
The threats below are what an agent control plane must withstand, and how SwarmOps
mitigates each. This is a demonstration model, not a production security certification.

| # | Threat | Mitigation in SwarmOps |
|---|--------|------------------------|
| 1 | **Prompt injection** — malicious input hijacks an agent | Deterministic security scanner (P10) blocks known patterns; a `SecurityIncident` + audit event are recorded. The GovernanceAgent's LLM output is prose only and cannot change a decision. |
| 2 | **Tool poisoning** — coercing an agent to add tools / escalate | Constrained toolset (P07): the GovernanceAgent may only call a fixed allowlist; `set_agent_status` re-checks the deterministic rule and refuses model-driven overrides. Scanner flags escalation patterns. |
| 3 | **Excessive permissions** — over-privileged agents | Deterministic risk engine (P02) scores PII/financial/production-write/autonomy; blast-radius analysis (P08) surfaces reachable danger. High-risk + no-gate agents are quarantined by policy (P03/P06). |
| 4 | **PII leakage** — bulk export of customer data | Scanner detects PII-export patterns; the PII Export policy DENYs external data export containing PII; incidents + audit recorded. Memory Bank stores no unnecessary PII. |
| 5 | **Rogue agent deployment** — an unreviewed agent appears | Discovery lifecycle (P06): DISCOVERED → risk → policy → QUARANTINED. Quarantined agents cannot execute (409). |
| 6 | **Compromised MCP / dependency** | Dependency graph + blast radius (P08) map every tool/MCP/DB an agent can reach and highlight dangerous paths; external transmission is flagged by the scanner. |
| 7 | **Duplicate financial actions** — double refunds | Idempotency (P04): a state-changing tool call with a seen key is replayed, never re-executed. Verified by the E2E test (refund executes exactly once). |
| 8 | **Unauthorized agent-to-agent calls** | Deterministic policy engine gates actions; the Agent Gateway seam (P13) centralizes routing/enforcement. Delegation edges are modeled in the graph. |
| 9 | **Audit tampering** | Append-only audit events (P09, ADR-006); every decision/approval/tool call is recorded and trace-correlated. Backend is the source of truth. |
| 10 | **Credential exposure** | No secrets in the repo; secrets live in Secret Manager (P12). Config via env; `.env` is gitignored; least-privilege service account + IAM. |

## Human-in-the-loop as a control

High-risk actions (large refunds) require sequential human approval with **backend-
enforced roles** (P05): the persona must actually hold the required role, a rejection
terminally blocks the workflow, and double approval is idempotent. The UI role switcher
is never the source of truth.

## Residual risk / scope

- The security scanner is a demo pattern set, not comprehensive DLP/WAF.
- Live Model Armor, Registry, Gateway, and Memory integrations are seams (P13), not yet
  bound to production Google services in this build.
- Authn/authz for the console itself is out of scope for the demo.
