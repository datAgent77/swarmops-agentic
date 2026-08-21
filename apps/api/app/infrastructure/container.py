"""Repository container — wires a persistence backend to the domain interfaces and
owns the seed/reset lifecycle plus the domain event bus.

Backend is selected by ``PERSISTENCE_BACKEND``: ``local`` (SQLite, the default) or
``firestore``. Both expose the identical repository surface, so nothing above the
infrastructure layer changes when the backend does.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.repositories import (
    AgentRepository,
    AgentVersionRepository,
    ApprovalRepository,
    AuditRepository,
    ChangeProposalRepository,
    DependencyRepository,
    ExecutionRepository,
    OrganizationRepository,
    PolicyRepository,
    RiskAssessmentRepository,
    SecurityIncidentRepository,
    ToolCallRepository,
    ToolRepository,
    UserRepository,
)
from app.infrastructure.db import Database
from app.infrastructure.events import EventBus, InMemoryEventBus
from app.infrastructure.repositories_sqlite import (
    SqliteAgentRepository,
    SqliteAgentVersionRepository,
    SqliteApprovalRepository,
    SqliteAuditRepository,
    SqliteChangeProposalRepository,
    SqliteDependencyRepository,
    SqliteExecutionRepository,
    SqliteOrganizationRepository,
    SqlitePolicyRepository,
    SqliteRiskAssessmentRepository,
    SqliteSecurityIncidentRepository,
    SqliteToolCallRepository,
    SqliteToolRepository,
    SqliteUserRepository,
)


class _PersistenceDb(Protocol):
    def is_empty(self) -> bool: ...
    def wipe(self) -> None: ...
    def close(self) -> None: ...


class RepositoryContainer:
    # Typed against the interfaces so either backend satisfies the same surface.
    _db: _PersistenceDb
    organizations: OrganizationRepository
    users: UserRepository
    agents: AgentRepository
    agent_versions: AgentVersionRepository
    tools: ToolRepository
    dependencies: DependencyRepository
    policies: PolicyRepository
    risk_assessments: RiskAssessmentRepository
    executions: ExecutionRepository
    tool_calls: ToolCallRepository
    approvals: ApprovalRepository
    audit_events: AuditRepository
    security_incidents: SecurityIncidentRepository
    change_proposals: ChangeProposalRepository

    def __init__(
        self,
        sqlite_path: str = ":memory:",
        *,
        backend: str = "local",
        project: str | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.backend = backend
        self.event_bus: EventBus = event_bus or InMemoryEventBus()
        if backend == "firestore":
            self._wire_firestore(project)
        else:
            self._wire_sqlite(sqlite_path)

    def _wire_sqlite(self, sqlite_path: str) -> None:
        self._db = Database(sqlite_path)
        self.organizations = SqliteOrganizationRepository(self._db)
        self.users = SqliteUserRepository(self._db)
        self.agents = SqliteAgentRepository(self._db)
        self.agent_versions = SqliteAgentVersionRepository(self._db)
        self.tools = SqliteToolRepository(self._db)
        self.dependencies = SqliteDependencyRepository(self._db)
        self.policies = SqlitePolicyRepository(self._db)
        self.risk_assessments = SqliteRiskAssessmentRepository(self._db)
        self.executions = SqliteExecutionRepository(self._db)
        self.tool_calls = SqliteToolCallRepository(self._db)
        self.approvals = SqliteApprovalRepository(self._db)
        self.audit_events = SqliteAuditRepository(self._db)
        self.security_incidents = SqliteSecurityIncidentRepository(self._db)
        self.change_proposals = SqliteChangeProposalRepository(self._db)

    def _wire_firestore(self, project: str | None) -> None:
        # Imported lazily so google-cloud-firestore stays an optional [gcp] extra.
        from app.infrastructure import firestore_repos as fs

        self._db = fs.FirestoreDatabase(project)
        self.organizations = fs.FsOrganizationRepository(self._db)
        self.users = fs.FsUserRepository(self._db)
        self.agents = fs.FsAgentRepository(self._db)
        self.agent_versions = fs.FsAgentVersionRepository(self._db)
        self.tools = fs.FsToolRepository(self._db)
        self.dependencies = fs.FsDependencyRepository(self._db)
        self.policies = fs.FsPolicyRepository(self._db)
        self.risk_assessments = fs.FsRiskAssessmentRepository(self._db)
        self.executions = fs.FsExecutionRepository(self._db)
        self.tool_calls = fs.FsToolCallRepository(self._db)
        self.approvals = fs.FsApprovalRepository(self._db)
        self.audit_events = fs.FsAuditRepository(self._db)
        self.security_incidents = fs.FsSecurityIncidentRepository(self._db)
        self.change_proposals = fs.FsChangeProposalRepository(self._db)

    def seed_if_empty(self) -> None:
        if self._db.is_empty():
            self.seed()

    def seed(self) -> None:
        from app.infrastructure.seed import apply_seed

        apply_seed(self)

    def reset(self) -> None:
        """Deterministically restore the demo dataset (used by /demo/reset)."""
        self._db.wipe()
        self.seed()

    def close(self) -> None:
        self._db.close()
