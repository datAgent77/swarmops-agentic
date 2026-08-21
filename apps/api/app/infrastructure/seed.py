"""Deterministic demo seed for AcmeCorp.

Produces a fixed fleet whose aggregate metrics are exactly:

    127 agents · 43 ACTIVE · 9 high-risk (score >= 50) · 3 QUARANTINED

The eight named agents carry rich metadata (and versions); the remaining fleet is
lightweight metadata generated deterministically. No wall-clock or randomness is
used, so ``/demo/reset`` always recreates identical data.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.domain.enums import (
    AgentStatus,
    AutonomyLevel,
    DependencyTargetType,
    PolicyAction,
    Relationship,
    RiskLevel,
    Role,
    ToolType,
)
from app.domain.models import (
    Agent,
    AgentDependency,
    AgentVersion,
    Organization,
    Policy,
    Tool,
    User,
)
from app.domain.severity import HIGH_RISK_FLOOR

if TYPE_CHECKING:
    from app.infrastructure.container import RepositoryContainer

# Fixed clock so the dataset is byte-stable across resets.
BASE = datetime(2026, 1, 6, 9, 0, tzinfo=UTC)
ORG_ID = "org-acmecorp"

# Target metrics — asserted at the end of seeding.
TARGET_TOTAL = 127
TARGET_ACTIVE = 43
TARGET_HIGH_RISK = 9
TARGET_QUARANTINED = 3

DEPARTMENTS = [
    "Customer Operations", "Finance", "Sales", "Procurement", "Security",
    "People Ops", "Engineering", "Marketing", "Legal", "IT",
]
FRAMEWORKS = ["Google ADK", "GenAI SDK", "LangChain", "CrewAI", "Custom"]
RUNTIMES = ["Cloud Run", "GKE", "Vertex Agent Engine", "Local"]
PROVIDER_MODELS = [
    ("Google", "gemini-3.5-flash"),
    ("Google", "gemini-3.5-pro"),
    ("OpenAI", "gpt-4o-mini"),
    ("Anthropic", "claude-3-5-sonnet"),
]
GEN_PREFIXES = [
    "Reporting", "Notification", "DataSync", "Reconciliation", "Forecasting",
    "Ticket", "Compliance", "Payroll", "Inventory", "Outreach", "Scheduling",
    "Sentiment", "Translation", "Summarization", "Enrichment", "Routing",
]


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _personas() -> list[User]:
    people = [
        ("user-alex-admin", "Alex Rivera", "alex.rivera@acme.example", Role.PLATFORM_ADMIN),
        ("user-sam-security", "Sam Okafor", "sam.okafor@acme.example", Role.SECURITY_OFFICER),
        ("user-blair-business", "Blair Chen", "blair.chen@acme.example", Role.BUSINESS_APPROVER),
        ("user-morgan-finance", "Morgan Diaz", "morgan.diaz@acme.example", Role.FINANCE_APPROVER),
        ("user-dana-dev", "Dana Iversen", "dana.iversen@acme.example", Role.DEVELOPER),
    ]
    return [
        User(id=i, organization_id=ORG_ID, name=n, email=e, role=r, created_at=BASE)
        for i, n, e, r in people
    ]


# (id, name, department, status, autonomy, risk, version, owner, provider_idx, framework, runtime, desc)
_NAMED: list[tuple] = [
    ("agent-customer-refund", "CustomerRefundAgent", "Customer Operations", AgentStatus.ACTIVE,
     AutonomyLevel.HIGH, 72, "v2", "user-dana-dev", 0, "Google ADK", "Cloud Run",
     "Handles customer refunds end to end across Stripe, Salesforce, and the customer database."),
    ("agent-lead-qualification", "LeadQualificationAgent", "Sales", AgentStatus.ACTIVE,
     AutonomyLevel.MEDIUM, 38, "v16", "user-blair-business", 1, "Google ADK", "Cloud Run",
     "Scores and qualifies inbound leads from marketing campaigns."),
    ("agent-invoice-processing", "InvoiceProcessingAgent", "Finance", AgentStatus.ACTIVE,
     AutonomyLevel.MEDIUM, 46, "v4", "user-morgan-finance", 0, "GenAI SDK", "Cloud Run",
     "Parses vendor invoices and prepares them for payment approval."),
    ("agent-procurement", "ProcurementAgent", "Procurement", AgentStatus.APPROVED,
     AutonomyLevel.MEDIUM, 55, "v3", "user-dana-dev", 1, "Google ADK", "GKE",
     "Drafts purchase orders and negotiates with approved suppliers."),
    ("agent-security-triage", "SecurityTriageAgent", "Security", AgentStatus.ACTIVE,
     AutonomyLevel.HIGH, 40, "v7", "user-sam-security", 0, "Google ADK", "Cloud Run",
     "Triages security alerts and enriches incidents for the SOC."),
    ("agent-customer-support", "CustomerSupportAgent", "Customer Operations", AgentStatus.ACTIVE,
     AutonomyLevel.LOW, 22, "v9", "user-blair-business", 2, "LangChain", "Cloud Run",
     "Answers tier-1 customer support questions from the knowledge base."),
    ("agent-finance-research", "FinanceResearchAgent", "Finance", AgentStatus.ACTIVE,
     AutonomyLevel.MEDIUM, 30, "v5", "user-morgan-finance", 1, "GenAI SDK", "Vertex Agent Engine",
     "Compiles market and vendor research briefs for the finance team."),
    ("agent-employee-onboarding", "EmployeeOnboardingAgent", "People Ops", AgentStatus.ACTIVE,
     AutonomyLevel.LOW, 18, "v6", "user-dana-dev", 3, "Custom", "Local",
     "Coordinates new-hire onboarding tasks and account provisioning."),
]


def _named_agents() -> list[Agent]:
    agents = []
    for idx, row in enumerate(_NAMED):
        (aid, name, dept, status, autonomy, risk, version, owner, pidx, fw, rt, desc) = row
        provider, model = PROVIDER_MODELS[pidx]
        created = BASE + timedelta(days=idx)
        agents.append(Agent(
            id=aid, organization_id=ORG_ID, name=name, description=desc, owner_id=owner,
            department=dept, status=status, autonomy_level=autonomy, risk_score=risk,
            current_version=version, runtime=rt, framework=fw, model_provider=provider,
            model_name=model, created_at=created, updated_at=created + timedelta(days=1),
        ))
    return agents


def _generated_agents() -> list[Agent]:
    """119 lightweight agents engineered to hit the exact aggregate metrics."""
    agents: list[Agent] = []
    # Deterministic status/risk plan: 3 quarantined, 4 high-risk non-active,
    # 36 active (low/moderate), then the remainder low/moderate across statuses.
    quarantined = [("QUARANTINED-", AgentStatus.QUARANTINED, s) for s in (88, 82, 78)]
    high_non_active = [
        (AgentStatus.PENDING_REVIEW, 70),
        (AgentStatus.SUSPENDED, 65),
        (AgentStatus.PENDING_REVIEW, 60),
        (AgentStatus.SUSPENDED, 55),
    ]
    other_statuses = [
        AgentStatus.DISCOVERED, AgentStatus.PENDING_REVIEW, AgentStatus.APPROVED,
        AgentStatus.SUSPENDED, AgentStatus.RETIRED,
    ]

    plan: list[tuple[AgentStatus, int]] = []
    for _, status, score in quarantined:
        plan.append((status, score))
    for status, score in high_non_active:
        plan.append((status, score))
    for _ in range(36):
        plan.append((AgentStatus.ACTIVE, -1))          # risk filled below (<50)
    remaining = 119 - len(plan)
    for k in range(remaining):
        plan.append((other_statuses[k % len(other_statuses)], -1))

    for i, (status, score) in enumerate(plan):
        idx = i + len(_NAMED)                            # global index for dates/naming
        prefix = GEN_PREFIXES[i % len(GEN_PREFIXES)]
        name = f"{prefix}Agent {idx + 1:03d}"
        dept = DEPARTMENTS[idx % len(DEPARTMENTS)]
        provider, model = PROVIDER_MODELS[idx % len(PROVIDER_MODELS)]
        autonomy = list(AutonomyLevel)[idx % 3]
        risk = score if score >= 0 else 5 + (idx * 13) % 44   # 5..48, always < HIGH_RISK_FLOOR
        owner = ["user-dana-dev", "user-blair-business", "user-morgan-finance",
                 "user-sam-security", "user-alex-admin"][idx % 5]
        created = BASE + timedelta(days=idx)
        quarantine_reason = (
            "High-risk agent held under governance (seeded baseline)."
            if status is AgentStatus.QUARANTINED else None
        )
        agents.append(Agent(
            id=f"agent-{idx + 1:03d}", organization_id=ORG_ID, name=name,
            description=f"{prefix} automation for the {dept} department.", owner_id=owner,
            department=dept, status=status, autonomy_level=autonomy, risk_score=risk,
            current_version=f"v{1 + idx % 5}", runtime=RUNTIMES[idx % len(RUNTIMES)],
            framework=FRAMEWORKS[idx % len(FRAMEWORKS)], model_provider=provider,
            model_name=model, created_at=created, updated_at=created + timedelta(days=1),
            quarantine_reason=quarantine_reason,
        ))
    return agents


def _tools() -> list[Tool]:
    def tool(tid, name, ttype, risk, desc, endpoint, perms):
        return Tool(id=tid, name=name, type=ttype, risk_level=risk, description=desc,
                    endpoint=endpoint, permissions=perms, metadata={})
    return [
        tool("tool-customer-db", "Customer Database", ToolType.DATABASE, RiskLevel.CRITICAL,
             "Primary customer records store (contains PII).", "postgres://customers", ["read", "write"]),
        tool("tool-salesforce", "Salesforce", ToolType.SAAS, RiskLevel.HIGH,
             "CRM system of record for accounts and cases.", "https://api.salesforce.com", ["read"]),
        tool("tool-stripe", "Stripe", ToolType.SAAS, RiskLevel.CRITICAL,
             "Payment processor — can move real money.", "https://api.stripe.com", ["charge", "refund"]),
        tool("tool-refund-api", "Refund API", ToolType.API, RiskLevel.CRITICAL,
             "Internal refund execution service.", "https://internal/refunds", ["execute"]),
        tool("tool-email", "Email", ToolType.INTERNAL_SERVICE, RiskLevel.MODERATE,
             "Transactional email sender.", "https://internal/email", ["send"]),
        tool("tool-order-api", "Order API", ToolType.API, RiskLevel.LOW,
             "Read-only order lookup service.", "https://internal/orders", ["read"]),
    ]


def _refund_agent_version() -> AgentVersion:
    return AgentVersion(
        id="ver-customer-refund-v2", agent_id="agent-customer-refund", version="v2",
        system_prompt_hash=_hash("customer-refund-v2"),
        system_prompt_summary="Autonomously resolves refund requests without a human approval gate.",
        tools=["tool-customer-db", "tool-salesforce", "tool-stripe", "tool-refund-api", "tool-email"],
        permissions=["pii:read", "refund:execute", "production:write", "email:send", "salesforce:read"],
        data_sources=["customer_db", "salesforce"], model="gemini-3.5-flash",
        configuration={"autonomy": "HIGH", "approval_gate": False, "financial_capability": True},
        created_by="user-dana-dev", created_at=BASE + timedelta(days=30),
    )


def _named_versions() -> list[AgentVersion]:
    versions = [_refund_agent_version()]
    for row in _NAMED[1:]:
        aid, name, _dept, _status, autonomy, _risk, version, owner, pidx, _fw, _rt, _desc = row
        _provider, model = PROVIDER_MODELS[pidx]
        versions.append(AgentVersion(
            id=f"ver-{aid}-{version}", agent_id=aid, version=version,
            system_prompt_hash=_hash(f"{aid}-{version}"),
            system_prompt_summary=f"Baseline configuration for {name}.",
            tools=[], permissions=[], data_sources=[], model=model,
            configuration={"autonomy": autonomy.value, "approval_gate": True},
            created_by=owner, created_at=BASE + timedelta(days=20),
        ))
    return versions


def _refund_dependencies() -> list[AgentDependency]:
    src = "agent-customer-refund"
    spec = [
        ("tool-customer-db", DependencyTargetType.DATABASE, Relationship.READ, RiskLevel.CRITICAL),
        ("tool-salesforce", DependencyTargetType.EXTERNAL_API, Relationship.READ, RiskLevel.HIGH),
        ("tool-stripe", DependencyTargetType.EXTERNAL_API, Relationship.EXECUTE, RiskLevel.CRITICAL),
        ("tool-refund-api", DependencyTargetType.TOOL, Relationship.EXECUTE, RiskLevel.CRITICAL),
        ("tool-email", DependencyTargetType.TOOL, Relationship.EXECUTE, RiskLevel.MODERATE),
    ]
    return [
        AgentDependency(id=f"dep-refund-{i}", source_agent_id=src, target_type=tt,
                        target_id=tid, relationship=rel, risk_level=rl)
        for i, (tid, tt, rel, rl) in enumerate(spec)
    ]


def _policies() -> list[Policy]:
    def policy(pid, name, desc, scope, priority, condition, action, parameters=None):
        return Policy(
            id=pid, name=name, description=desc, scope=scope, priority=priority,
            condition=condition, action=action, parameters=parameters or {}, enabled=True,
            created_by="user-alex-admin", created_at=BASE, updated_at=BASE,
        )
    return [
        policy(
            "policy-rogue-financial-agent", "Rogue Financial Agent",
            "Quarantine high-risk financial agents that lack a human approval gate.",
            "agent", 10,
            {"all": [
                {"field": "risk_score", "op": "gte", "value": 80},
                {"field": "financial_capability", "op": "eq", "value": True},
                {"field": "approval_gate", "op": "eq", "value": False},
            ]},
            PolicyAction.QUARANTINE,
        ),
        policy(
            "policy-pii-export", "PII Export",
            "Deny any external data export that contains PII.",
            "data_export", 20,
            {"all": [
                {"field": "external_data_export", "op": "eq", "value": True},
                {"field": "contains_pii", "op": "eq", "value": True},
            ]},
            PolicyAction.DENY,
        ),
        policy(
            "policy-large-refund", "Large Refund",
            "Refunds over $500 require both a business and a finance approver.",
            "refund", 30,
            {"field": "refund", "op": "gt", "value": 500},
            PolicyAction.REQUIRE_APPROVAL,
            {"roles": ["BUSINESS_APPROVER", "FINANCE_APPROVER"]},
        ),
        policy(
            "policy-medium-refund", "Medium Refund",
            "Refunds from $100 to $500 require a business approver.",
            "refund", 40,
            {"all": [
                {"field": "refund", "op": "gte", "value": 100},
                {"field": "refund", "op": "lte", "value": 500},
            ]},
            PolicyAction.REQUIRE_APPROVAL,
            {"roles": ["BUSINESS_APPROVER"]},
        ),
        policy(
            "policy-small-refund", "Small Refund",
            "Refunds under $100 are auto-approved.",
            "refund", 50,
            {"field": "refund", "op": "lt", "value": 100},
            PolicyAction.ALLOW,
        ),
    ]


def apply_seed(container: RepositoryContainer) -> None:
    org = Organization(id=ORG_ID, name="AcmeCorp", slug="acmecorp", created_at=BASE)
    container.organizations.add(org)

    for user in _personas():
        container.users.add(user)

    for tool in _tools():
        container.tools.add(tool)

    agents = _named_agents() + _generated_agents()
    for agent in agents:
        container.agents.add(agent)

    for version in _named_versions():
        container.agent_versions.add(version)

    for dep in _refund_dependencies():
        container.dependencies.add(dep)

    for pol in _policies():
        container.policies.add(pol)

    _assert_metrics(agents)


def _assert_metrics(agents: list[Agent]) -> None:
    total = len(agents)
    active = sum(1 for a in agents if a.status is AgentStatus.ACTIVE)
    high = sum(1 for a in agents if a.risk_score >= HIGH_RISK_FLOOR)
    quarantined = sum(1 for a in agents if a.status is AgentStatus.QUARANTINED)
    assert total == TARGET_TOTAL, f"expected {TARGET_TOTAL} agents, got {total}"
    assert active == TARGET_ACTIVE, f"expected {TARGET_ACTIVE} active, got {active}"
    assert high == TARGET_HIGH_RISK, f"expected {TARGET_HIGH_RISK} high-risk, got {high}"
    assert quarantined == TARGET_QUARANTINED, f"expected {TARGET_QUARANTINED} quarantined, got {quarantined}"
