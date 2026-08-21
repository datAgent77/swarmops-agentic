"""Policy CRUD and deterministic evaluation endpoints."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import EvaluateRequest, PolicyCreate, PolicyDecisionOut, PolicyUpdate
from app.domain.models import Policy
from app.domain.policy_engine import (
    PolicyConditionError,
    evaluate_policies,
    validate_condition,
)
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


def _slug(name: str) -> str:
    return "policy-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _validate(condition: dict) -> None:
    try:
        validate_condition(condition)
    except PolicyConditionError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid policy condition: {exc}") from exc


@router.get("", response_model=list[Policy])
async def list_policies(container: RepositoryContainer = Depends(get_container)) -> list[Policy]:
    return list(container.policies.list())


@router.post("", response_model=Policy, status_code=201)
async def create_policy(
    body: PolicyCreate,
    container: RepositoryContainer = Depends(get_container),
) -> Policy:
    _validate(body.condition)
    now = datetime.now(UTC)
    policy = Policy(
        id=_slug(body.name), name=body.name, description=body.description, scope=body.scope,
        priority=body.priority, condition=body.condition, action=body.action,
        parameters=body.parameters, enabled=body.enabled, created_by=body.created_by,
        created_at=now, updated_at=now,
    )
    container.policies.add(policy)
    return policy


@router.put("/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    container: RepositoryContainer = Depends(get_container),
) -> Policy:
    existing = container.policies.get(policy_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found")
    patch = body.model_dump(exclude_unset=True)
    if "condition" in patch:
        _validate(patch["condition"])
    updated = existing.model_copy(update={**patch, "updated_at": datetime.now(UTC)})
    container.policies.update(updated)
    return updated


@router.post("/evaluate", response_model=PolicyDecisionOut)
async def evaluate(
    body: EvaluateRequest,
    container: RepositoryContainer = Depends(get_container),
) -> PolicyDecisionOut:
    decision = evaluate_policies(list(container.policies.list()), body.context)
    return PolicyDecisionOut(
        matched=decision.matched, action=decision.action, policy_id=decision.policy_id,
        policy_name=decision.policy_name, required_roles=decision.required_roles,
        reason=decision.reason,
    )
