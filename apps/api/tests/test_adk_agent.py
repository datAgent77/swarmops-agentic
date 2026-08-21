"""Google ADK GovernanceAgent — real LlmAgent with the constrained tools.

Skipped when the optional google-adk package is not installed."""

from __future__ import annotations

import importlib.util

import pytest

from app.agents.governance_agent import GovernanceAgent
from app.config import get_settings
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.governance_tools import ALLOWED_TOOLS


def _adk_installed() -> bool:
    try:
        return importlib.util.find_spec("google.adk") is not None
    except ModuleNotFoundError:
        return False


pytestmark = pytest.mark.skipif(not _adk_installed(), reason="google-adk ([ai] extra) not installed")


def test_governance_agent_reports_adk_framework(container: RepositoryContainer) -> None:
    agent = GovernanceAgent(container, get_settings())
    assert agent.framework == "Google ADK"


def test_adk_agent_exposes_only_constrained_tools(container: RepositoryContainer) -> None:
    agent = GovernanceAgent(container, get_settings())
    adk = agent.adk_agent()
    assert type(adk).__name__ == "LlmAgent"
    assert adk.name == "GovernanceAgent"
    tool_names = {getattr(t, "__name__", getattr(t, "name", "")) for t in adk.tools}
    assert tool_names == set(ALLOWED_TOOLS)


def test_deterministic_decision_still_authoritative(container: RepositoryContainer) -> None:
    # The ADK/Gemini layer never changes the deterministic outcome.
    agent = GovernanceAgent(container, get_settings())
    result = agent.analyze("agent-customer-refund")
    assert result.assessment.overall_score == 87
    assert result.policy.action.value == "QUARANTINE"
