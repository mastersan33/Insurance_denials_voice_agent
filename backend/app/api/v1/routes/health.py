from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.db.redis import get_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "outbound-billing-voice-agent"}


@router.get("/health/ready")
async def readiness_check():
    checks = {}
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
