from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer()

# RBAC hierarchy: each role includes all permissions of lower roles
ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 0,
    "operator": 1,
    "supervisor": 2,
    "admin": 3,
}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(minimum_role: str):
    """FastAPI dependency factory that enforces a minimum role level.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role("admin"))])
        async def delete_resource(...):
            ...
    """
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    async def _check(user: CurrentUser) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, -1)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role}' role or higher",
            )
        return user

    return Depends(_check)


def is_admin(user: User) -> bool:
    return ROLE_HIERARCHY.get(user.role, -1) >= ROLE_HIERARCHY["admin"]


def is_supervisor_or_above(user: User) -> bool:
    return ROLE_HIERARCHY.get(user.role, -1) >= ROLE_HIERARCHY["supervisor"]
