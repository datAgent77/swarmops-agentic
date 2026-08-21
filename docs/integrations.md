# Google Integrations — what is live vs simulated

SwarmOps plugs into Google's enterprise agent infrastructure behind clean adapter
interfaces. The **Integrations** page (and `GET /api/v1/integrations/status`) always
reports the truth: a demo provider is never shown as connected.

## Status meanings

| Status | Meaning |
|--------|---------|
| `CONNECTED` | A genuine live Google integration is active. |
| `DEMO_MODE` | SwarmOps provides a working local substitute for the capability. |
| `NOT_CONFIGURED` | The capability is off (no substitute is running as "connected"). |
| `ERROR` | The integration was configured but failed. |

## Roster

| Integration | Default (local) | How to make it live |
|-------------|-----------------|---------------------|
| **Gemini** | NOT_CONFIGURED (local-template fallback) | `GEMINI_API_KEY`, or `GOOGLE_GENAI_USE_VERTEXAI=true` + project |
| **Vertex AI** | NOT_CONFIGURED | `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT` |
| **Google ADK** | NOT_CONFIGURED | The **GenAI SDK** is the active Google Agent Framework; install `google-adk` and bind an ADK `LlmAgent` to switch |
| **Agent Registry** | DEMO_MODE | Bind `AgentRegistryProvider` to Google's Registry for infra discovery; governance metadata stays in SwarmOps |
| **Agent Runtime** | DEMO_MODE / CONNECTED on Cloud Run | Deploy to Cloud Run, or bind a Google Agent Runtime provider |
| **Memory Bank** | DEMO_MODE | Bind `MemoryProvider` to Google's Memory Bank (no PII/secrets in long-term memory) |
| **Agent Gateway** | DEMO_MODE | Front agents with Google's Agent Gateway; SwarmOps policy stays the enforcement source of truth |
| **Model Armor** | DEMO_MODE (local scanner) | `MODEL_ARMOR_ENABLED=true` + project + `google-cloud-modelarmor` |
| **Cloud Run** | NOT_CONFIGURED (local dev) | Deploy via `infrastructure/deploy.sh` / Terraform (detected by `K_SERVICE`) |
| **Pub/Sub** | DEMO_MODE (in-memory bus) | `EVENT_BUS=pubsub` + project + `[gcp]` extra |
| **Firestore** | DEMO_MODE (local SQLite) | `PERSISTENCE_BACKEND=firestore` + `[gcp]` extra |
| **Cloud Trace / Observability** | DEMO_MODE (local trace) | `OTEL_ENABLED=true` + project + `[otel]` extra |

## Governance metadata always stays in SwarmOps

Even when a Google Registry catalogs an agent's infrastructure identity, these fields
remain authoritative in SwarmOps: business owner, department, risk score, approval
state, governance status, policy bindings, cost center, incident history.

## Adapter interfaces

`AgentRegistryProvider`, `AgentRuntimeProvider`, `MemoryProvider`,
`AgentGatewayProvider`, `ModelArmorProvider`, `ObservabilityProvider` — see
`apps/api/app/application/integrations.py`. Demo implementations back them today; real
Google integrations slot in behind the same interfaces without changing callers.
