"""Human-in-the-loop approval workflow.

Backend is the source of truth for authority: the actor's persona must actually
hold the role the approval requests. Approvals are idempotent (approving twice is
safe), and the deferred execution resumes exactly once — when every required
approval is granted. A rejection terminally blocks the execution.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.execution_service import block_execution, resume_execution
from app.domain.enums import ApprovalStatus
from app.domain.models import ApprovalRequest
from app.infrastructure.container import RepositoryContainer


class ApprovalNotFound(Exception):
    pass


class WrongRole(Exception):
    """Actor persona does not hold the role this approval requires."""


def _now() -> datetime:
    return datetime.now(UTC)


def _authorize(container: RepositoryContainer, approval: ApprovalRequest, actor_user_id: str) -> None:
    user = container.users.get(actor_user_id)
    if user is None or user.role != approval.requested_from_role:
        raise WrongRole(
            f"Actor '{actor_user_id}' may not act on an approval requiring "
            f"{approval.requested_from_role.value}"
        )


def approve(container: RepositoryContainer, approval_id: str, actor_user_id: str) -> ApprovalRequest:
    approval = container.approvals.get(approval_id)
    if approval is None:
        raise ApprovalNotFound(approval_id)
    if approval.status is not ApprovalStatus.PENDING:
        return approval  # idempotent: double approval is safe

    _authorize(container, approval, actor_user_id)

    approval.status = ApprovalStatus.APPROVED
    approval.resolved_at = _now()
    approval.resolved_by = actor_user_id
    container.approvals.update(approval)

    siblings = container.approvals.list_for_execution(approval.execution_id)
    if all(s.status is ApprovalStatus.APPROVED for s in siblings):
        execution = container.executions.get(approval.execution_id)
        if execution is not None:
            resume_execution(container, execution)  # runs deferred actions exactly once
    return approval


def reject(container: RepositoryContainer, approval_id: str, actor_user_id: str) -> ApprovalRequest:
    approval = container.approvals.get(approval_id)
    if approval is None:
        raise ApprovalNotFound(approval_id)
    if approval.status is not ApprovalStatus.PENDING:
        return approval  # idempotent

    _authorize(container, approval, actor_user_id)

    approval.status = ApprovalStatus.REJECTED
    approval.resolved_at = _now()
    approval.resolved_by = actor_user_id
    container.approvals.update(approval)

    # Any remaining pending approvals are moot; expire them and block the execution.
    for sibling in container.approvals.list_for_execution(approval.execution_id):
        if sibling.status is ApprovalStatus.PENDING:
            sibling.status = ApprovalStatus.EXPIRED
            sibling.resolved_at = _now()
            container.approvals.update(sibling)

    execution = container.executions.get(approval.execution_id)
    if execution is not None:
        block_execution(container, execution, f"blocked: approval rejected by {actor_user_id}")
    return approval
