"""User management endpoints — admin/supervisor only."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser, require_role
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserResponse

router = APIRouter()

_VALID_ROLES = {"admin", "supervisor", "operator", "viewer"}


class UserRoleUpdate(BaseModel):
    role: str
    is_active: bool | None = None


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    _: Annotated[None, require_role("supervisor")] = None,
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = list(result.scalars().all())
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserRoleUpdate,
    current: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_role("admin")] = None,
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User", user_id)

    if data.role not in _VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role must be one of {sorted(_VALID_ROLES)}")

    # Prevent admin from demoting themselves
    if user_id == current.id and data.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role")

    update_fields: dict = {"role": data.role}
    if data.is_active is not None:
        update_fields["is_active"] = data.is_active
    user = await repo.update(user, update_fields)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: str,
    current: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, require_role("admin")] = None,
):
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account")
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User", user_id)
    await repo.update(user, {"is_active": False})
