"""SQLite database bootstrap.

A deliberately small, dependency-free persistence layer for local development.
Complex fields (lists/dicts) are stored as JSON TEXT. The schema is created on
demand; the repositories in ``repositories_sqlite`` map rows to domain models.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id               TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL,
    name             TEXT NOT NULL,
    email            TEXT NOT NULL,
    role             TEXT NOT NULL,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    id               TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL,
    name             TEXT NOT NULL,
    description      TEXT NOT NULL,
    owner_id         TEXT NOT NULL,
    department       TEXT NOT NULL,
    status           TEXT NOT NULL,
    autonomy_level   TEXT NOT NULL,
    risk_score       INTEGER NOT NULL,
    current_version  TEXT NOT NULL,
    runtime          TEXT NOT NULL,
    framework        TEXT NOT NULL,
    model_provider   TEXT NOT NULL,
    model_name       TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    quarantine_reason TEXT
);

CREATE TABLE IF NOT EXISTS agent_versions (
    id                     TEXT PRIMARY KEY,
    agent_id               TEXT NOT NULL,
    version                TEXT NOT NULL,
    system_prompt_hash     TEXT NOT NULL,
    system_prompt_summary  TEXT NOT NULL,
    tools                  TEXT NOT NULL,
    permissions            TEXT NOT NULL,
    data_sources           TEXT NOT NULL,
    model                  TEXT NOT NULL,
    configuration          TEXT NOT NULL,
    created_by             TEXT NOT NULL,
    created_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tools (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    type         TEXT NOT NULL,
    risk_level   TEXT NOT NULL,
    description  TEXT NOT NULL,
    endpoint     TEXT,
    permissions  TEXT NOT NULL,
    metadata     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_dependencies (
    id               TEXT PRIMARY KEY,
    source_agent_id  TEXT NOT NULL,
    target_type      TEXT NOT NULL,
    target_id        TEXT NOT NULL,
    relationship     TEXT NOT NULL,
    risk_level       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS executions (
    id                TEXT PRIMARY KEY,
    agent_id          TEXT NOT NULL,
    agent_version_id  TEXT,
    status            TEXT NOT NULL,
    input_summary     TEXT NOT NULL,
    output_summary    TEXT,
    risk_context      TEXT,
    started_at        TEXT,
    completed_at      TEXT,
    duration_ms       INTEGER,
    trace_id          TEXT NOT NULL,
    estimated_cost    REAL NOT NULL,
    pending_actions   TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS approvals (
    id                  TEXT PRIMARY KEY,
    execution_id        TEXT NOT NULL,
    policy_id           TEXT,
    requested_from_role TEXT NOT NULL,
    sequence            INTEGER NOT NULL,
    status              TEXT NOT NULL,
    reason              TEXT NOT NULL,
    context             TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    resolved_at         TEXT,
    resolved_by         TEXT
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id                TEXT PRIMARY KEY,
    execution_id      TEXT NOT NULL,
    tool_id           TEXT NOT NULL,
    arguments_summary TEXT NOT NULL,
    result_summary    TEXT NOT NULL,
    policy_decision   TEXT,
    started_at        TEXT NOT NULL,
    completed_at      TEXT NOT NULL,
    duration_ms       INTEGER NOT NULL,
    idempotency_key   TEXT
);

CREATE TABLE IF NOT EXISTS policies (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL,
    scope        TEXT NOT NULL,
    priority     INTEGER NOT NULL,
    condition    TEXT NOT NULL,
    action       TEXT NOT NULL,
    parameters   TEXT NOT NULL,
    enabled      INTEGER NOT NULL,
    created_by   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS change_proposals (
    id                  TEXT PRIMARY KEY,
    agent_id            TEXT NOT NULL,
    base_version        TEXT NOT NULL,
    candidate_version   TEXT NOT NULL,
    change_type         TEXT NOT NULL,
    changes             TEXT NOT NULL,
    old_summary         TEXT NOT NULL,
    new_summary         TEXT NOT NULL,
    performance_before  INTEGER NOT NULL,
    performance_after   INTEGER NOT NULL,
    compliance_before   INTEGER NOT NULL,
    compliance_after    INTEGER NOT NULL,
    decision            TEXT NOT NULL,
    reason              TEXT NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_incidents (
    id                  TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL,
    source              TEXT NOT NULL,
    agent_id            TEXT,
    category            TEXT NOT NULL,
    severity            TEXT NOT NULL,
    action              TEXT NOT NULL,
    input_excerpt       TEXT NOT NULL,
    detected_categories TEXT NOT NULL,
    scanner             TEXT NOT NULL,
    scanner_status      TEXT NOT NULL,
    policy_id           TEXT,
    resolved            INTEGER NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id               TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL,
    actor_type       TEXT NOT NULL,
    actor_id         TEXT,
    action           TEXT NOT NULL,
    resource_type    TEXT NOT NULL,
    resource_id      TEXT NOT NULL,
    decision         TEXT,
    reason           TEXT,
    metadata         TEXT NOT NULL,
    trace_id         TEXT,
    timestamp        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id                 TEXT PRIMARY KEY,
    agent_id           TEXT NOT NULL,
    agent_version_id   TEXT,
    overall_score      INTEGER NOT NULL,
    severity           TEXT NOT NULL,
    pii_score          INTEGER NOT NULL,
    financial_score    INTEGER NOT NULL,
    external_tool_score INTEGER NOT NULL,
    privilege_score    INTEGER NOT NULL,
    autonomy_score     INTEGER NOT NULL,
    prompt_score       INTEGER NOT NULL,
    data_score         INTEGER NOT NULL,
    drivers            TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    created_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_department ON agents(department);
CREATE INDEX IF NOT EXISTS idx_versions_agent ON agent_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_deps_source ON agent_dependencies(source_agent_id);
CREATE INDEX IF NOT EXISTS idx_risk_agent ON risk_assessments(agent_id);
CREATE INDEX IF NOT EXISTS idx_policies_priority ON policies(priority);
CREATE INDEX IF NOT EXISTS idx_toolcalls_exec ON tool_calls(execution_id);
CREATE INDEX IF NOT EXISTS idx_toolcalls_idem ON tool_calls(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_approvals_exec ON approvals(execution_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_type, resource_id);
"""

_ALL_TABLES = (
    "tool_calls",
    "approvals",
    "executions",
    "change_proposals",
    "security_incidents",
    "audit_events",
    "risk_assessments",
    "policies",
    "agent_dependencies",
    "agent_versions",
    "tools",
    "agents",
    "users",
    "organizations",
)


class Database:
    """Thin wrapper around a single shared SQLite connection.

    ``check_same_thread=False`` because FastAPI runs sync handlers in a threadpool;
    a lock serializes writes so the demo stays consistent under light concurrency.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self.lock = threading.Lock()
        self.create_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def create_schema(self) -> None:
        with self.lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def is_empty(self) -> bool:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM organizations").fetchone()
        return int(row["n"]) == 0

    def wipe(self) -> None:
        with self.lock:
            for table in _ALL_TABLES:
                self._conn.execute(f"DELETE FROM {table}")
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()
