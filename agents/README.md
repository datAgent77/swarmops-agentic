# agents/

Google agent-framework agents.

The **GovernanceAgent** (P07) is implemented in the backend package so it can import
the domain/repositories directly:

- `apps/api/app/agents/governance_agent.py` — the agent (Gemini via the Google GenAI SDK)
- `apps/api/app/infrastructure/governance_tools.py` — its constrained toolset (allowlist)
- `apps/api/app/infrastructure/gemini_explainer.py` — live/fallback explanation layer

The agent explains deterministic governance decisions; it can never override a score,
severity, or action. Set `GOOGLE_GENAI_USE_VERTEXAI=true` with a project (or
`GEMINI_API_KEY`) to enable live Gemini; otherwise it uses a clearly-labeled local template.
