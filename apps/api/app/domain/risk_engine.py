"""SwarmOps deterministic risk engine.

Pure, explainable, and free of any LLM. Given an agent's configuration it produces
a 0–100 score across seven weighted dimensions, a severity band, human-readable
drivers, and a recommended action. This is the authoritative risk signal — P07's
Gemini layer may *explain* it but can never change it.

Dimension caps (sum = 100):

    PII access                0–20   -> pii
    Financial capabilities    0–20   -> financial
    Production write access   0–15   -> production_write (privilege)
    External tools            0–10   -> external_tools
    Agent autonomy            0–15   -> autonomy
    Missing approval gates    0–10   -> approval_gap  (persisted as data_score)
    Prompt/tool security      0–10   -> prompt_security
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import AutonomyLevel, DependencyTargetType, RecommendedAction, RiskLevel
from app.domain.models import Agent, AgentDependency, AgentVersion
from app.domain.severity import severity_from_score

# Per-dimension maxima (the weights).
CAP_PII = 20
CAP_FINANCIAL = 20
CAP_PRODUCTION_WRITE = 15
CAP_EXTERNAL_TOOLS = 10
CAP_AUTONOMY = 15
CAP_APPROVAL_GAP = 10
CAP_PROMPT_SECURITY = 10

_AUTONOMY_SCORE = {AutonomyLevel.HIGH: 15, AutonomyLevel.MEDIUM: 9, AutonomyLevel.LOW: 3}

# Signals that indicate a real money-moving capability.
_FINANCIAL_PERMISSIONS = ("refund:execute", "payment", "charge", "payout", "transfer")
_FINANCIAL_TOOLS = ("tool-stripe", "tool-refund-api")
_PII_SOURCES = ("customer_db", "customers", "pii")


@dataclass(frozen=True)
class RiskInput:
    """Everything the engine needs, assembled by the application layer."""

    agent: Agent
    version: AgentVersion | None = None
    dependencies: list[AgentDependency] = field(default_factory=list)


@dataclass(frozen=True)
class RiskResult:
    pii: int
    financial: int
    production_write: int
    external_tools: int
    autonomy: int
    approval_gap: int
    prompt_security: int
    total: int
    severity: RiskLevel
    drivers: list[str]
    recommended_action: RecommendedAction


def _permissions(version: AgentVersion | None) -> set[str]:
    return {p.lower() for p in version.permissions} if version else set()


def _has_pii(version: AgentVersion | None) -> bool:
    if version is None:
        return False
    if any(p.startswith("pii") for p in _permissions(version)):
        return True
    return any(src.lower() in _PII_SOURCES for src in version.data_sources)


def _has_financial(version: AgentVersion | None) -> bool:
    if version is None:
        return False
    if version.configuration.get("financial_capability") is True:
        return True
    perms = _permissions(version)
    if any(any(sig in p for sig in _FINANCIAL_PERMISSIONS) for p in perms):
        return True
    return any(t in _FINANCIAL_TOOLS for t in version.tools)


def _external_count(dependencies: list[AgentDependency]) -> int:
    return sum(1 for d in dependencies if d.target_type is DependencyTargetType.EXTERNAL_API)


def _approval_gate(version: AgentVersion | None) -> bool:
    # Absence of explicit config is treated as "gated" (safe default).
    if version is None:
        return True
    return bool(version.configuration.get("approval_gate", True))


def assess(inp: RiskInput) -> RiskResult:
    version = inp.version
    perms = _permissions(version)

    has_pii = _has_pii(version)
    has_financial = _has_financial(version)
    has_prod_write = "production:write" in perms
    external_count = _external_count(inp.dependencies)
    has_gate = _approval_gate(version)
    has_tools = bool(version.tools) if version else False

    # --- Dimension scores -------------------------------------------------
    pii = 0
    if has_pii:
        pii = 16 + (4 if "pii:write" in perms else 0)  # 16 read, 20 read+write

    financial = CAP_FINANCIAL if has_financial else 0
    production_write = CAP_PRODUCTION_WRITE if has_prod_write else 0
    external_tools = min(CAP_EXTERNAL_TOOLS, 4 * external_count)
    autonomy = _AUTONOMY_SCORE[inp.agent.autonomy_level]

    # A missing approval gate only matters when the agent can do something costly.
    approval_gap = CAP_APPROVAL_GAP if (not has_gate and (has_financial or has_prod_write)) else 0

    # Baseline exposure until the P10 security scanner enriches this dimension.
    prompt_security = 3 if (has_tools or external_count > 0) else 0

    total = pii + financial + production_write + external_tools + autonomy + approval_gap + prompt_security
    total = min(100, total)
    severity = severity_from_score(total)

    drivers = _drivers(has_financial, has_pii, has_prod_write, external_count, inp.agent.autonomy_level, has_gate)
    action = _recommend(severity, has_financial, has_gate)

    return RiskResult(
        pii=pii, financial=financial, production_write=production_write,
        external_tools=external_tools, autonomy=autonomy, approval_gap=approval_gap,
        prompt_security=prompt_security, total=total, severity=severity,
        drivers=drivers, recommended_action=action,
    )


def _drivers(
    has_financial: bool,
    has_pii: bool,
    has_prod_write: bool,
    external_count: int,
    autonomy: AutonomyLevel,
    has_gate: bool,
) -> list[str]:
    out: list[str] = []
    if has_financial:
        out.append("Can execute financial transactions")
    if has_pii:
        out.append("Handles customer PII")
    if has_prod_write:
        out.append("Has production write access")
    if not has_gate and (has_financial or has_prod_write):
        out.append("No human approval configured")
    if external_count:
        out.append(f"Reaches {external_count} external system(s)")
    if autonomy is AutonomyLevel.HIGH:
        out.append("Operates at high autonomy")
    return out


def _recommend(severity: RiskLevel, has_financial: bool, has_gate: bool) -> RecommendedAction:
    if severity is RiskLevel.CRITICAL:
        if has_financial and not has_gate:
            return RecommendedAction.QUARANTINE
        return RecommendedAction.SUSPEND
    if severity is RiskLevel.HIGH:
        return RecommendedAction.REQUIRE_APPROVAL
    if severity is RiskLevel.MODERATE:
        return RecommendedAction.MONITOR
    return RecommendedAction.ALLOW
