"""GovernanceAgent — the first AI agent in SwarmOps.

It inspects a discovered agent, runs the deterministic risk engine, retrieves the
applicable policies, and asks Gemini (via the Google GenAI SDK) to explain the risk
and recommend remediation. The decision itself is always deterministic: the model's
output is prose only and can never change a score, severity, or action.

Framework note: this uses the Google GenAI SDK (an accepted Google Agent Framework)
with a strictly constrained toolset (see ``GovernanceToolset``). Set
``GOOGLE_GENAI_USE_VERTEXAI=true`` with a project to route through Vertex AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.audit_service import record_event
from app.application.risk_service import assess_agent
from app.config import Settings
from app.domain.models import RiskAssessment
from app.domain.policy_engine import PolicyDecision, evaluate_policies
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.gemini_explainer import (
    GovernanceExplainer,
    GovernanceExplanation,
    get_explainer,
)
from app.infrastructure.governance_tools import GovernanceToolset

INSTRUCTION = (
    "You are the SwarmOps GovernanceAgent. You may only use the provided tools. "
    "A deterministic engine decides risk and policy outcomes; you explain them and "
    "recommend remediation. You must never claim authority to override a DENY or "
    "QUARANTINE decision."
)


class GovernanceAgentError(Exception):
    pass


@dataclass(frozen=True)
class GovernanceAnalysis:
    assessment: RiskAssessment          # deterministic, authoritative
    policy: PolicyDecision              # deterministic, authoritative
    explanation: GovernanceExplanation  # AI prose (or local template)


class GovernanceAgent:
    name = "GovernanceAgent"
    instruction = INSTRUCTION

    def __init__(
        self,
        container: RepositoryContainer,
        settings: Settings,
        explainer: GovernanceExplainer | None = None,
    ) -> None:
        self._c = container
        self._settings = settings
        self.tools = GovernanceToolset(container)
        # The explainer is the only LLM touch-point; injectable for tests.
        self._explainer = explainer or get_explainer(settings)

    def tool_names(self) -> frozenset[str]:
        return self.tools.tool_names()

    @property
    def framework(self) -> str:
        """The active Google Agent Framework: ADK when installed, else the GenAI SDK."""
        from app.agents.adk_governance import adk_available

        return "Google ADK" if adk_available() else "Google GenAI SDK"

    def adk_agent(self) -> object:
        """Build the real ADK LlmAgent for this GovernanceAgent (requires google-adk)."""
        from app.agents.adk_governance import build_adk_agent

        return build_adk_agent(self._c, self._settings)

    def analyze(self, agent_id: str, action_context: dict[str, Any] | None = None) -> GovernanceAnalysis:
        agent = self._c.agents.get(agent_id)
        if agent is None:
            raise GovernanceAgentError(agent_id)

        # Deterministic + authoritative: assess (persist) and evaluate policy.
        assessment = assess_agent(self._c, agent_id)
        context = self.tools._governance_context(agent_id, assessment.overall_score)
        if action_context:
            context.update(action_context)
        decision = evaluate_policies(list(self._c.policies.list()), context)

        # AI layer: explanation only. Its output never feeds back into the decision.
        facts = {
            "agent_name": agent.name,
            "score": assessment.overall_score,
            "severity": assessment.severity.value,
            "drivers": assessment.drivers,
            "recommended_action": assessment.recommended_action.value,
            "policy_action": decision.action.value,
            "policy_name": decision.policy_name,
        }
        explanation = self._explainer.explain(facts)

        record_event(
            self._c, action="governance.analysis", resource_type="agent", resource_id=agent_id,
            decision=decision.action.value,
            reason=f"score {assessment.overall_score}; explained by {explanation.model_status}",
            metadata={"model_status": explanation.model_status, "model": explanation.model_name},
        )
        return GovernanceAnalysis(assessment=assessment, policy=decision, explanation=explanation)
