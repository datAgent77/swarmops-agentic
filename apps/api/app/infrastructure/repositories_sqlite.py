"""SQLite-backed implementations of the domain repository interfaces."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from typing import Any

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
from app.domain.repositories import (
    AgentQuery,
    AgentRepository,
    AgentVersionRepository,
    DependencyRepository,
    OrganizationRepository,
    PolicyRepository,
    RiskAssessmentRepository,
    ToolRepository,
    UserRepository,
)
from app.domain.severity import severity_from_score
from app.infrastructure.db import Database

# Minimum score floor per severity band, used by the risk filter.
_RISK_FLOOR: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 25,
    RiskLevel.HIGH: 50,
    RiskLevel.CRITICAL: 75,
}


def _dumps(value: Any) -> str:
    return json.dumps(value, default=str)


class _Base:
    def __init__(self, db: Database) -> None:
        self._db = db

    @property
    def _c(self) -> sqlite3.Connection:
        return self._db.conn

    def _write(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._db.lock:
            self._c.execute(sql, params)
            self._c.commit()


class SqliteOrganizationRepository(_Base, OrganizationRepository):
    def add(self, org: Organization) -> None:
        self._write(
            "INSERT OR REPLACE INTO organizations (id, name, slug, created_at) VALUES (?,?,?,?)",
            (org.id, org.name, org.slug, org.created_at.isoformat()),
        )

    def get(self, org_id: str) -> Organization | None:
        row = self._c.execute("SELECT * FROM organizations WHERE id=?", (org_id,)).fetchone()
        return Organization.model_validate(dict(row)) if row else None

    def get_current(self) -> Organization | None:
        row = self._c.execute("SELECT * FROM organizations ORDER BY created_at LIMIT 1").fetchone()
        return Organization.model_validate(dict(row)) if row else None


class SqliteUserRepository(_Base, UserRepository):
    def add(self, user: User) -> None:
        self._write(
            "INSERT OR REPLACE INTO users (id, organization_id, name, email, role, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (user.id, user.organization_id, user.name, user.email, user.role.value, user.created_at.isoformat()),
        )

    def get(self, user_id: str) -> User | None:
        row = self._c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return User.model_validate(dict(row)) if row else None

    def list(self, organization_id: str | None = None) -> Sequence[User]:
        if organization_id:
            rows = self._c.execute(
                "SELECT * FROM users WHERE organization_id=? ORDER BY created_at", (organization_id,)
            ).fetchall()
        else:
            rows = self._c.execute("SELECT * FROM users ORDER BY created_at").fetchall()
        return [User.model_validate(dict(r)) for r in rows]


_AGENT_COLUMNS = (
    "id, organization_id, name, description, owner_id, department, status, autonomy_level, "
    "risk_score, current_version, runtime, framework, model_provider, model_name, created_at, updated_at"
)


class SqliteAgentRepository(_Base, AgentRepository):
    def _params(self, a: Agent) -> tuple[Any, ...]:
        return (
            a.id, a.organization_id, a.name, a.description, a.owner_id, a.department,
            a.status.value, a.autonomy_level.value, a.risk_score, a.current_version,
            a.runtime, a.framework, a.model_provider, a.model_name,
            a.created_at.isoformat(), a.updated_at.isoformat(),
        )

    def add(self, agent: Agent) -> None:
        self._write(
            f"INSERT OR REPLACE INTO agents ({_AGENT_COLUMNS}) VALUES ({','.join('?' * 16)})",
            self._params(agent),
        )

    def update(self, agent: Agent) -> None:
        self.add(agent)  # INSERT OR REPLACE upserts by primary key.

    def get(self, agent_id: str) -> Agent | None:
        row = self._c.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
        return Agent.model_validate(dict(row)) if row else None

    def list(self, query: AgentQuery | None = None) -> Sequence[Agent]:
        query = query or AgentQuery()
        clauses: list[str] = []
        params: list[Any] = []
        if query.status:
            clauses.append("status = ?")
            params.append(query.status)
        if query.department:
            clauses.append("department = ?")
            params.append(query.department)
        if query.risk is not None:
            clauses.append("risk_score >= ?")
            params.append(_RISK_FLOOR[query.risk])
        if query.search:
            clauses.append("(LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(department) LIKE ?)")
            needle = f"%{query.search.lower()}%"
            params.extend([needle, needle, needle])

        sql = "SELECT * FROM agents"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY risk_score DESC, name ASC"
        if query.limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])

        rows = self._c.execute(sql, tuple(params)).fetchall()
        return [Agent.model_validate(dict(r)) for r in rows]

    def count_total(self) -> int:
        row = self._c.execute("SELECT COUNT(*) AS n FROM agents").fetchone()
        return int(row["n"])

    def departments(self) -> Sequence[str]:
        rows = self._c.execute("SELECT DISTINCT department FROM agents ORDER BY department").fetchall()
        return [r["department"] for r in rows]


class SqliteAgentVersionRepository(_Base, AgentVersionRepository):
    def _to_model(self, row: sqlite3.Row) -> AgentVersion:
        data = dict(row)
        for field in ("tools", "permissions", "data_sources", "configuration"):
            data[field] = json.loads(data[field])
        return AgentVersion.model_validate(data)

    def add(self, version: AgentVersion) -> None:
        self._write(
            "INSERT OR REPLACE INTO agent_versions "
            "(id, agent_id, version, system_prompt_hash, system_prompt_summary, tools, permissions, "
            "data_sources, model, configuration, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                version.id, version.agent_id, version.version, version.system_prompt_hash,
                version.system_prompt_summary, _dumps(version.tools), _dumps(version.permissions),
                _dumps(version.data_sources), version.model, _dumps(version.configuration),
                version.created_by, version.created_at.isoformat(),
            ),
        )

    def get(self, version_id: str) -> AgentVersion | None:
        row = self._c.execute("SELECT * FROM agent_versions WHERE id=?", (version_id,)).fetchone()
        return self._to_model(row) if row else None

    def list_for_agent(self, agent_id: str) -> list[AgentVersion]:
        rows = self._c.execute(
            "SELECT * FROM agent_versions WHERE agent_id=? ORDER BY created_at", (agent_id,)
        ).fetchall()
        return [self._to_model(r) for r in rows]


class SqliteToolRepository(_Base, ToolRepository):
    def _to_model(self, row: sqlite3.Row) -> Tool:
        data = dict(row)
        data["permissions"] = json.loads(data["permissions"])
        data["metadata"] = json.loads(data["metadata"])
        return Tool.model_validate(data)

    def add(self, tool: Tool) -> None:
        self._write(
            "INSERT OR REPLACE INTO tools (id, name, type, risk_level, description, endpoint, "
            "permissions, metadata) VALUES (?,?,?,?,?,?,?,?)",
            (
                tool.id, tool.name, tool.type.value, tool.risk_level.value, tool.description,
                tool.endpoint, _dumps(tool.permissions), _dumps(tool.metadata),
            ),
        )

    def get(self, tool_id: str) -> Tool | None:
        row = self._c.execute("SELECT * FROM tools WHERE id=?", (tool_id,)).fetchone()
        return self._to_model(row) if row else None

    def list(self) -> Sequence[Tool]:
        rows = self._c.execute("SELECT * FROM tools ORDER BY name").fetchall()
        return [self._to_model(r) for r in rows]


class SqliteDependencyRepository(_Base, DependencyRepository):
    def add(self, dependency: AgentDependency) -> None:
        self._write(
            "INSERT OR REPLACE INTO agent_dependencies "
            "(id, source_agent_id, target_type, target_id, relationship, risk_level) VALUES (?,?,?,?,?,?)",
            (
                dependency.id, dependency.source_agent_id, dependency.target_type.value,
                dependency.target_id, dependency.relationship.value, dependency.risk_level.value,
            ),
        )

    def list_for_agent(self, agent_id: str) -> list[AgentDependency]:
        rows = self._c.execute(
            "SELECT * FROM agent_dependencies WHERE source_agent_id=?", (agent_id,)
        ).fetchall()
        return [AgentDependency.model_validate(dict(r)) for r in rows]


class SqlitePolicyRepository(_Base, PolicyRepository):
    def _to_model(self, row: sqlite3.Row) -> Policy:
        data = dict(row)
        data["condition"] = json.loads(data["condition"])
        data["parameters"] = json.loads(data["parameters"])
        data["enabled"] = bool(data["enabled"])
        return Policy.model_validate(data)

    def add(self, p: Policy) -> None:
        self._write(
            "INSERT OR REPLACE INTO policies (id, name, description, scope, priority, condition, "
            "action, parameters, enabled, created_by, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                p.id, p.name, p.description, p.scope, p.priority, _dumps(p.condition),
                p.action.value, _dumps(p.parameters), int(p.enabled), p.created_by,
                p.created_at.isoformat(), p.updated_at.isoformat(),
            ),
        )

    def update(self, policy: Policy) -> None:
        self.add(policy)

    def get(self, policy_id: str) -> Policy | None:
        row = self._c.execute("SELECT * FROM policies WHERE id=?", (policy_id,)).fetchone()
        return self._to_model(row) if row else None

    def list(self) -> Sequence[Policy]:
        rows = self._c.execute("SELECT * FROM policies ORDER BY priority ASC").fetchall()
        return [self._to_model(r) for r in rows]


class SqliteRiskAssessmentRepository(_Base, RiskAssessmentRepository):
    _COLUMNS = (
        "id, agent_id, agent_version_id, overall_score, severity, pii_score, financial_score, "
        "external_tool_score, privilege_score, autonomy_score, prompt_score, data_score, "
        "drivers, recommended_action, created_at"
    )

    def _to_model(self, row: sqlite3.Row) -> RiskAssessment:
        data = dict(row)
        data["drivers"] = json.loads(data["drivers"])
        return RiskAssessment.model_validate(data)

    def add(self, a: RiskAssessment) -> None:
        self._write(
            f"INSERT OR REPLACE INTO risk_assessments ({self._COLUMNS}) VALUES ({','.join('?' * 15)})",
            (
                a.id, a.agent_id, a.agent_version_id, a.overall_score, a.severity.value,
                a.pii_score, a.financial_score, a.external_tool_score, a.privilege_score,
                a.autonomy_score, a.prompt_score, a.data_score, _dumps(a.drivers),
                a.recommended_action.value, a.created_at.isoformat(),
            ),
        )

    def latest_for_agent(self, agent_id: str) -> RiskAssessment | None:
        row = self._c.execute(
            "SELECT * FROM risk_assessments WHERE agent_id=? ORDER BY rowid DESC LIMIT 1", (agent_id,)
        ).fetchone()
        return self._to_model(row) if row else None

    def list_for_agent(self, agent_id: str) -> Sequence[RiskAssessment]:
        rows = self._c.execute(
            "SELECT * FROM risk_assessments WHERE agent_id=? ORDER BY rowid DESC", (agent_id,)
        ).fetchall()
        return [self._to_model(r) for r in rows]


__all__ = [
    "severity_from_score",
    "SqliteOrganizationRepository",
    "SqliteUserRepository",
    "SqliteAgentRepository",
    "SqliteAgentVersionRepository",
    "SqliteToolRepository",
    "SqliteDependencyRepository",
    "SqlitePolicyRepository",
    "SqliteRiskAssessmentRepository",
]
