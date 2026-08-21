"""Application service that runs the deterministic risk engine and persists results.

It assembles the engine input from the repositories, records an immutable
RiskAssessment, and syncs the agent's current risk_score to the computed value.
The engine itself (domain/risk_engine) stays pure and I/O-free.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.models import AgentVersion, RiskAssessment
from app.domain.risk_engine import RiskInput, RiskResult, assess
from app.infrastructure.container import RepositoryContainer


class AgentNotFound(Exception):
    pass


def _current_version(container: RepositoryContainer, agent_id: str, version_label: str) -> AgentVersion | None:
    for v in container.agent_versions.list_for_agent(agent_id):
        if v.version == version_label:
            return v
    return None


def _to_assessment(agent_id: str, version_id: str | None, result: RiskResult, ident: str,
                   created_at: datetime) -> RiskAssessment:
    return RiskAssessment(
        id=ident, agent_id=agent_id, agent_version_id=version_id,
        overall_score=result.total, severity=result.severity,
        pii_score=result.pii, financial_score=result.financial,
        external_tool_score=result.external_tools, privilege_score=result.production_write,
        autonomy_score=result.autonomy, prompt_score=result.prompt_security,
        data_score=result.approval_gap,  # missing-approval-gate dimension
        drivers=result.drivers, recommended_action=result.recommended_action,
        created_at=created_at,
    )


def assess_agent(container: RepositoryContainer, agent_id: str) -> RiskAssessment:
    """Compute, persist, and return a fresh risk assessment for an agent."""
    agent = container.agents.get(agent_id)
    if agent is None:
        raise AgentNotFound(agent_id)

    version = _current_version(container, agent_id, agent.current_version)
    dependencies = list(container.dependencies.list_for_agent(agent_id))
    result = assess(RiskInput(agent=agent, version=version, dependencies=dependencies))

    n = len(container.risk_assessments.list_for_agent(agent_id)) + 1
    assessment = _to_assessment(
        agent_id=agent_id,
        version_id=version.id if version else None,
        result=result,
        ident=f"risk-{agent_id}-{n:03d}",
        created_at=datetime.now(UTC),
    )
    container.risk_assessments.add(assessment)

    # Keep the agent's headline risk_score in sync with the authoritative engine.
    agent.risk_score = result.total
    container.agents.update(agent)

    return assessment


def latest_assessment(container: RepositoryContainer, agent_id: str) -> RiskAssessment | None:
    if container.agents.get(agent_id) is None:
        raise AgentNotFound(agent_id)
    return container.risk_assessments.latest_for_agent(agent_id)
