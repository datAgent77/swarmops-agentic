"""FastAPI dependencies for accessing the repository container."""

from __future__ import annotations

from fastapi import Request

from app.infrastructure.container import RepositoryContainer


def get_container(request: Request) -> RepositoryContainer:
    """Return the process-wide repository container attached at app startup."""
    return request.app.state.container
