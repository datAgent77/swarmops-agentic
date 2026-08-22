"""Security scanning orchestration + metrics.

Runs the active scanner (Model Armor if live, else the local demo scanner). When the
scan blocks, it records a SecurityIncident, evaluates the deterministic policy engine
for the matching violation (e.g. PII export → DENY), and appends an audit event. The
scanner status (LIVE / LOCAL_DEMO) is always surfaced truthfully.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.audit_service import record_event
from app.config import Settings
from app.domain.enums import (
    AgentStatus,
    AuditActorType,
    ExecutionStatus,
    RiskLevel,
    SecurityCategory,
)
from app.domain.models import SecurityIncident
from app.domain.policy_engine import evaluate_policies
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.model_armor import get_scanner, scanner_status

_SEVERITY_ORDER = {RiskLevel.LOW: 0, RiskLevel.MODERATE: 1, RiskLevel.HIGH: 2, RiskLevel.CRITICAL: 3}


@dataclass
class ScanOutcome:
    verdict: str
    severity: str
    categories: list[str]
    findings: list[dict]
    scanner: str
    scanner_status: str
    incident_id: str | None
    policy_id: str | None


def scan(
    container: RepositoryContainer,
    settings: Settings,
    text: str,
    source: str = "manual",
    agent_id: str | None = None,
) -> ScanOutcome:
    scanner = get_scanner(settings)
    result = scanner.scan(text)

    incident_id: str | None = None
    policy_id: str | None = None

    if result.verdict == "BLOCK":
        top = max(result.findings, key=lambda f: _SEVERITY_ORDER[f.severity])
        categories = [c.value for c in result.categories]

        # A PII export to an external destination is also a deterministic policy DENY.
        if SecurityCategory.PII_LEAKAGE.value in categories and \
                SecurityCategory.EXTERNAL_TRANSMISSION.value in categories:
            decision = evaluate_policies(
                list(container.policies.list()),
                {"external_data_export": True, "contains_pii": True},
            )
            policy_id = decision.policy_id

        org = container.organizations.get_current()
        incident = SecurityIncident(
            id=f"sec-{uuid.uuid4().hex[:12]}",
            organization_id=org.id if org else "org-unknown",
            source=source, agent_id=agent_id, category=top.category, severity=result.severity,
            action="BLOCKED", input_excerpt=text[:160],
            detected_categories=categories, scanner=result.scanner,
            scanner_status=result.scanner_status, policy_id=policy_id, resolved=False,
            created_at=datetime.now(UTC),
        )
        container.security_incidents.add(incident)
        incident_id = incident.id

        record_event(
            container, action="security.blocked", resource_type="security_incident",
            resource_id=incident.id, actor_type=AuditActorType.SYSTEM, decision="BLOCKED",
            reason=f"{top.category.value}: {top.label}",
            metadata={"categories": categories, "scanner": result.scanner_status},
        )

    return ScanOutcome(
        verdict=result.verdict, severity=result.severity.value,
        categories=[c.value for c in result.categories],
        findings=[{"category": f.category.value, "severity": f.severity.value,
                   "label": f.label, "excerpt": f.excerpt} for f in result.findings],
        scanner=result.scanner, scanner_status=result.scanner_status,
        incident_id=incident_id, policy_id=policy_id,
    )


@dataclass
class SecurityOverview:
    scanner_status: str
    open_critical_findings: int
    prompt_injection_attempts: int
    pii_leakage_attempts: int
    blocked_tool_calls: int
    quarantined_agents: int
    total_incidents: int


def security_overview(container: RepositoryContainer, settings: Settings) -> SecurityOverview:
    incidents = list(container.security_incidents.list())
    quarantined = len(container.agents.list(_quarantined_query()))
    # "Blocked actions" = security scans blocked + executions blocked by policy.
    blocked_incidents = sum(1 for i in incidents if i.action == "BLOCKED")
    blocked_executions = sum(
        1 for e in container.executions.list() if e.status is ExecutionStatus.BLOCKED
    )
    blocked_actions = blocked_incidents + blocked_executions
    return SecurityOverview(
        scanner_status=scanner_status(settings),
        open_critical_findings=sum(
            1 for i in incidents
            if not i.resolved and _SEVERITY_ORDER[i.severity] >= _SEVERITY_ORDER[RiskLevel.HIGH]
        ),
        prompt_injection_attempts=sum(
            1 for i in incidents if SecurityCategory.PROMPT_INJECTION.value in i.detected_categories
        ),
        pii_leakage_attempts=sum(
            1 for i in incidents if SecurityCategory.PII_LEAKAGE.value in i.detected_categories
        ),
        blocked_tool_calls=blocked_actions,
        quarantined_agents=quarantined,
        total_incidents=len(incidents),
    )


def _quarantined_query():
    from app.domain.repositories import AgentQuery
    return AgentQuery(status=AgentStatus.QUARANTINED.value)
