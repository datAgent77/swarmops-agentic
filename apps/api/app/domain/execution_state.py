"""Execution state machine.

Transitions are explicit and enforced; any move not in the table raises
``InvalidStateTransition``. Terminal states accept no further transitions.
"""

from __future__ import annotations

from app.domain.enums import ExecutionStatus as S

# Allowed transitions. Anything not listed is rejected.
_TRANSITIONS: dict[S, frozenset[S]] = {
    S.QUEUED: frozenset({S.RUNNING, S.CANCELLED}),
    S.RUNNING: frozenset({S.WAITING_APPROVAL, S.BLOCKED, S.FAILED, S.COMPLETED, S.CANCELLED}),
    S.WAITING_APPROVAL: frozenset({S.RUNNING, S.BLOCKED, S.CANCELLED}),
    S.BLOCKED: frozenset(),
    S.FAILED: frozenset(),
    S.COMPLETED: frozenset(),
    S.CANCELLED: frozenset(),
}

TERMINAL_STATES = frozenset(s for s, nxt in _TRANSITIONS.items() if not nxt)


class InvalidStateTransition(Exception):
    def __init__(self, current: S, target: S) -> None:
        super().__init__(f"Invalid execution transition: {current.value} -> {target.value}")
        self.current = current
        self.target = target


def can_transition(current: S, target: S) -> bool:
    return target in _TRANSITIONS.get(current, frozenset())


def assert_transition(current: S, target: S) -> S:
    """Return the target status if the transition is allowed, else raise."""
    if not can_transition(current, target):
        raise InvalidStateTransition(current, target)
    return target
