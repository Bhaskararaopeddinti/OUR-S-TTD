"""
OURS TTD — Real-time WebSocket Broadcast Manager
Handles active WebSocket connections and broadcasting JSON updates to connected clients.
Supports both async context and thread-safe sync context.
"""
import json
import logging
import asyncio
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class BroadcastManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Total clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Total clients: %d", len(self.active_connections))

    async def broadcast(self, payload: Dict[str, Any]):
        """Broadcast a JSON message to all connected WebSocket clients."""
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to.")
            return

        message = json.dumps(payload)
        logger.info("DEBUG: Updated! Broadcasting to %d clients (type: %s)", len(self.active_connections), payload.get("type"))
        dead_connections = set()

        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning("Error sending WebSocket message: %s", e)
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

    def broadcast_sync(self, payload: Dict[str, Any]):
        """Thread-safe synchronous bridge for calling broadcast from sync routes."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(payload))
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.broadcast(payload), loop)
                else:
                    loop.run_until_complete(self.broadcast(payload))
            except Exception as e:
                try:
                    asyncio.run(self.broadcast(payload))
                except Exception as ex:
                    logger.error("Failed sync broadcast dispatch: %s", ex)


broadcast_manager = BroadcastManager()
