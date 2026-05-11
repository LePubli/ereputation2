"""
WebSocket Notifications Manager — B2B Prospector
Endpoints :
  WS  /ws/notifications?token=<jwt>
  POST /notifications/broadcast  (interne)

Usage depuis n'importe quel plugin :
    from services.notifications import notify_user, broadcast
    await notify_user(user_id, "signal", "Nouveau lead chaud", "ACME Corp vient de visiter...")
    await broadcast("enrich_complete", "Enrichissement terminé", "42 prospects mis à jour")
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)


class NotificationManager:
    """Gestionnaire de connexions WebSocket avec rooms par user_id"""

    def __init__(self):
        # user_id -> set of websocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # broadcast to all
        self._all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        self._all_connections.add(websocket)
        logger.info(f"WS connected: user={user_id} total={len(self._all_connections)}")

        # Send welcome
        await self._send(websocket, {
            "type": "connected",
            "title": "Connecté",
            "message": "Notifications temps réel activées",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        self._all_connections.discard(websocket)
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WS disconnected: user={user_id} total={len(self._all_connections)}")

    async def notify_user(
        self,
        user_id: str,
        msg_type: str,
        title: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        """Envoie une notification à un utilisateur spécifique"""
        if user_id not in self._connections:
            return
        payload = {
            "type": msg_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        dead: Set[WebSocket] = set()
        for ws in list(self._connections[user_id]):
            try:
                await self._send(ws, payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[user_id].discard(ws)
            self._all_connections.discard(ws)

    async def broadcast(
        self,
        msg_type: str,
        title: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        """Envoie une notification à TOUS les utilisateurs connectés"""
        if not self._all_connections:
            return
        payload = {
            "type": msg_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        dead: Set[WebSocket] = set()
        for ws in list(self._all_connections):
            try:
                await self._send(ws, payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._all_connections.discard(ws)

    async def send_progress(
        self,
        user_id: str,
        job_id: str,
        progress: int,
        title: str,
        message: Optional[str] = None,
    ) -> None:
        """Envoie une mise à jour de progression"""
        await self.notify_user(user_id, "job_progress", title, message, {
            "job_id": job_id,
            "progress": progress,
        })

    @staticmethod
    async def _send(ws: WebSocket, payload: dict) -> None:
        await ws.send_text(json.dumps(payload, ensure_ascii=False, default=str))

    @property
    def connected_count(self) -> int:
        return len(self._all_connections)


# Singleton global
manager = NotificationManager()


# Convenience shortcuts
async def notify_user(user_id: str, msg_type: str, title: str, message: str = None, data: dict = None):
    await manager.notify_user(user_id, msg_type, title, message, data)

async def broadcast(msg_type: str, title: str, message: str = None, data: dict = None):
    await manager.broadcast(msg_type, title, message, data)
