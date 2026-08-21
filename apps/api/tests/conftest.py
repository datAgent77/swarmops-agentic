"""Shared test fixtures.

Each test gets an isolated, seeded in-memory repository container so tests never
touch the developer's local SQLite file and never share state.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.container import RepositoryContainer
from app.main import create_app


@pytest.fixture
def container() -> Iterator[RepositoryContainer]:
    c = RepositoryContainer(":memory:")
    c.seed()
    yield c
    c.close()


@pytest.fixture
def client(container: RepositoryContainer) -> TestClient:
    return TestClient(create_app(container=container))
