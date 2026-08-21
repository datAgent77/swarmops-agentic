"""Google ADK wrapping of the GovernanceAgent.

Builds a real ``google.adk.agents.LlmAgent`` named ``GovernanceAgent`` that exposes the
constrained governance toolset as ADK tools. The deterministic risk/policy engines stay
authoritative — the ADK/Gemini layer explains and recommends, it never decides. The ADK
tool ``set_agent_status`` re-enforces the deterministic rule internally.

``google-adk`` is an optional ``[ai]`` dependency and is imported lazily, so the base
install and test suite never require it.
"""

from __future__ import annotations

import importlib.util
from typing import Any

from app.config import Settings
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.governance_tools import GovernanceToolset

INSTRUCTION = (
    "You are the SwarmOps GovernanceAgent running on Google ADK. You may only use the "
    "provided tools. A deterministic engine decides risk and policy outcomes; you explain "
    "them and recommend remediation. You must never claim authority to override a DENY or "
    "QUARANTINE decision."
)


def adk_available() -> bool:
    try:
        return importlib.util.find_spec("google.adk") is not None
    except ModuleNotFoundError:
        return False


def build_adk_agent(container: RepositoryContainer, settings: Settings) -> Any:
    """Construct the ADK LlmAgent with the constrained governance tools.

    Raises ModuleNotFoundError if google-adk is not installed (callers guard with
    ``adk_available()``).
    """
    from google.adk.agents import LlmAgent

    tools = GovernanceToolset(container)
    return LlmAgent(
        name="GovernanceAgent",
        model=settings.gemini_model,
        description="Explains deterministic governance decisions; never overrides them.",
        instruction=INSTRUCTION,
        tools=[
            tools.get_agent_metadata,
            tools.get_agent_dependencies,
            tools.calculate_risk,
            tools.get_applicable_policies,
            tools.create_risk_assessment,
            tools.create_approval_request,
            tools.record_audit_event,
            tools.set_agent_status,
        ],
    )
