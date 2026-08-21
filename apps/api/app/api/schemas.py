"""Response contracts for the foundational endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["swarmops-api"])


class StatusResponse(BaseModel):
    service: str
    version: str
    environment: str
    demo_mode: bool
    category: str = Field(description="Primary hackathon category / product framing.")
    tagline: str
