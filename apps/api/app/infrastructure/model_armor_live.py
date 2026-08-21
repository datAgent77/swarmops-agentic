"""Live Model Armor scanner (only used when the optional client + credentials exist).

This module is imported lazily by ``model_armor.get_scanner`` and only when Model
Armor is genuinely available. Every call is guarded: if the client or request fails
for any reason, the result degrades to the deterministic local scanner and is honestly
labeled LOCAL_DEMO — the UI never shows LIVE for a request that did not run through
Model Armor.

NOTE: the exact Model Armor request/response mapping must be validated against the
current official API before relying on it in production; this wrapper degrades safely
if it does not match.
"""

from __future__ import annotations

from app.config import Settings
from app.domain.enums import RiskLevel, SecurityCategory
from app.domain.security import LocalSecurityScanner, ScanFinding, ScanResult


class ModelArmorScanner:
    name = "ModelArmor"
    status = "LIVE"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._local = LocalSecurityScanner()

    def scan(self, text: str) -> ScanResult:  # pragma: no cover - requires live Model Armor
        try:
            from google.cloud import modelarmor_v1

            client = modelarmor_v1.ModelArmorClient()
            response = client.sanitize_user_prompt(
                request={
                    "name": (
                        f"projects/{self._settings.google_cloud_project}"
                        f"/locations/{self._settings.google_cloud_location}/templates/swarmops"
                    ),
                    "user_prompt_data": {"text": text},
                }
            )
            return self._map(response)
        except Exception:  # noqa: BLE001 — degrade honestly to the local scanner
            result = self._local.scan(text)
            result.scanner = "LocalSecurityScanner (Model Armor unavailable)"
            result.scanner_status = "LOCAL_DEMO"
            return result

    def _map(self, response: object) -> ScanResult:  # pragma: no cover
        # Conservative mapping: block if Model Armor flagged the prompt.
        blocked = bool(getattr(getattr(response, "sanitization_result", None), "filter_match_state", 0))
        findings = (
            [ScanFinding(category=SecurityCategory.PROMPT_INJECTION, severity=RiskLevel.HIGH,
                         label="model armor match", excerpt="")]
            if blocked else []
        )
        return ScanResult(
            verdict="BLOCK" if blocked else "ALLOW",
            severity=RiskLevel.HIGH if blocked else RiskLevel.LOW,
            findings=findings, scanner=self.name, scanner_status=self.status,
            categories=[f.category for f in findings],
        )
