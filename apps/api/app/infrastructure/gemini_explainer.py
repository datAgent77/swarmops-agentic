"""Governance explanation layer (Gemini via the Google GenAI SDK).

This is the ONLY place an LLM is invoked, and it produces prose only. It receives a
deterministic decision that has already been made and explains it — it can never
change a score, severity, or action. When Gemini is not configured/available the
explainer degrades to a clearly-labeled local template; it never claims Gemini ran
when it did not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.config import Settings

# Model status strings surfaced to the UI so the source is always truthful.
STATUS_LIVE = "LIVE"
STATUS_LOCAL = "LOCAL_TEMPLATE"


@dataclass(frozen=True)
class GovernanceExplanation:
    text: str
    model_status: str          # STATUS_LIVE | STATUS_LOCAL
    model_name: str
    provider: str


class GovernanceExplainer(Protocol):
    def explain(self, facts: dict[str, Any]) -> GovernanceExplanation: ...


def _prompt(facts: dict[str, Any]) -> str:
    return (
        "You are a governance analyst. A DETERMINISTIC engine has already decided the "
        "outcome below. Explain the risk and recommend remediation in 3-5 sentences. "
        "You may not change the decision.\n\n"
        f"Agent: {facts.get('agent_name')}\n"
        f"Risk score: {facts.get('score')}/100 ({facts.get('severity')})\n"
        f"Risk drivers: {', '.join(facts.get('drivers', [])) or 'none'}\n"
        f"Recommended action: {facts.get('recommended_action')}\n"
        f"Policy decision: {facts.get('policy_action')} ({facts.get('policy_name')})\n"
    )


def _local_text(facts: dict[str, Any]) -> str:
    drivers = facts.get("drivers", [])
    driver_line = "; ".join(drivers) if drivers else "no elevated risk drivers"
    return (
        f"[Local template — Gemini not invoked] {facts.get('agent_name')} scores "
        f"{facts.get('score')}/100 ({facts.get('severity')}). Key drivers: {driver_line}. "
        f"The deterministic policy decision is {facts.get('policy_action')} "
        f"({facts.get('policy_name')}); recommended remediation: {facts.get('recommended_action')}. "
        "Configure GEMINI_API_KEY or Vertex AI to generate a natural-language explanation."
    )


class LocalTemplateExplainer:
    """Deterministic, offline fallback. Clearly not Gemini."""

    def explain(self, facts: dict[str, Any]) -> GovernanceExplanation:
        return GovernanceExplanation(
            text=_local_text(facts), model_status=STATUS_LOCAL,
            model_name="local-template", provider="local",
        )


class GeminiExplainer:
    """Live explainer backed by the Google GenAI SDK (Gemini Developer API or Vertex AI)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback = LocalTemplateExplainer()

    def _client(self):  # lazy import so the SDK stays an optional dependency
        from google import genai

        if self._settings.google_genai_use_vertexai and self._settings.google_cloud_project:
            return genai.Client(
                vertexai=True,
                project=self._settings.google_cloud_project,
                location=self._settings.google_cloud_location,
            )
        return genai.Client(api_key=self._settings.gemini_api_key)

    def explain(self, facts: dict[str, Any]) -> GovernanceExplanation:
        try:
            from google.genai import types

            client = self._client()
            resp = client.models.generate_content(
                model=self._settings.gemini_model,
                contents=_prompt(facts),
                config=types.GenerateContentConfig(
                    system_instruction="Explain governance decisions; never alter them.",
                    temperature=0.2, max_output_tokens=400,
                ),
            )
            text = (resp.text or "").strip() or _local_text(facts)
            provider = "google-genai (Vertex AI)" if self._settings.google_genai_use_vertexai \
                else "google-genai (Gemini API)"
            return GovernanceExplanation(
                text=text, model_status=STATUS_LIVE,
                model_name=self._settings.gemini_model, provider=provider,
            )
        except Exception:  # noqa: BLE001 — any SDK/credential/network error degrades honestly
            return self._fallback.explain(facts)


def _genai_available() -> bool:
    try:
        import google.genai  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def get_explainer(settings: Settings) -> GovernanceExplainer:
    """Pick a live Gemini explainer only when the SDK AND credentials are present."""
    has_creds = bool(settings.gemini_api_key) or (
        settings.google_genai_use_vertexai and bool(settings.google_cloud_project)
    )
    if has_creds and _genai_available():
        return GeminiExplainer(settings)
    return LocalTemplateExplainer()
