from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import CurrentUser
from backend.app.db.redis import get_redis
from backend.app.db.session import get_db
from backend.app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    PasswordChange,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserLogin,
    UserUpdateProfile,
)
from backend.app.services.auth_service import AuthService

router = APIRouter()

_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_WINDOW_SECS = 60


async def _check_login_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:login:{client_ip}"
    try:
        redis = await get_redis()
        attempts = await redis.incr(key)
        if attempts == 1:
            await redis.expire(key, _LOGIN_WINDOW_SECS)
        if attempts > _LOGIN_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {_LOGIN_WINDOW_SECS} seconds.",
                headers={"Retry-After": str(_LOGIN_WINDOW_SECS)},
            )
    except HTTPException:
        raise
    except Exception:
        pass


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(_check_login_rate_limit)],
):
    ip = request.client.host if request.client else None
    return await AuthService(db).login(data.email, data.password, ip_address=ip)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshTokenRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).logout(user.id, data.refresh_token)


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).logout_all(user.id)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).forgot_password(data.email)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).reset_password(data)


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdateProfile,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).update_profile(user, data)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChange,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService(db).change_password(user, data)
