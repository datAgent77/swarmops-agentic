"""Append-only audit helper.

A thin recorder used by lifecycle/governance flows. P09 expands this into full
OpenTelemetry-correlated instrumentation with query endpoints; the model and store
are already append-only here.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import AuditActorType
from app.domain.models import AuditEvent
from app.infrastructure.container import RepositoryContainer


def record_event(
    container: RepositoryContainer,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    actor_type: AuditActorType = AuditActorType.SYSTEM,
    actor_id: str | None = None,
    decision: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> AuditEvent:
    org = container.organizations.get_current()
    event = AuditEvent(
        id=f"audit-{uuid.uuid4().hex[:12]}",
        organization_id=org.id if org else "org-unknown",
        actor_type=actor_type, actor_id=actor_id, action=action,
        resource_type=resource_type, resource_id=resource_id, decision=decision,
        reason=reason, metadata=metadata or {}, trace_id=trace_id,
        timestamp=datetime.now(UTC),
    )
    container.audit_events.add(event)
    return event
