"""Deterministic policy engine.

Evaluates JSON-declared conditions against a context dictionary. There is **no
`eval`, `exec`, or dynamic code path** — operators are a fixed whitelist and every
value is treated as inert data. Conditions are validated up front so a malformed or
unknown-operator policy is rejected, never silently ignored.

Condition grammar (recursive):

    group  = {"all": [condition, ...]} | {"any": [condition, ...]}
    leaf   = {"field": <str>, "op": <operator>, "value": <json>}
    operator in {eq, neq, gt, gte, lt, lte, in, contains, exists}
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.domain.enums import PolicyAction

VALID_OPERATORS = frozenset({"eq", "neq", "gt", "gte", "lt", "lte", "in", "contains", "exists"})


class PolicyConditionError(ValueError):
    """Raised when a condition tree is structurally invalid."""


# --- Validation ----------------------------------------------------------

def validate_condition(node: Any) -> None:
    if not isinstance(node, dict):
        raise PolicyConditionError("condition must be an object")

    if "all" in node or "any" in node:
        key = "all" if "all" in node else "any"
        if set(node) != {key}:
            raise PolicyConditionError(f"'{key}' group must be the only key")
        children = node[key]
        if not isinstance(children, list) or not children:
            raise PolicyConditionError(f"'{key}' must be a non-empty list")
        for child in children:
            validate_condition(child)
        return

    # Leaf.
    if "op" not in node or "field" not in node:
        raise PolicyConditionError("leaf condition requires 'field' and 'op'")
    op = node["op"]
    if op not in VALID_OPERATORS:
        raise PolicyConditionError(f"unknown operator '{op}'")
    if op != "exists" and "value" not in node:
        raise PolicyConditionError(f"operator '{op}' requires 'value'")


# --- Evaluation ----------------------------------------------------------

def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _eval_leaf(field_name: str, op: str, value: Any, context: dict[str, Any]) -> bool:
    present = field_name in context and context[field_name] is not None
    actual = context.get(field_name)

    if op == "exists":
        want = True if value is None else bool(value)
        return present == want
    if op == "eq":
        return actual == value
    if op == "neq":
        return actual != value
    if op in {"gt", "gte", "lt", "lte"}:
        a, b = _num(actual), _num(value)
        if a is None or b is None:
            return False
        return {"gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b}[op]
    if op == "in":
        try:
            return actual in value  # membership in the policy-provided collection
        except TypeError:
            return False
    if op == "contains":
        if isinstance(actual, (str, list, tuple, set, dict)):
            return value in actual  # field is a list/str containing value
        return False
    return False  # unreachable after validation


def evaluate_condition(node: dict[str, Any], context: dict[str, Any]) -> bool:
    if "all" in node:
        return all(evaluate_condition(c, context) for c in node["all"])
    if "any" in node:
        return any(evaluate_condition(c, context) for c in node["any"])
    return _eval_leaf(node["field"], node["op"], node.get("value"), context)


# --- Decision ------------------------------------------------------------

class PolicyLike(Protocol):
    """Structural type for evaluate_policies (satisfied by domain.models.Policy)."""

    id: str
    name: str
    description: str
    priority: int
    condition: dict[str, Any]
    action: PolicyAction
    parameters: dict[str, Any]
    enabled: bool


@dataclass(frozen=True)
class PolicyDecision:
    matched: bool
    action: PolicyAction
    policy_id: str | None
    policy_name: str | None
    required_roles: list[str] = field(default_factory=list)
    reason: str = ""


def evaluate_policies(policies: Iterable[PolicyLike], context: dict[str, Any]) -> PolicyDecision:
    """Return the decision of the first enabled policy (lowest priority number)
    whose condition matches. Defaults to ALLOW when nothing matches."""
    for policy in sorted(policies, key=lambda p: p.priority):
        if not policy.enabled:
            continue
        if evaluate_condition(policy.condition, context):
            roles = list(policy.parameters.get("roles", []))
            return PolicyDecision(
                matched=True, action=policy.action, policy_id=policy.id,
                policy_name=policy.name, required_roles=roles,
                reason=policy.description or policy.name,
            )
    return PolicyDecision(
        matched=False, action=PolicyAction.ALLOW, policy_id=None, policy_name=None,
        reason="No policy matched; default allow",
    )
