# agents/

Google agent-framework agents.

The **GovernanceAgent** is implemented in the backend package so it can import the
domain/repositories directly:

- `apps/api/app/agents/adk_governance.py` — the **Google ADK** `LlmAgent` builder that
  exposes the constrained governance toolset as ADK tools.
- `apps/api/app/agents/governance_agent.py` — the agent orchestrator (deterministic-first;
  reports its active framework — Google ADK when installed, else the Google GenAI SDK).
- `apps/api/app/infrastructure/governance_tools.py` — the constrained toolset (fixed allowlist).
- `apps/api/app/infrastructure/gemini_explainer.py` — the Gemini explanation layer
  (GenAI SDK live, with a clearly-labeled local-template fallback).

**Framework:** the agent runs on **Google ADK** (`google-adk`, in the `[ai]` extra); when
ADK is absent it falls back to the Google GenAI SDK. Either way it is a Google Agent
Framework. The agent **explains** deterministic governance decisions — it can never
override a score, severity, or action, and the ADK `set_agent_status` tool re-enforces the
deterministic rule internally. Set `GOOGLE_GENAI_USE_VERTEXAI=true` with a project (or
`GEMINI_API_KEY`) to invoke Gemini live; otherwise the local template is used.
