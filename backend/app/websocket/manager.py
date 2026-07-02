import asyncio
from collections.abc import Callable

from fastapi import WebSocket

from backend.app.config.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._handlers: dict[str, Callable] = {}

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self._connections[connection_id] = websocket
        logger.info("ws_connected", connection_id=connection_id)

    async def disconnect(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)
        logger.info("ws_disconnected", connection_id=connection_id)

    async def send_json(self, connection_id: str, data: dict) -> None:
        ws = self._connections.get(connection_id)
        if ws:
            await ws.send_json(data)

    async def send_text(self, connection_id: str, text: str) -> None:
        ws = self._connections.get(connection_id)
        if ws:
            await ws.send_text(text)

    async def send_bytes(self, connection_id: str, data: bytes) -> None:
        ws = self._connections.get(connection_id)
        if ws:
            await ws.send_bytes(data)

    async def broadcast(self, data: dict) -> None:
        tasks = [ws.send_json(data) for ws in self._connections.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_active_connections(self) -> list[str]:
        return list(self._connections.keys())

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = ConnectionManager()
