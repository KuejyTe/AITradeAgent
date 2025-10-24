from __future__ import annotations

import asyncio
import json
from typing import List

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import app_logger
from app.monitoring.metrics import websocket_connections


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        websocket_connections.set(len(self.active_connections))
        app_logger.info(
            "WebSocket connected",
            active_connections=len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        websocket_connections.set(len(self.active_connections))
        app_logger.info(
            "WebSocket disconnected",
            active_connections=len(self.active_connections),
        )

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in list(self.active_connections):
            await connection.send_text(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            response = {
                "type": "echo",
                "data": payload,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await manager.send_personal_message(json.dumps(response), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(json.dumps({"message": "Client disconnected"}))
    except Exception as exc:  # pragma: no cover - defensive
        app_logger.error("WebSocket error", error=str(exc))
        manager.disconnect(websocket)
    finally:
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
