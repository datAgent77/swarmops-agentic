"""Deterministic security scanning.

`LocalSecurityScanner` detects a small set of demo attack patterns — prompt
injection, PII leakage, suspicious external transmission, and tool poisoning — using
plain regex (no `eval`, no LLM). This is a demonstration scanner, **not** comprehensive
production security, and it is always labeled as such (LOCAL_DEMO).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from app.domain.enums import RiskLevel, SecurityCategory

# (compiled pattern, category, severity, human label)
_PATTERNS: list[tuple[re.Pattern[str], SecurityCategory, RiskLevel, str]] = [
    (re.compile(r"ignore (all )?(previous|prior|above) instructions", re.I),
     SecurityCategory.PROMPT_INJECTION, RiskLevel.HIGH, "instruction override"),
    (re.compile(r"disregard (your|the) (system )?(prompt|instructions)", re.I),
     SecurityCategory.PROMPT_INJECTION, RiskLevel.HIGH, "instruction override"),
    (re.compile(r"you are now|act as (an? )?(unrestricted|dan)", re.I),
     SecurityCategory.PROMPT_INJECTION, RiskLevel.HIGH, "role hijack"),
    (re.compile(r"(export|dump|exfiltrate).{0,30}(all )?(customer|user|pii|personal)( records| data)?", re.I),
     SecurityCategory.PII_LEAKAGE, RiskLevel.HIGH, "bulk PII export"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
     SecurityCategory.PII_LEAKAGE, RiskLevel.HIGH, "SSN pattern"),
    (re.compile(r"(send|post|upload|exfiltrate|export).{0,40}(https?://|attacker|evil|exfil|\.example)", re.I),
     SecurityCategory.EXTERNAL_TRANSMISSION, RiskLevel.HIGH, "external transmission"),
    (re.compile(r"attacker\.\w+|exfil\.\w+", re.I),
     SecurityCategory.EXTERNAL_TRANSMISSION, RiskLevel.HIGH, "suspicious external host"),
    (re.compile(r"(grant|escalate|add).{0,20}(permission|privilege|admin|tool)", re.I),
     SecurityCategory.TOOL_POISONING, RiskLevel.CRITICAL, "privilege/tool escalation"),
    (re.compile(r"curl.{0,20}\|\s*(bash|sh)", re.I),
     SecurityCategory.TOOL_POISONING, RiskLevel.CRITICAL, "remote code execution"),
]

_SEVERITY_ORDER = {RiskLevel.LOW: 0, RiskLevel.MODERATE: 1, RiskLevel.HIGH: 2, RiskLevel.CRITICAL: 3}


@dataclass(frozen=True)
class ScanFinding:
    category: SecurityCategory
    severity: RiskLevel
    label: str
    excerpt: str


@dataclass
class ScanResult:
    verdict: str  # "BLOCK" | "ALLOW"
    severity: RiskLevel
    findings: list[ScanFinding]
    scanner: str
    scanner_status: str  # "LIVE" | "LOCAL_DEMO"
    categories: list[SecurityCategory] = field(default_factory=list)


class SecurityScanner(Protocol):
    name: str
    status: str

    def scan(self, text: str) -> ScanResult: ...


class LocalSecurityScanner:
    name = "LocalSecurityScanner"
    status = "LOCAL_DEMO"

    def scan(self, text: str) -> ScanResult:
        findings: list[ScanFinding] = []
        for pattern, category, severity, label in _PATTERNS:
            match = pattern.search(text)
            if match:
                excerpt = text[max(0, match.start() - 10): match.end() + 10].strip()
                findings.append(ScanFinding(category=category, severity=severity,
                                            label=label, excerpt=excerpt))

        if findings:
            top = max(findings, key=lambda f: _SEVERITY_ORDER[f.severity])
            severity = top.severity
            # Any HIGH+ finding blocks.
            verdict = "BLOCK" if _SEVERITY_ORDER[severity] >= _SEVERITY_ORDER[RiskLevel.HIGH] else "ALLOW"
        else:
            severity = RiskLevel.LOW
            verdict = "ALLOW"

        return ScanResult(
            verdict=verdict, severity=severity, findings=findings,
            scanner=self.name, scanner_status=self.status,
            categories=sorted({f.category for f in findings}, key=lambda c: c.value),
        )
