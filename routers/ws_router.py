from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Dict, List
import json

import models
from database import SessionLocal
from auth import SECRET_KEY, ALGORITHM

router = APIRouter()


# =========================
# CONNECTION MANAGER
# =========================
class ConnectionManager:
    """Tracks active WebSocket connections per chat room."""

    def __init__(self):
        # room_id -> list of (websocket, username, avatar_color)
        self.active_connections: Dict[int, List[tuple]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, username: str, avatar_color: str):
        await websocket.accept()
        self.active_connections.setdefault(room_id, []).append(
            (websocket, username, avatar_color)
        )

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                c for c in self.active_connections[room_id] if c[0] != websocket
            ]

    def get_online_count(self, room_id: int) -> int:
        return len(self.active_connections.get(room_id, []))

    async def broadcast(self, message: dict, room_id: int, exclude: WebSocket = None):
        """Send a message to every connected client in the room."""
        dead = []
        for conn_tuple in self.active_connections.get(room_id, []):
            ws = conn_tuple[0]
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(conn_tuple)
        for d in dead:
            if d in self.active_connections.get(room_id, []):
                self.active_connections[room_id].remove(d)


manager = ConnectionManager()


def _get_user_from_cookie_token(token: str):
    """Decode the JWT (same cookie the rest of the app uses) and load the user."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        return None

    db: Session = SessionLocal()
    try:
        return db.query(models.User).filter(models.User.username == username).first()
    finally:
        db.close()


# =========================
# WEBSOCKET ROUTE
# =========================
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):

    access_token = websocket.cookies.get("access_token")

    # ---- authenticate before accepting ----
    try:
        if not access_token:
            raise JWTError("missing token")
        user = _get_user_from_cookie_token(access_token)
        if not user:
            raise JWTError("unknown user")
    except JWTError:
        await websocket.close(code=1008)
        return

    username = user.username
    avatar_color = user.avatar_color
    user_id = user.id

    await manager.connect(websocket, room_id, username, avatar_color)

    await manager.broadcast(
        {
            "type": "system",
            "message": f"{username} joined the chat",
            "online": manager.get_online_count(room_id),
        },
        room_id,
    )

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except Exception:
                continue

            msg_type = data.get("type", "message")

            # ---- typing indicator: nothing saved, just relayed ----
            if msg_type == "typing":
                await manager.broadcast(
                    {"type": "typing", "username": username},
                    room_id,
                    exclude=websocket,
                )
                continue

            # ---- normal chat message ----
            content = (data.get("content") or "").strip()
            if not content or len(content) > 2000:
                continue

            db = SessionLocal()
            try:
                new_msg = models.Message(
                    content=content, sender_id=user_id, room_id=room_id
                )
                db.add(new_msg)
                db.commit()
                db.refresh(new_msg)
                msg_id = new_msg.id
                timestamp = new_msg.timestamp.isoformat()
            finally:
                db.close()

            await manager.broadcast(
                {
                    "type": "message",
                    "id": msg_id,
                    "content": content,
                    "username": username,
                    "avatar_color": avatar_color,
                    "timestamp": timestamp,
                    "room_id": room_id,
                },
                room_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(
            {
                "type": "system",
                "message": f"{username} left the chat",
                "online": manager.get_online_count(room_id),
            },
            room_id,
        )
