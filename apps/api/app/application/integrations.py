"""Gemini Enterprise Agent Platform adapters + truthful integration status.

SwarmOps plugs into Google's enterprise agent infrastructure without recreating it.
Where a live integration is genuinely available (credentials + client + config), the
status is CONNECTED; where SwarmOps provides a local substitute, it is DEMO_MODE; where
a capability is simply off, NOT_CONFIGURED. A demo provider is **never** reported as
live — the Integrations page always tells the truth.

Adapter interfaces (ports): AgentRegistryProvider, AgentRuntimeProvider, MemoryProvider,
AgentGatewayProvider, ModelArmorProvider, ObservabilityProvider. Demo implementations
back them today; real Google integrations slot in behind the same interfaces.
"""

from __future__ import annotations

import importlib.util
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import Settings
from app.domain.enums import IntegrationStatus
from app.infrastructure.model_armor import scanner_status
from app.infrastructure.telemetry import BACKEND_CLOUD_TRACE, tracing_backend

# Governance metadata that always stays in SwarmOps, even when a Google Registry
# catalogs the agent's infrastructure identity.
SWARMOPS_GOVERNANCE_FIELDS = (
    "business_owner", "department", "risk_score", "approval_state",
    "governance_status", "policy_bindings", "cost_center", "incident_history",
)


@dataclass
class IntegrationInfo:
    key: str
    name: str
    category: str
    status: IntegrationStatus
    detail: str
    docs: str


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _has_gemini_creds(settings: Settings) -> bool:
    return bool(settings.gemini_api_key) or (
        settings.google_genai_use_vertexai and bool(settings.google_cloud_project)
    )


# --- Adapter interfaces (ports) ------------------------------------------

class IntegrationProvider(ABC):
    @abstractmethod
    def describe(self, settings: Settings) -> IntegrationInfo: ...


class AgentRegistryProvider(IntegrationProvider):
    """Publishes/versions/discovers agents. Google Registry catalogs infrastructure
    identity; SwarmOps keeps the governance metadata (owner, risk, approval, policy)."""


class AgentRuntimeProvider(IntegrationProvider):
    """Long-running, async background execution of agents."""


class MemoryProvider(IntegrationProvider):
    """Persistent, secure cross-session governance context. No unnecessary PII/secrets."""


class AgentGatewayProvider(IntegrationProvider):
    """Unified routing + policy enforcement in front of agents."""


class ModelArmorProvider(IntegrationProvider):
    """Inline guardrails (prompt injection, tool poisoning, PII)."""


class ObservabilityProvider(IntegrationProvider):
    """OpenTelemetry-compliant traces + audit."""


# --- Demo / adapter implementations --------------------------------------

