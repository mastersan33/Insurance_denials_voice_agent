"""WebSocket endpoint for live dashboard updates.

Clients connect to /ws/dashboard?token=<JWT> and receive periodic
stat pushes. This removes the need for polling on the frontend.
"""
import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.config.logging import get_logger
from backend.app.core.security import decode_access_token
from backend.app.db.session import async_session_factory
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()
logger = get_logger(__name__)

_PUSH_INTERVAL_SECONDS = 10

# Registry of active dashboard connections: connection_id → WebSocket
_dashboard_clients: dict[str, WebSocket] = {}


async def _push_stats(ws: WebSocket) -> None:
    """Fetch dashboard stats and push to a single client."""
    try:
        async with async_session_factory() as db:
            service = DashboardService(db)
            stats = await service.get_stats()
        await ws.send_text(json.dumps({"type": "stats", "data": stats.model_dump()}))
    except Exception as e:
        logger.error("dashboard_ws_push_error", error=str(e))


async def broadcast_stats() -> None:
    """Broadcast dashboard stats to all connected dashboard clients.

    Called from call event handlers (trigger, status callback) to push
    updates immediately when something meaningful changes.
    """
    if not _dashboard_clients:
        return
    try:
        async with async_session_factory() as db:
            service = DashboardService(db)
            stats = await service.get_stats()
        payload = json.dumps({"type": "stats", "data": stats.model_dump()})
        dead: list[str] = []
        for cid, ws in list(_dashboard_clients.items()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(cid)
        for cid in dead:
            _dashboard_clients.pop(cid, None)
    except Exception as e:
        logger.error("dashboard_broadcast_error", error=str(e))


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Live dashboard WebSocket.  Authenticate via ?token=<JWT>."""
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    connection_id = payload.get("sub", "anon")
    await websocket.accept()
    _dashboard_clients[connection_id] = websocket
    logger.info("dashboard_ws_connected", user_id=connection_id)

    try:
        # Send initial stats immediately on connect
        await _push_stats(websocket)

        # Push on interval; also handle pings from client
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=_PUSH_INTERVAL_SECONDS)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await _push_stats(websocket)
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("dashboard_ws_error", user_id=connection_id, error=str(e))
    finally:
        _dashboard_clients.pop(connection_id, None)
        logger.info("dashboard_ws_disconnected", user_id=connection_id)

