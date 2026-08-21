"""Observability read models: fleet metrics overview and trace reconstruction.

The audit trail is trace-correlated (every execution event carries the execution's
``trace_id``), so a full end-to-end reasoning-chain trace is reconstructed from
persisted data — no external tracing backend required for the demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import get_settings
from app.domain.enums import ExecutionStatus
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.telemetry import tracing_backend


@dataclass
class Overview:
    total_executions: int
    by_status: dict[str, int]
    completed: int
    failed: int
    blocked: int
    error_rate: float
    avg_latency_ms: float
    policy_violations: int
    estimated_spend: float
    token_usage: int | None
    avg_approval_wait_ms: float
    audit_event_count: int
    telemetry_backend: str


@dataclass
class TraceStep:
    name: str
    kind: str
    decision: str | None
    reason: str | None
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceResult:
    trace_id: str
    execution_id: str | None
    status: str | None
    duration_ms: int | None
    steps: list[TraceStep]


def compute_overview(container: RepositoryContainer) -> Overview:
    executions = list(container.executions.list())
    total = len(executions)
    by_status: dict[str, int] = {}
    for e in executions:
        by_status[e.status.value] = by_status.get(e.status.value, 0) + 1

    completed = by_status.get(ExecutionStatus.COMPLETED.value, 0)
    failed = by_status.get(ExecutionStatus.FAILED.value, 0)
    blocked = by_status.get(ExecutionStatus.BLOCKED.value, 0)
    error_rate = round((failed + blocked) / total, 3) if total else 0.0

    latencies = [e.duration_ms for e in executions
                 if e.status is ExecutionStatus.COMPLETED and e.duration_ms is not None]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
    estimated_spend = round(sum(e.estimated_cost for e in executions), 4)

    audit = list(container.audit_events.list())
    policy_violations = sum(
        1 for a in audit if a.action == "policy.evaluated" and a.decision in {"DENY", "QUARANTINE"}
    )

    waits = [
        (a.resolved_at - a.created_at).total_seconds() * 1000
        for a in container.approvals.list()
        if a.resolved_at is not None
    ]
    avg_wait = round(sum(waits) / len(waits), 1) if waits else 0.0

    return Overview(
        total_executions=total, by_status=by_status, completed=completed, failed=failed,
        blocked=blocked, error_rate=error_rate, avg_latency_ms=avg_latency,
        policy_violations=policy_violations, estimated_spend=estimated_spend,
        token_usage=None,  # not tracked yet — reported honestly as unavailable
        avg_approval_wait_ms=avg_wait, audit_event_count=len(audit),
        telemetry_backend=tracing_backend(get_settings()),
    )


def build_trace(container: RepositoryContainer, trace_id: str) -> TraceResult:
    execution = next((e for e in container.executions.list() if e.trace_id == trace_id), None)
    events = list(container.audit_events.list_for_trace(trace_id))

    steps: list[TraceStep] = []
    if execution is not None:
        steps.append(TraceStep(
            name="execution", kind="root", decision=execution.status.value,
            reason=execution.input_summary,
            timestamp=execution.started_at.isoformat() if execution.started_at else "",
            metadata={"agent_id": execution.agent_id, "duration_ms": execution.duration_ms},
        ))
    for ev in events:
        kind = "tool" if ev.action.startswith("tool_call") else "event"
        steps.append(TraceStep(
            name=ev.action, kind=kind, decision=ev.decision, reason=ev.reason,
            timestamp=ev.timestamp.isoformat(), metadata=ev.metadata,
        ))

    return TraceResult(
        trace_id=trace_id,
        execution_id=execution.id if execution else None,
        status=execution.status.value if execution else None,
        duration_ms=execution.duration_ms if execution else None,
        steps=steps,
    )
