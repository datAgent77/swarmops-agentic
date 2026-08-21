"""User (persona) endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.api.schemas import UserListResponse
from app.infrastructure.container import RepositoryContainer

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    container: RepositoryContainer = Depends(get_container),
) -> UserListResponse:
    return UserListResponse(items=container.users.list())
