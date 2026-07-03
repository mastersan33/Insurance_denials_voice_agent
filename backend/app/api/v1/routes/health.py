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


@router.get("/health/system")
async def system_metrics():
    """Return CPU, memory, and service-level health metrics."""
    metrics: dict = {}

    # psutil — optional; gracefully absent in some envs
    try:
        import psutil
        metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        metrics["memory_total_mb"] = round(mem.total / 1024 / 1024, 1)
        metrics["memory_used_mb"] = round(mem.used / 1024 / 1024, 1)
        metrics["memory_percent"] = mem.percent
        disk = psutil.disk_usage("/")
        metrics["disk_total_gb"] = round(disk.total / 1024 / 1024 / 1024, 1)
        metrics["disk_used_gb"] = round(disk.used / 1024 / 1024 / 1024, 1)
        metrics["disk_percent"] = disk.percent
    except ImportError:
        metrics["psutil"] = "not_installed"

    # DB check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        metrics["database"] = True
    except Exception:
        metrics["database"] = False

    # Redis ping
    try:
        redis = await get_redis()
        await redis.ping()
        metrics["redis"] = True
        info = await redis.info("memory")
        metrics["redis_used_memory_mb"] = round(info.get("used_memory", 0) / 1024 / 1024, 1)
    except Exception:
        metrics["redis"] = False

    # Active WS connections
    try:
        from backend.app.websocket.manager import ws_manager
        metrics["active_ws_connections"] = ws_manager.connection_count
    except Exception:
        metrics["active_ws_connections"] = 0

    return metrics

