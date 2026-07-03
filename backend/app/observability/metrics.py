"""
Prometheus metrics endpoint and instrumentation.

Exposes /metrics for Prometheus scraping.

Metrics tracked:
- http_requests_total{method, path, status}
- http_request_duration_seconds{method, path}
- active_websocket_connections
- call_pipeline_duration_seconds
- llm_response_duration_seconds
- stt_duration_seconds
- tts_duration_seconds
- redis_cache_hits_total
- redis_cache_misses_total
"""
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ── Lazy import prometheus_client (optional dep) ───────────────────────────────
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    _ENABLED = True

    # HTTP metrics
    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    HTTP_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration",
        ["method", "path"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    )

    # WebSocket
    WS_CONNECTIONS = Gauge(
        "active_websocket_connections",
        "Number of active WebSocket connections",
    )

    # AI pipeline
    CALL_PIPELINE_DURATION = Histogram(
        "call_pipeline_duration_seconds",
        "End-to-end call pipeline duration (STT+LLM+TTS)",
        buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0],
    )
    LLM_DURATION = Histogram(
        "llm_response_duration_seconds",
        "LLM response time",
        buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    )
    STT_DURATION = Histogram(
        "stt_duration_seconds",
        "Speech-to-text duration",
        buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    )
    TTS_DURATION = Histogram(
        "tts_duration_seconds",
        "Text-to-speech duration",
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    )

    # Cache
    CACHE_HITS = Counter("redis_cache_hits_total", "Redis cache hits", ["key_prefix"])
    CACHE_MISSES = Counter("redis_cache_misses_total", "Redis cache misses", ["key_prefix"])

    # Business
    CALLS_STARTED = Counter("calls_started_total", "Total outbound calls started")
    CALLS_COMPLETED = Counter("calls_completed_total", "Total calls completed successfully")
    CALLS_FAILED = Counter("calls_failed_total", "Total calls failed")
    HANDOFFS = Counter("human_handoffs_total", "Total AI → human handoffs")

except ImportError:
    _ENABLED = False


# ── Middleware ─────────────────────────────────────────────────────────────────

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records HTTP request count and duration for every non-metrics request."""

    # Paths to skip (health + metrics themselves)
    _SKIP = {"/metrics", "/api/v1/health", "/health/ready"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _ENABLED or request.url.path in self._SKIP:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        # Normalize path params to avoid high-cardinality labels
        path = _normalize_path(request.url.path)
        HTTP_REQUESTS.labels(method=request.method, path=path, status=response.status_code).inc()
        HTTP_DURATION.labels(method=request.method, path=path).observe(elapsed)

        return response


def _normalize_path(path: str) -> str:
    """Replace UUIDs and IDs in paths to avoid unbounded label cardinality."""
    import re
    # Replace UUIDs
    path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{id}", path)
    # Replace numeric IDs
    path = re.sub(r"/\d+", "/{id}", path)
    return path


# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    if not _ENABLED:
        return PlainTextResponse("# prometheus_client not installed\n", media_type="text/plain")
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── Convenience context managers for AI pipeline timing ───────────────────────

@asynccontextmanager
async def track_llm() -> AsyncGenerator[None, None]:
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    yield
    LLM_DURATION.observe(time.perf_counter() - start)


@asynccontextmanager
async def track_stt() -> AsyncGenerator[None, None]:
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    yield
    STT_DURATION.observe(time.perf_counter() - start)


@asynccontextmanager
async def track_tts() -> AsyncGenerator[None, None]:
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    yield
    TTS_DURATION.observe(time.perf_counter() - start)


def record_call_started() -> None:
    if _ENABLED:
        CALLS_STARTED.inc()


def record_call_completed() -> None:
    if _ENABLED:
        CALLS_COMPLETED.inc()


def record_call_failed() -> None:
    if _ENABLED:
        CALLS_FAILED.inc()


def record_handoff() -> None:
    if _ENABLED:
        HANDOFFS.inc()


def ws_connected() -> None:
    if _ENABLED:
        WS_CONNECTIONS.inc()


def ws_disconnected() -> None:
    if _ENABLED:
        WS_CONNECTIONS.dec()
