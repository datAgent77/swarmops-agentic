"""Application settings, loaded from the environment with safe local defaults.

Only foundational configuration lives here in P00. Google Cloud / Gemini fields
are declared as optional placeholders now so later phases can wire them in
without changing the settings contract.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core -------------------------------------------------------------
    environment: str = Field(default="development", alias="ENVIRONMENT")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    # --- Persistence ------------------------------------------------------
    # "local" (SQLite) today; "firestore" is added in P12 behind the same
    # repository interfaces.
    persistence_backend: str = Field(default="local", alias="PERSISTENCE_BACKEND")
    sqlite_path: str = Field(default="swarmops.db", alias="SQLITE_PATH")
    # Domain event bus: "inmemory" (default) or "pubsub" (needs a GCP project).
    event_bus: str = Field(default="inmemory", alias="EVENT_BUS")

    # CORS is restricted to configured frontend origins. NoDecode disables
    # pydantic-settings' JSON parsing so a plain comma-separated env value works
    # (the validator below splits it); a JSON list is also accepted.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000"], alias="CORS_ORIGINS"
    )

    # --- Google Cloud / Gemini (placeholders; wired in later phases) -------
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="us-central1", alias="GOOGLE_CLOUD_LOCATION")
    google_genai_use_vertexai: bool = Field(default=False, alias="GOOGLE_GENAI_USE_VERTEXAI")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
    # Direct Gemini Developer API key (alternative to Vertex AI). Optional.
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    # --- Observability ----------------------------------------------------
    # When enabled with a GCP project, traces export to Cloud Trace; otherwise the
    # audit trail retains local, trace-correlated telemetry.
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")

    # --- Security ---------------------------------------------------------
    # When enabled with a GCP project AND the google-cloud-modelarmor package,
    # scanning uses Google Model Armor; otherwise the local demo scanner is used.
    model_armor_enabled: bool = Field(default=False, alias="MODEL_ARMOR_ENABLED")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
