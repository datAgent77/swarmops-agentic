"""Firestore-backed repositories (optional ``[gcp]`` extra).

Same interfaces as the SQLite repositories, selected by ``PERSISTENCE_BACKEND=firestore``.
Documents are stored as ``model.model_dump(mode="json")`` and reconstructed with
``model_validate``, so the mapping is uniform across every entity. List operations
fetch a collection and filter/sort in Python (the datasets are demo-sized).

Run locally against the Firestore emulator (see docs/deployment/google-cloud.md); the
client is imported lazily so the base install never requires it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from app.domain.enums import RiskLevel
from app.domain.models import (
    Agent,
    AgentChangeProposal,
    AgentDependency,
    AgentVersion,
    ApprovalRequest,
    AuditEvent,
    Execution,
    Organization,
    Policy,
    RiskAssessment,
    SecurityIncident,
    Tool,
    ToolCall,
    User,
)
from app.domain.repositories import (
    AgentQuery,
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

_RISK_FLOOR = {RiskLevel.LOW: 0, RiskLevel.MODERATE: 25, RiskLevel.HIGH: 50, RiskLevel.CRITICAL: 75}

M = TypeVar("M", bound=BaseModel)

COLLECTIONS = (
    "organizations", "users", "agents", "agent_versions", "tools", "agent_dependencies",
    "policies", "risk_assessments", "executions", "tool_calls", "approvals",
    "audit_events", "security_incidents", "change_proposals",
)


class FirestoreDatabase:
    def __init__(self, project: str | None) -> None:
        from google.cloud import firestore  # lazy: optional dependency

        self.client = firestore.Client(project=project) if project else firestore.Client()

    def is_empty(self) -> bool:
        return next(self.client.collection("organizations").limit(1).stream(), None) is None

    def wipe(self) -> None:
        for name in COLLECTIONS:
            for doc in self.client.collection(name).stream():
                doc.reference.delete()

    def close(self) -> None:  # symmetry with the SQLite database
        pass


class _Fs:
    def __init__(self, db: FirestoreDatabase, collection: str, model: type[M]) -> None:
        self._col = db.client.collection(collection)
        self._model = model

    def _set(self, doc_id: str, model: BaseModel) -> None:
        self._col.document(doc_id).set(model.model_dump(mode="json"))

    def _get(self, doc_id: str) -> Any:
        snap = self._col.document(doc_id).get()
        return self._model.model_validate(snap.to_dict()) if snap.exists else None

    def _all(self) -> list[Any]:
        return [self._model.model_validate(d.to_dict()) for d in self._col.stream()]

    def _where(self, field: str, value: Any) -> list[Any]:
        return [
            self._model.model_validate(d.to_dict())
            for d in self._col.where(field, "==", value).stream()
        ]


class FsOrganizationRepository(_Fs, OrganizationRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "organizations", Organization)

    def add(self, org: Organization) -> None:
        self._set(org.id, org)

    def get(self, org_id: str) -> Organization | None:
        return self._get(org_id)

    def get_current(self) -> Organization | None:
        items = sorted(self._all(), key=lambda o: o.created_at)
        return items[0] if items else None


class FsUserRepository(_Fs, UserRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "users", User)

    def add(self, user: User) -> None:
        self._set(user.id, user)

    def get(self, user_id: str) -> User | None:
        return self._get(user_id)

    def list(self, organization_id: str | None = None) -> Sequence[User]:
        items = self._all()
        if organization_id:
            items = [u for u in items if u.organization_id == organization_id]
        return sorted(items, key=lambda u: u.created_at)


class FsAgentRepository(_Fs, AgentRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "agents", Agent)

    def add(self, agent: Agent) -> None:
        self._set(agent.id, agent)

    def update(self, agent: Agent) -> None:
        self._set(agent.id, agent)

    def get(self, agent_id: str) -> Agent | None:
        return self._get(agent_id)

    def list(self, query: AgentQuery | None = None) -> Sequence[Agent]:
        q = query or AgentQuery()
        items = self._all()
        if q.status:
            items = [a for a in items if a.status.value == q.status]
        if q.department:
            items = [a for a in items if a.department == q.department]
        if q.risk is not None:
            items = [a for a in items if a.risk_score >= _RISK_FLOOR[q.risk]]
        if q.search:
            needle = q.search.lower()
            items = [a for a in items
                     if needle in a.name.lower() or needle in a.description.lower()
                     or needle in a.department.lower()]
        items.sort(key=lambda a: (-a.risk_score, a.name))
        if q.limit is not None:
            items = items[q.offset: q.offset + q.limit]
        return items

    def count_total(self) -> int:
        return len(self._all())

    def departments(self) -> Sequence[str]:
        return sorted({a.department for a in self._all()})


class FsAgentVersionRepository(_Fs, AgentVersionRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "agent_versions", AgentVersion)

    def add(self, version: AgentVersion) -> None:
        self._set(version.id, version)

    def get(self, version_id: str) -> AgentVersion | None:
        return self._get(version_id)

    def list_for_agent(self, agent_id: str) -> list[AgentVersion]:
        return sorted(self._where("agent_id", agent_id), key=lambda v: v.created_at)


class FsToolRepository(_Fs, ToolRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "tools", Tool)

    def add(self, tool: Tool) -> None:
        self._set(tool.id, tool)

    def get(self, tool_id: str) -> Tool | None:
        return self._get(tool_id)

    def list(self) -> Sequence[Tool]:
        return sorted(self._all(), key=lambda t: t.name)


class FsDependencyRepository(_Fs, DependencyRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "agent_dependencies", AgentDependency)

    def add(self, dependency: AgentDependency) -> None:
        self._set(dependency.id, dependency)

    def list_for_agent(self, agent_id: str) -> list[AgentDependency]:
        return self._where("source_agent_id", agent_id)

    def list_all(self) -> Sequence[AgentDependency]:
        return self._all()


class FsPolicyRepository(_Fs, PolicyRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "policies", Policy)

    def add(self, policy: Policy) -> None:
        self._set(policy.id, policy)

    def update(self, policy: Policy) -> None:
        self._set(policy.id, policy)

    def get(self, policy_id: str) -> Policy | None:
        return self._get(policy_id)

    def list(self) -> Sequence[Policy]:
        return sorted(self._all(), key=lambda p: p.priority)


class FsRiskAssessmentRepository(_Fs, RiskAssessmentRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "risk_assessments", RiskAssessment)

    def add(self, assessment: RiskAssessment) -> None:
        self._set(assessment.id, assessment)

    def latest_for_agent(self, agent_id: str) -> RiskAssessment | None:
        items = sorted(self._where("agent_id", agent_id), key=lambda a: a.created_at)
        return items[-1] if items else None

    def list_for_agent(self, agent_id: str) -> Sequence[RiskAssessment]:
        return sorted(self._where("agent_id", agent_id), key=lambda a: a.created_at, reverse=True)


class FsExecutionRepository(_Fs, ExecutionRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "executions", Execution)

    def add(self, execution: Execution) -> None:
        self._set(execution.id, execution)

    def update(self, execution: Execution) -> None:
        self._set(execution.id, execution)

    def get(self, execution_id: str) -> Execution | None:
        return self._get(execution_id)

    def list(self, limit: int | None = None) -> Sequence[Execution]:
        items = sorted(self._all(), key=lambda e: e.started_at or e.trace_id, reverse=True)
        return items[:limit] if limit is not None else items


class FsToolCallRepository(_Fs, ToolCallRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "tool_calls", ToolCall)

    def add(self, tool_call: ToolCall) -> None:
        self._set(tool_call.id, tool_call)

    def list_for_execution(self, execution_id: str) -> Sequence[ToolCall]:
        return sorted(self._where("execution_id", execution_id), key=lambda t: t.started_at)

    def find_by_idempotency_key(self, key: str) -> ToolCall | None:
        items = sorted(self._where("idempotency_key", key), key=lambda t: t.started_at)
        return items[0] if items else None


class FsApprovalRepository(_Fs, ApprovalRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "approvals", ApprovalRequest)

    def add(self, approval: ApprovalRequest) -> None:
        self._set(approval.id, approval)

    def update(self, approval: ApprovalRequest) -> None:
        self._set(approval.id, approval)

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._get(approval_id)

    def list(self, status: str | None = None) -> Sequence[ApprovalRequest]:
        items = sorted(self._all(), key=lambda a: a.created_at)
        return [a for a in items if a.status.value == status] if status else items

    def list_for_execution(self, execution_id: str) -> Sequence[ApprovalRequest]:
        return sorted(self._where("execution_id", execution_id), key=lambda a: a.sequence)


class FsAuditRepository(_Fs, AuditRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "audit_events", AuditEvent)

    def add(self, event: AuditEvent) -> None:
        self._set(event.id, event)

    def list(self, limit: int | None = None) -> Sequence[AuditEvent]:
        items = sorted(self._all(), key=lambda e: e.timestamp, reverse=True)
        return items[:limit] if limit is not None else items

    def list_for_resource(self, resource_type: str, resource_id: str) -> Sequence[AuditEvent]:
        return sorted(
            [e for e in self._all() if e.resource_type == resource_type and e.resource_id == resource_id],
            key=lambda e: e.timestamp,
        )

    def list_for_trace(self, trace_id: str) -> Sequence[AuditEvent]:
        return sorted(self._where("trace_id", trace_id), key=lambda e: e.timestamp)


class FsSecurityIncidentRepository(_Fs, SecurityIncidentRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "security_incidents", SecurityIncident)

    def add(self, incident: SecurityIncident) -> None:
        self._set(incident.id, incident)

    def list(self, limit: int | None = None) -> Sequence[SecurityIncident]:
        items = sorted(self._all(), key=lambda i: i.created_at, reverse=True)
        return items[:limit] if limit is not None else items


class FsChangeProposalRepository(_Fs, ChangeProposalRepository):
    def __init__(self, db: FirestoreDatabase) -> None:
        super().__init__(db, "change_proposals", AgentChangeProposal)

    def add(self, proposal: AgentChangeProposal) -> None:
        self._set(proposal.id, proposal)

    def update(self, proposal: AgentChangeProposal) -> None:
        self._set(proposal.id, proposal)

    def get(self, proposal_id: str) -> AgentChangeProposal | None:
        return self._get(proposal_id)

    def list_for_agent(self, agent_id: str) -> Sequence[AgentChangeProposal]:
        return sorted(self._where("agent_id", agent_id), key=lambda p: p.created_at, reverse=True)
