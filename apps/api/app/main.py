"""FastAPI application factory and ASGI entrypoint.

Route handlers are thin and delegate to the application/domain layers. The
repository container is built at startup and attached to ``app.state`` so tests can
inject an isolated one.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import agents, demo, health, organizations, risk, status, users
from app.config import get_settings
from app.infrastructure.container import RepositoryContainer


def create_app(container: RepositoryContainer | None = None) -> FastAPI:
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

    if container is None:
        container = RepositoryContainer(settings.sqlite_path)
        if settings.demo_mode:
            container.seed_if_empty()
    app.state.container = container

    app.include_router(health.router)
    app.include_router(status.router)
    app.include_router(organizations.router)
    app.include_router(agents.router)
    app.include_router(risk.router)
    app.include_router(users.router)
    app.include_router(demo.router)
    return app


app = create_app()
