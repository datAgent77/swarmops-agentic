"""FastAPI application factory and ASGI entrypoint.

Route handlers are thin and delegate to lower layers as those layers arrive in
later phases. P00 wires only health/status plus CORS.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import health, status
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SwarmOps API",
        version=__version__,
        summary="Enterprise Agent Control Plane — Discover. Govern. Orchestrate. Observe.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(status.router)
    return app


app = create_app()
