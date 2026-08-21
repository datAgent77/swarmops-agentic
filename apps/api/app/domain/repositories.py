"""Repository interfaces (ports).

The domain declares these; infrastructure provides implementations (SQLite in P01,
Firestore in P12). Application/API code depends only on these abstractions, never
on a concrete backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

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


@dataclass(frozen=True)
class AgentQuery:
    """Filter/search parameters for listing agents. All fields optional."""

    status: str | None = None
    department: str | None = None
    risk: RiskLevel | None = None  # minimum severity band (e.g. HIGH → HIGH+)
    search: str | None = None
    limit: int | None = None
    offset: int = 0


class OrganizationRepository(ABC):
    @abstractmethod
    def add(self, org: Organization) -> None: ...

    @abstractmethod
    def get(self, org_id: str) -> Organization | None: ...

    @abstractmethod
    def get_current(self) -> Organization | None: ...


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> None: ...

    @abstractmethod
    def get(self, user_id: str) -> User | None: ...

    @abstractmethod
    def list(self, organization_id: str | None = None) -> Sequence[User]: ...


class AgentRepository(ABC):
    @abstractmethod
    def add(self, agent: Agent) -> None: ...

    @abstractmethod
    def get(self, agent_id: str) -> Agent | None: ...

    @abstractmethod
    def update(self, agent: Agent) -> None: ...

    @abstractmethod
    def list(self, query: AgentQuery | None = None) -> Sequence[Agent]: ...

    @abstractmethod
    def count_total(self) -> int: ...

    @abstractmethod
    def departments(self) -> Sequence[str]: ...


class AgentVersionRepository(ABC):
    @abstractmethod
    def add(self, version: AgentVersion) -> None: ...

    @abstractmethod
    def get(self, version_id: str) -> AgentVersion | None: ...

    @abstractmethod
    def list_for_agent(self, agent_id: str) -> list[AgentVersion]: ...


class ToolRepository(ABC):
    @abstractmethod
    def add(self, tool: Tool) -> None: ...

    @abstractmethod
    def get(self, tool_id: str) -> Tool | None: ...

    @abstractmethod
    def list(self) -> Sequence[Tool]: ...


class DependencyRepository(ABC):
    @abstractmethod
    def add(self, dependency: AgentDependency) -> None: ...

    @abstractmethod
    def list_for_agent(self, agent_id: str) -> list[AgentDependency]: ...

    @abstractmethod
    def list_all(self) -> Sequence[AgentDependency]: ...


class PolicyRepository(ABC):
    @abstractmethod
    def add(self, policy: Policy) -> None: ...

    @abstractmethod
    def get(self, policy_id: str) -> Policy | None: ...

    @abstractmethod
    def update(self, policy: Policy) -> None: ...

    @abstractmethod
    def list(self) -> Sequence[Policy]: ...


class ExecutionRepository(ABC):
    @abstractmethod
    def add(self, execution: Execution) -> None: ...

    @abstractmethod
    def get(self, execution_id: str) -> Execution | None: ...

    @abstractmethod
    def update(self, execution: Execution) -> None: ...

    @abstractmethod
    def list(self, limit: int | None = None) -> Sequence[Execution]: ...


class ToolCallRepository(ABC):
    @abstractmethod
    def add(self, tool_call: ToolCall) -> None: ...

    @abstractmethod
    def list_for_execution(self, execution_id: str) -> Sequence[ToolCall]: ...

    @abstractmethod
    def find_by_idempotency_key(self, key: str) -> ToolCall | None: ...


class ApprovalRepository(ABC):
    @abstractmethod
    def add(self, approval: ApprovalRequest) -> None: ...

    @abstractmethod
    def get(self, approval_id: str) -> ApprovalRequest | None: ...

    @abstractmethod
    def update(self, approval: ApprovalRequest) -> None: ...

    @abstractmethod
    def list(self, status: str | None = None) -> Sequence[ApprovalRequest]: ...

    @abstractmethod
    def list_for_execution(self, execution_id: str) -> Sequence[ApprovalRequest]: ...


class AuditRepository(ABC):
    @abstractmethod
    def add(self, event: AuditEvent) -> None: ...

    @abstractmethod
    def list(self, limit: int | None = None) -> Sequence[AuditEvent]: ...

    @abstractmethod
    def list_for_resource(self, resource_type: str, resource_id: str) -> Sequence[AuditEvent]: ...

    @abstractmethod
    def list_for_trace(self, trace_id: str) -> Sequence[AuditEvent]: ...


class ChangeProposalRepository(ABC):
    @abstractmethod
    def add(self, proposal: AgentChangeProposal) -> None: ...

    @abstractmethod
    def get(self, proposal_id: str) -> AgentChangeProposal | None: ...

    @abstractmethod
    def update(self, proposal: AgentChangeProposal) -> None: ...

    @abstractmethod
    def list_for_agent(self, agent_id: str) -> Sequence[AgentChangeProposal]: ...


class SecurityIncidentRepository(ABC):
    @abstractmethod
    def add(self, incident: SecurityIncident) -> None: ...

    @abstractmethod
    def list(self, limit: int | None = None) -> Sequence[SecurityIncident]: ...


class RiskAssessmentRepository(ABC):
    @abstractmethod
    def add(self, assessment: RiskAssessment) -> None: ...

    @abstractmethod
    def latest_for_agent(self, agent_id: str) -> RiskAssessment | None: ...

    @abstractmethod
    def list_for_agent(self, agent_id: str) -> Sequence[RiskAssessment]: ...
