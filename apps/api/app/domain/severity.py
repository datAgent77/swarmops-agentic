"""Severity banding from a 0–100 risk score.

The full deterministic risk engine arrives in P02; the band thresholds themselves
are stable and shared here so P01 (seed data, filters, UI) and P02 agree.
"""

from __future__ import annotations

from app.domain.enums import RiskLevel

# A score >= this floor counts as "high risk" for fleet metrics and filters.
HIGH_RISK_FLOOR = 50


def severity_from_score(score: int) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MODERATE
    return RiskLevel.LOW
