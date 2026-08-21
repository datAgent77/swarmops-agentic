"""Execution orchestration.

Creates an execution, walks it through the state machine, and runs requested tool
calls via the safe (mock) tool layer. Two guarantees enforced here:

- A QUARANTINED agent can never start an execution.
- A state-changing tool call with a previously seen idempotency key is replayed from
  the prior result — it never executes twice (no duplicate refunds).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.application.audit_service import record_event
from app.domain.enums import AgentStatus, ExecutionStatus, PolicyAction
from app.domain.execution_state import assert_transition
from app.domain.models import Execution, ToolCall
from app.domain.policy_engine import PolicyDecision, evaluate_policies
from app.infrastructure.container import RepositoryContainer
from app.infrastructure.events import (
    APPROVAL_REQUESTED,
    EXECUTION_COMPLETED,
    TOOL_CALL_COMPLETED,
    DomainEvent,
)
from app.infrastructure.tool_layer import KNOWN_TOOLS, ToolNotFound, is_state_changing, run_tool


def _audit(
    container: RepositoryContainer,
    execution: Execution,
    action: str,
    *,
    resource_type: str = "execution",
    resource_id: str | None = None,
    decision: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append an audit event correlated to the execution's trace."""
    record_event(
        container, action=action, resource_type=resource_type,
        resource_id=resource_id or execution.id, decision=decision, reason=reason,
        metadata=metadata, trace_id=execution.trace_id,
    )


class ExecutionAgentNotFound(Exception):
    pass


class ExecutionBlocked(Exception):
    """Agent may not start an execution (e.g. quarantined)."""


class UnknownTool(Exception):
    pass


@dataclass(frozen=True)
class ToolCallRequest:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None


def _now() -> datetime:
    return datetime.now(UTC)


def _risk_context(container: RepositoryContainer, agent_id: str) -> str:
    latest = container.risk_assessments.latest_for_agent(agent_id)
    if latest is not None:
        return f"{latest.severity.value} ({latest.overall_score})"
    agent = container.agents.get(agent_id)
    return f"{agent.severity.value} ({agent.risk_score})" if agent else "UNKNOWN"


def _version_id(container: RepositoryContainer, agent_id: str, label: str) -> str | None:
    for v in container.agent_versions.list_for_agent(agent_id):
        if v.version == label:
            return v.id
    return None


def _run_one(container: RepositoryContainer, execution: Execution, req: ToolCallRequest) -> tuple[ToolCall, dict]:
    started = _now()
    replay = False
    if is_state_changing(req.tool) and req.idempotency_key:
        prior = container.tool_calls.find_by_idempotency_key(req.idempotency_key)
        if prior is not None:
            replay = True
            result_summary = f"idempotent-replay: {prior.result_summary}"
            result = json.loads(prior.result_summary)
    if not replay:
        result = run_tool(req.tool, req.arguments, req.idempotency_key)
        result_summary = json.dumps(result)
    completed = _now()

    call = ToolCall(
        id=f"tc-{uuid.uuid4().hex[:12]}", execution_id=execution.id, tool_id=req.tool,
        arguments_summary=json.dumps(req.arguments), result_summary=result_summary,
        policy_decision="ALLOW", started_at=started, completed_at=completed,
        duration_ms=max(0, int((completed - started).total_seconds() * 1000)),
        idempotency_key=req.idempotency_key,
    )
    container.tool_calls.add(call)
    _audit(container, execution, "tool_call.completed", resource_type="tool_call",
           resource_id=call.id, reason=f"{req.tool}{' (replay)' if replay else ''}",
           metadata={"tool": req.tool, "duration_ms": call.duration_ms})
    container.event_bus.publish(DomainEvent(
        TOOL_CALL_COMPLETED, {"execution_id": execution.id, "tool": req.tool, "replay": replay}))
    return call, result


def _governance_context(tool_calls: list[ToolCallRequest]) -> dict[str, Any]:
    """Build the policy-evaluation context from the requested tool calls.

    Refund amounts surface as ``refund`` so the refund policies apply; other
    arguments are merged through as-is.
    """
    context: dict[str, Any] = {}
    for tc in tool_calls:
        context.update(tc.arguments)
        if tc.tool == "execute_refund" and "amount" in tc.arguments:
            context["refund"] = tc.arguments["amount"]
    return context


