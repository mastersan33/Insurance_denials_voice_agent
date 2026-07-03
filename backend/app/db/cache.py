"""
Typed Redis cache layer with TTL, JSON serialization, and cache invalidation.

Usage:
    from backend.app.db.cache import cache

    # Read-through
    data = await cache.get_json("dashboard:stats")
    if data is None:
        data = await expensive_query()
        await cache.set_json("dashboard:stats", data, ttl=30)

    # Invalidate
    await cache.invalidate("dashboard:stats")
    await cache.invalidate_prefix("analytics:")
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── TTL constants ──────────────────────────────────────────────────────────────
DASHBOARD_STATS_TTL = 30          # 30 s — refreshed by real-time events
ANALYTICS_TTL = 300               # 5 min — trends change slowly
HEALTH_TTL = 10                   # 10 s — health endpoint response
SESSION_CONTEXT_TTL = 3600        # 1 h — call billing context per SID


class RedisCache:
    """Thin typed wrapper around the app's Redis singleton."""

    async def _redis(self):
        from backend.app.db.redis import get_redis
        return await get_redis()

    # ── Core primitives ────────────────────────────────────────────────────────

    async def get_json(self, key: str) -> Any | None:
        try:
            r = await self._redis()
            raw = await r.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:
            logger.warning("cache.get_json_error key=%s err=%s", key, exc)
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> bool:
        try:
            r = await self._redis()
            await r.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as exc:
            logger.warning("cache.set_json_error key=%s err=%s", key, exc)
            return False

    async def get_str(self, key: str) -> str | None:
        try:
            r = await self._redis()
            return await r.get(key)
        except Exception:
            return None

    async def set_str(self, key: str, value: str, ttl: int = 60) -> bool:
        try:
            r = await self._redis()
            await r.setex(key, ttl, value)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> None:
        try:
            r = await self._redis()
            await r.delete(key)
        except Exception as exc:
            logger.warning("cache.delete_error key=%s err=%s", key, exc)

    async def invalidate(self, *keys: str) -> None:
        """Delete one or more specific keys."""
        for key in keys:
            await self.delete(key)

    async def invalidate_prefix(self, prefix: str) -> None:
        """Delete all keys starting with prefix (use sparingly — SCAN based)."""
        try:
            r = await self._redis()
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor, match=f"{prefix}*", count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except Exception as exc:
            logger.warning("cache.invalidate_prefix_error prefix=%s err=%s", prefix, exc)

    # ── Distributed lock ───────────────────────────────────────────────────────

    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        """SET NX — returns True if lock was acquired."""
        try:
            r = await self._redis()
            return await r.set(f"lock:{key}", "1", ex=ttl, nx=True) is not None
        except Exception:
            return True  # Fail open (don't block the app)

    async def release_lock(self, key: str) -> None:
        await self.delete(f"lock:{key}")

    # ── Convenience keys ───────────────────────────────────────────────────────

    @staticmethod
    def dashboard_key() -> str:
        return "dashboard:stats"

    @staticmethod
    def analytics_key(method: str, **kwargs) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"analytics:{method}:{params}" if params else f"analytics:{method}"

    @staticmethod
    def billing_context_key(call_sid: str) -> str:
        return f"billing_ctx:{call_sid}"

    @staticmethod
    def health_key() -> str:
        return "health:system"


# Singleton
cache = RedisCache()
