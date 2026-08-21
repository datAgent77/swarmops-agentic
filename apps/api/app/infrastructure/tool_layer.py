"""Safe demo tool layer.

Every tool here is a **mock**. Nothing in this module contacts a real external
service. In particular ``execute_refund`` NEVER calls Stripe or any financial
infrastructure — it returns a deterministic demo transaction. Idempotency is
enforced one layer up (execution service) using the tool call's idempotency key.
"""

from __future__ import annotations

from typing import Any

# Tools that change state and therefore must be idempotency-guarded.
STATE_CHANGING: frozenset[str] = frozenset({"execute_refund", "send_email"})

KNOWN_TOOLS: frozenset[str] = frozenset({
    "get_customer", "get_order", "calculate_refund",
    "execute_refund", "send_email", "get_salesforce_case",
})


class ToolNotFound(Exception):
    pass


def is_state_changing(name: str) -> bool:
    return name in STATE_CHANGING


def run_tool(name: str, arguments: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
    """Execute a demo tool and return its (deterministic) result."""
    if name not in KNOWN_TOOLS:
        raise ToolNotFound(name)

    if name == "get_customer":
        cid = arguments.get("customer_id", "cust_demo")
        return {"customer_id": cid, "name": "Demo Customer", "email": "demo@acme.example", "tier": "gold"}

    if name == "get_order":
        return {
            "order_id": arguments.get("order_id", "order_demo"),
            "amount": arguments.get("amount", 650),
            "currency": "USD",
            "status": "delivered",
        }

    if name == "calculate_refund":
        amount = arguments.get("amount", 650)
        return {"amount": amount, "currency": "USD", "breakdown": {"item": amount, "tax": 0}}

    if name == "execute_refund":
        # DEMO ONLY — no Stripe, no real money. Transaction id is stable per key.
        amount = arguments.get("amount", 650)
        suffix = idempotency_key or "adhoc"
        return {"transaction_id": f"demo_refund_{suffix}", "status": "completed", "amount": amount}

    if name == "send_email":
        return {"message_id": f"demo_msg_{arguments.get('to', 'x')}", "status": "sent"}

    if name == "get_salesforce_case":
        return {"case_id": arguments.get("case_id", "case_demo"), "subject": "Refund request", "status": "open"}

    raise ToolNotFound(name)  # unreachable
