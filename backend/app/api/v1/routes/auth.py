from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.redis import get_redis
from backend.app.db.session import get_db
from backend.app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from backend.app.services.auth_service import AuthService

router = APIRouter()

_LOGIN_MAX_ATTEMPTS = 10   # per IP per window
_LOGIN_WINDOW_SECS = 60    # 1-minute rolling window


async def _check_login_rate_limit(request: Request) -> None:
    """Block IPs that exceed 10 failed/attempted logins per minute."""
    client_ip = (request.client.host if request.client else "unknown")
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
        # Redis unavailable — fail open so auth is never blocked by infra issues
        pass


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(_check_login_rate_limit)],
):
    service = AuthService(db)
    return await service.login(data.email, data.password)
