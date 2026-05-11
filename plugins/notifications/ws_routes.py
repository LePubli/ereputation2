"""
WebSocket router — à inclure dans main.py :
    from plugins.notifications.ws_routes import router as ws_router
    app.include_router(ws_router)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging

from core.security import verify_token
from services.notifications import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Endpoint WebSocket pour les notifications temps réel.
    Auth via token JWT en query param : ws://host/ws/notifications?token=<jwt>
    """
    # Authenticate
    user_id = "anonymous"
    if token:
        try:
            payload = verify_token(token)
            user_id = str(payload.get("sub", "anonymous"))
        except Exception as e:
            logger.warning(f"WS auth failed: {e}")
            await websocket.close(code=1008, reason="Token invalide")
            return

    await manager.connect(websocket, user_id)

    try:
        # Keep alive loop — handle ping/pong
        while True:
            try:
                data = await websocket.receive_text()
                # Handle client messages (ping, subscribe, etc.)
                import json
                msg = json.loads(data) if data else {}
                if msg.get("type") == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)


# HTTP endpoint to get connection stats
@router.get("/ws/stats")
async def ws_stats():
    return {
        "connected_clients": manager.connected_count,
    }
