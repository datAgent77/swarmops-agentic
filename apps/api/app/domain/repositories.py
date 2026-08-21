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
    AgentDependency,
    AgentVersion,
    Organization,
    Policy,
    RiskAssessment,
    Tool,
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


class PolicyRepository(ABC):
    @abstractmethod
    def add(self, policy: Policy) -> None: ...

    @abstractmethod
    def get(self, policy_id: str) -> Policy | None: ...

    @abstractmethod
    def update(self, policy: Policy) -> None: ...

    @abstractmethod
    def list(self) -> Sequence[Policy]: ...


class RiskAssessmentRepository(ABC):
    @abstractmethod
    def add(self, assessment: RiskAssessment) -> None: ...

    @abstractmethod
    def latest_for_agent(self, agent_id: str) -> RiskAssessment | None: ...

    @abstractmethod
    def list_for_agent(self, agent_id: str) -> Sequence[RiskAssessment]: ...
