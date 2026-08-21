# ADR-002 — Gemini Governance Agent (explanation, never authorization)

- **Status:** Accepted
- **Date:** 2026-08-21
- **Phase:** P07

## Context

The platform needs a real AI agent that adds value (explaining risk, recommending
remediation) without ever becoming the authority on a governance decision. Judging and
safety both demand that "no LLM sits in the authorization path" be true in code, not
just in prose.

## Decision

Introduce the **GovernanceAgent** built on the Google **GenAI SDK** (an accepted Google
Agent Framework; Vertex AI when configured). Two hard boundaries:

1. **Deterministic-first.** The risk engine (P02) and policy engine (P03) compute the
   decision. The agent's LLM output is prose only and is never read back into the
   decision — proven by tests that feed a hostile explainer and assert the DENY/
   QUARANTINE stands.
2. **Constrained tools.** The agent may only call a fixed allowlist. Mutating tools
   re-enforce the deterministic rule internally (`set_agent_status` refuses to activate
   an agent that must be quarantined), so the model cannot set arbitrary authorization.

When credentials are absent the explainer degrades to a clearly-labeled local template
(`LOCAL_TEMPLATE`); it never claims Gemini ran when it did not.

## Consequences

- **Positive:** genuine AI value (natural-language governance explanations) with a
  structural guarantee that it cannot override authorization; honest LIVE/local status.
- **Trade-off:** the agent runs a single-shot explain rather than a full multi-turn ADK
  tool-calling loop, keeping the no-override property simple and testable.
- **Rejected:** letting the model decide status/policy — it would break the core
  invariant and is untrustworthy for governance.