def start_execution(
    container: RepositoryContainer,
    agent_id: str,
    input_summary: str,
    tool_calls: list[ToolCallRequest],
) -> Execution:
    agent = container.agents.get(agent_id)
    if agent is None:
        raise ExecutionAgentNotFound(agent_id)
    if agent.status is AgentStatus.QUARANTINED:
        raise ExecutionBlocked(f"Agent '{agent_id}' is quarantined and cannot start executions")

    unknown = [tc.tool for tc in tool_calls if tc.tool not in KNOWN_TOOLS]
    if unknown:
        raise UnknownTool(", ".join(unknown))

    started = _now()
    execution = Execution(
        id=f"exec-{uuid.uuid4().hex[:12]}", agent_id=agent_id,
        agent_version_id=_version_id(container, agent_id, agent.current_version),
        status=ExecutionStatus.QUEUED, input_summary=input_summary,
        risk_context=_risk_context(container, agent_id), started_at=started,
        trace_id=f"trace-{uuid.uuid4().hex[:16]}",
        estimated_cost=round(0.001 + 0.0005 * len(tool_calls), 4),
    )
    container.executions.add(execution)
    execution.status = assert_transition(execution.status, ExecutionStatus.RUNNING)
    container.executions.update(execution)
    _audit(container, execution, "execution.started", reason=input_summary,
           metadata={"agent_id": agent_id})

    # Deterministic governance gate.
    decision = evaluate_policies(list(container.policies.list()), _governance_context(tool_calls))
    _audit(container, execution, "policy.evaluated", decision=decision.action.value,
           reason=decision.policy_name or "no policy matched")

    if decision.action in (PolicyAction.DENY, PolicyAction.QUARANTINE):
        execution.status = assert_transition(execution.status, ExecutionStatus.BLOCKED)
        execution.output_summary = f"blocked by policy: {decision.policy_name} ({decision.action.value})"
        _audit(container, execution, "execution.blocked", decision=decision.action.value,
               reason=execution.output_summary)
        _finalize(container, execution, started)
        return execution

    if decision.action is PolicyAction.REQUIRE_APPROVAL:
        _open_approvals(container, execution, tool_calls, decision)
        execution.status = assert_transition(execution.status, ExecutionStatus.WAITING_APPROVAL)
        _audit(container, execution, "execution.waiting_approval", reason=decision.policy_name)
        execution.pending_actions = [
            {"tool": tc.tool, "arguments": tc.arguments, "idempotency_key": tc.idempotency_key}
            for tc in tool_calls
        ]
        execution.output_summary = f"waiting for approval: {decision.policy_name}"
        container.executions.update(execution)
        return execution

    # ALLOW / LOG_ONLY / REDACT / no match → run now.
    return _run_and_complete(container, execution, tool_calls, started)


def _open_approvals(
    container: RepositoryContainer,
    execution: Execution,
    tool_calls: list[ToolCallRequest],
    decision: PolicyDecision,
) -> None:
    from app.domain.enums import ApprovalStatus, Role
    from app.domain.models import ApprovalRequest

    context = _governance_context(tool_calls)
    for i, role in enumerate(decision.required_roles):
        approval = ApprovalRequest(
            id=f"appr-{uuid.uuid4().hex[:12]}", execution_id=execution.id,
            policy_id=decision.policy_id, requested_from_role=Role(role), sequence=i + 1,
            status=ApprovalStatus.PENDING, reason=decision.reason, context=context,
            created_at=_now(),
        )
        container.approvals.add(approval)
        _audit(container, execution, "approval.requested", resource_type="approval",
               resource_id=approval.id, reason=f"requires {role}")
        container.event_bus.publish(DomainEvent(
            APPROVAL_REQUESTED, {"execution_id": execution.id, "approval_id": approval.id, "role": role}))


def _run_and_complete(
    container: RepositoryContainer,
    execution: Execution,
    tool_calls: list[ToolCallRequest],
    started: datetime,
) -> Execution:
    outputs: list[dict] = []
    try:
        for req in tool_calls:
            _, result = _run_one(container, execution, req)
            outputs.append(result)
    except ToolNotFound as exc:  # defensive; validated earlier
        execution.status = assert_transition(execution.status, ExecutionStatus.FAILED)
        execution.output_summary = f"tool error: {exc}"
        _audit(container, execution, "execution.failed", reason=execution.output_summary)
        _finalize(container, execution, started)
        return execution

    execution.status = assert_transition(execution.status, ExecutionStatus.COMPLETED)
    execution.output_summary = json.dumps(outputs[-1]) if outputs else "no tool calls"
    execution.pending_actions = []
    _audit(container, execution, "execution.completed",
           metadata={"tool_calls": len(tool_calls), "cost": execution.estimated_cost})
    container.event_bus.publish(DomainEvent(
        EXECUTION_COMPLETED, {"execution_id": execution.id, "agent_id": execution.agent_id}))
    _finalize(container, execution, started)
    return execution


def resume_execution(container: RepositoryContainer, execution: Execution) -> Execution:
    """Resume a WAITING_APPROVAL execution once all approvals are granted.

    Guarded so the deferred actions run exactly once: if the execution is no longer
    WAITING_APPROVAL, this is a no-op.
    """
    if execution.status is not ExecutionStatus.WAITING_APPROVAL:
        return execution
    execution.status = assert_transition(execution.status, ExecutionStatus.RUNNING)
    container.executions.update(execution)
    _audit(container, execution, "execution.resumed", reason="all approvals granted")
    requests = [
        ToolCallRequest(tool=a["tool"], arguments=a.get("arguments", {}),
                        idempotency_key=a.get("idempotency_key"))
        for a in execution.pending_actions
    ]
    started = execution.started_at or _now()
    return _run_and_complete(container, execution, requests, started)


def block_execution(container: RepositoryContainer, execution: Execution, reason: str) -> Execution:
    """Terminally block a WAITING_APPROVAL execution (e.g. an approval was rejected)."""
    if execution.status is not ExecutionStatus.WAITING_APPROVAL:
        return execution
    execution.status = assert_transition(execution.status, ExecutionStatus.BLOCKED)
    execution.output_summary = reason
    execution.pending_actions = []
    _audit(container, execution, "execution.blocked", decision="BLOCKED", reason=reason)
    _finalize(container, execution, execution.started_at or _now())
    return execution


def _finalize(container: RepositoryContainer, execution: Execution, started: datetime) -> None:
    completed = _now()
    execution.completed_at = completed
    execution.duration_ms = max(0, int((completed - started).total_seconds() * 1000))
    container.executions.update(execution)