class DemoAgentRegistryProvider(AgentRegistryProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        return IntegrationInfo(
            key="agent_registry", name="Agent Registry", category="Discovery & Lifecycle",
            status=IntegrationStatus.DEMO_MODE,
            detail="SwarmOps registry: agents are cataloged, versioned, and discoverable in "
                   "SwarmOps; governance metadata stays here even when a Google Registry is added.",
            docs="Wire an AgentRegistryProvider to Google's Agent Registry for infrastructure "
                 "discovery; keep SwarmOps governance metadata authoritative.",
        )


class DemoAgentRuntimeProvider(AgentRuntimeProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        on_cloud_run = bool(os.environ.get("K_SERVICE"))
        return IntegrationInfo(
            key="agent_runtime", name="Agent Runtime", category="Core Execution & State",
            status=IntegrationStatus.CONNECTED if on_cloud_run else IntegrationStatus.DEMO_MODE,
            detail="Executions run through the SwarmOps state machine"
                   + (" on Cloud Run." if on_cloud_run
                      else " in-process (deploy to Cloud Run for the managed runtime)."),
            docs="Deploy to Cloud Run (see docs/deployment/google-cloud.md) or bind a Google "
                 "Agent Runtime provider for managed long-running execution.",
        )


class DemoMemoryProvider(MemoryProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        return IntegrationInfo(
            key="memory_bank", name="Memory Bank", category="Core Execution & State",
            status=IntegrationStatus.DEMO_MODE,
            detail="Long-term governance context (assessments, proposals, audit) persists in "
                   "the SwarmOps store; no unnecessary PII or secrets are retained.",
            docs="Bind a MemoryProvider to Google's Memory Bank for cross-session context; "
                 "keep PII/secrets out of long-term memory.",
        )


class DemoAgentGatewayProvider(AgentGatewayProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        return IntegrationInfo(
            key="agent_gateway", name="Agent Gateway", category="Security & Governance",
            status=IntegrationStatus.DEMO_MODE,
            detail="The deterministic policy engine enforces routing/authorization decisions; "
                   "SwarmOps does not recreate gateway infrastructure.",
            docs="Front agents with Google's Agent Gateway for unified routing; SwarmOps policy "
                 "decisions remain the enforcement source of truth.",
        )


class ModelArmorProviderAdapter(ModelArmorProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        live = scanner_status(settings) == "LIVE"
        return IntegrationInfo(
            key="model_armor", name="Model Armor", category="Security & Governance",
            status=IntegrationStatus.CONNECTED if live else IntegrationStatus.DEMO_MODE,
            detail="Google Model Armor guardrails." if live
                   else "Local demo security scanner (prompt injection / PII / tool poisoning).",
            docs="Set MODEL_ARMOR_ENABLED=true with a GCP project + google-cloud-modelarmor to go live.",
        )


class CloudObservabilityProvider(ObservabilityProvider):
    def describe(self, settings: Settings) -> IntegrationInfo:
        connected = tracing_backend(settings) == BACKEND_CLOUD_TRACE
        return IntegrationInfo(
            key="agent_observability", name="Agent Observability", category="Telemetry",
            status=IntegrationStatus.CONNECTED if connected else IntegrationStatus.DEMO_MODE,
            detail="Trace-correlated audit trail" + (" exported to Cloud Trace." if connected
                   else " retained locally (set OTEL_ENABLED + a GCP project to export)."),
            docs="Set OTEL_ENABLED=true with a GCP project and install the [otel] extra.",
        )


_PLATFORM_PROVIDERS: list[IntegrationProvider] = [
    DemoAgentRegistryProvider(),
    DemoAgentRuntimeProvider(),
    DemoMemoryProvider(),
    DemoAgentGatewayProvider(),
    ModelArmorProviderAdapter(),
    CloudObservabilityProvider(),
]


# --- Base Google services (truthful status) ------------------------------

def _base_integrations(settings: Settings) -> list[IntegrationInfo]:
    genai = _module_available("google.genai")
    gemini_live = genai and _has_gemini_creds(settings)
    vertex_live = genai and settings.google_genai_use_vertexai and bool(settings.google_cloud_project)
    on_cloud_run = bool(os.environ.get("K_SERVICE"))
    firestore_live = settings.persistence_backend == "firestore" and _module_available("google.cloud.firestore")
    pubsub_live = settings.event_bus == "pubsub" and bool(settings.google_cloud_project) \
        and _module_available("google.cloud.pubsub")

    def info(key, name, category, status, detail, docs) -> IntegrationInfo:
        return IntegrationInfo(key=key, name=name, category=category, status=status,
                               detail=detail, docs=docs)

    return [
        info("gemini", "Gemini", "Model",
             IntegrationStatus.CONNECTED if gemini_live else IntegrationStatus.NOT_CONFIGURED,
             f"Model {settings.gemini_model}." if gemini_live
             else "No credentials; GovernanceAgent uses the local-template fallback.",
             "Set GEMINI_API_KEY, or GOOGLE_GENAI_USE_VERTEXAI=true with a project."),
        info("vertex_ai", "Vertex AI", "Model",
             IntegrationStatus.CONNECTED if vertex_live else IntegrationStatus.NOT_CONFIGURED,
             "Gemini routed through Vertex AI." if vertex_live else "Vertex AI routing is off.",
             "Set GOOGLE_GENAI_USE_VERTEXAI=true and GOOGLE_CLOUD_PROJECT."),
        info("google_adk", "Google ADK", "Framework",
             IntegrationStatus.NOT_CONFIGURED,
             "The Google GenAI SDK is the active Google Agent Framework; the ADK adapter is not wired.",
             "Install google-adk and bind the GovernanceAgent to an ADK LlmAgent to switch frameworks."),
        info("cloud_run", "Cloud Run", "Infrastructure",
             IntegrationStatus.CONNECTED if on_cloud_run else IntegrationStatus.NOT_CONFIGURED,
             "Running on Cloud Run." if on_cloud_run else "Not running on Cloud Run (local dev).",
             "Deploy with infrastructure/deploy.sh or Terraform (docs/deployment/google-cloud.md)."),
        info("pubsub", "Pub/Sub", "Infrastructure",
             IntegrationStatus.CONNECTED if pubsub_live else IntegrationStatus.DEMO_MODE,
             "Domain events published to Pub/Sub." if pubsub_live
             else "In-memory event bus (set EVENT_BUS=pubsub + a project to publish).",
             "Set EVENT_BUS=pubsub, GOOGLE_CLOUD_PROJECT, and install the [gcp] extra."),
        info("firestore", "Firestore", "Infrastructure",
             IntegrationStatus.CONNECTED if firestore_live else IntegrationStatus.DEMO_MODE,
             "State persisted in Firestore." if firestore_live else "Local SQLite persistence.",
             "Set PERSISTENCE_BACKEND=firestore and install the [gcp] extra."),
        info("cloud_trace", "Cloud Trace", "Telemetry",
             IntegrationStatus.CONNECTED if tracing_backend(settings) == BACKEND_CLOUD_TRACE
             else IntegrationStatus.DEMO_MODE,
             "Traces exported to Cloud Trace." if tracing_backend(settings) == BACKEND_CLOUD_TRACE
             else "Local trace reconstruction from the audit trail.",
             "Set OTEL_ENABLED=true with a GCP project and the [otel] extra."),
    ]


def describe_integrations(settings: Settings) -> list[IntegrationInfo]:
    """The full, truthful integration roster shown on the Integrations page."""
    platform = [p.describe(settings) for p in _PLATFORM_PROVIDERS]
    return _base_integrations(settings) + platform
