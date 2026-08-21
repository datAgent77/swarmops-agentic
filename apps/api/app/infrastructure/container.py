"""Repository container — wires the SQLite backend to the domain interfaces and
owns the seed/reset lifecycle. A later phase (P12) adds a Firestore variant behind
the same surface, selected by ``PERSISTENCE_BACKEND``.
"""

from __future__ import annotations

from app.infrastructure.db import Database
from app.infrastructure.repositories_sqlite import (
    SqliteAgentRepository,
    SqliteAgentVersionRepository,
    SqliteDependencyRepository,
    SqliteOrganizationRepository,
    SqlitePolicyRepository,
    SqliteRiskAssessmentRepository,
    SqliteToolRepository,
    SqliteUserRepository,
)


class RepositoryContainer:
    def __init__(self, sqlite_path: str) -> None:
        self.db = Database(sqlite_path)
        self.organizations = SqliteOrganizationRepository(self.db)
        self.users = SqliteUserRepository(self.db)
        self.agents = SqliteAgentRepository(self.db)
        self.agent_versions = SqliteAgentVersionRepository(self.db)
        self.tools = SqliteToolRepository(self.db)
        self.dependencies = SqliteDependencyRepository(self.db)
        self.policies = SqlitePolicyRepository(self.db)
        self.risk_assessments = SqliteRiskAssessmentRepository(self.db)

    def seed_if_empty(self) -> None:
        if self.db.is_empty():
            self.seed()

    def seed(self) -> None:
        # Imported lazily to avoid a domain <- infrastructure import cycle at module load.
        from app.infrastructure.seed import apply_seed

        apply_seed(self)

    def reset(self) -> None:
        """Deterministically restore the demo dataset (used by /demo/reset)."""
        self.db.wipe()
        self.seed()

    def close(self) -> None:
        self.db.close()
