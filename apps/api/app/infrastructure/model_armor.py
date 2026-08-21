"""Model Armor adapter.

Integration seam for Google Model Armor (inline guardrails for prompt injection,
tool poisoning, and PII leakage). When Model Armor is enabled AND its client library
(`google-cloud-modelarmor`) is installed AND a GCP project is configured, scanning
routes through it and status is reported as **LIVE**. Otherwise the deterministic
`LocalSecurityScanner` is used and status is reported as **LOCAL_DEMO**.

This adapter never fabricates a Model Armor call and never labels the local scanner as
live — the UI shows exactly which one ran.
"""

from __future__ import annotations

from app.config import Settings
from app.domain.security import LocalSecurityScanner, SecurityScanner

STATUS_LIVE = "LIVE"
STATUS_LOCAL = "LOCAL_DEMO"


def _model_armor_importable() -> bool:
    try:  # pragma: no cover - only true when the optional package is installed
        import google.cloud.modelarmor  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def is_live(settings: Settings) -> bool:
    return bool(
        settings.model_armor_enabled
        and settings.google_cloud_project
        and _model_armor_importable()
    )


def scanner_status(settings: Settings) -> str:
    return STATUS_LIVE if is_live(settings) else STATUS_LOCAL


def get_scanner(settings: Settings) -> SecurityScanner:
    """Return the active scanner. Only returns a live Model Armor scanner when it is
    genuinely available; otherwise the honest local-demo scanner."""
    if is_live(settings):  # pragma: no cover - requires the optional package + creds
        from app.infrastructure.model_armor_live import ModelArmorScanner

        return ModelArmorScanner(settings)
    return LocalSecurityScanner()
