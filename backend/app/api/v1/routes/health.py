from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.db.redis import get_redis
from backend.app.db.session import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "outbound-billing-voice-agent"}


@router.get("/health/ready")
async def readiness_check():
    checks: dict[str, bool] = {}

    # Database
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    all_healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ready" if all_healthy else "degraded", "checks": checks},
    )
