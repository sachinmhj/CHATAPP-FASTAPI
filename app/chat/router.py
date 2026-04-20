import json
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Message, Room, User
from app.auth.utils import decode_access_token

router = APIRouter(tags=["WebSocket Chat"])

# ─── Connection Manager ───────────────────────────────────────────────────────
# Keeps track of all active WebSocket connections, grouped by room_id.
# Structure: { room_id: [WebSocket, WebSocket, ...] }

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    def connect(self, room_id: int, websocket: WebSocket):
        """Add a new WebSocket connection to a room."""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        """Remove a WebSocket from its room. Clean up empty rooms."""
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        """Broadcast a JSON message to all clients in a room."""
        connections = self.active_connections.get(room_id, [])
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        # Clean up any broken connections found during broadcast
        for conn in disconnected:
            self.disconnect(room_id, conn)


manager = ConnectionManager()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_recent_messages(db: Session, room_id: int, limit: int = 20, cursor: Optional[int] = None):
    """
    Cursor-based pagination for message history.
    Uses message ID as cursor instead of OFFSET — more efficient and stable.

    cursor = last seen message ID (fetch messages BEFORE this ID)
    """
    query = db.query(Message).filter(Message.room_id == room_id)

    if cursor is not None:
        query = query.filter(Message.id < cursor)

    messages = query.order_by(Message.id.desc()).limit(limit).all()
    # Return in chronological order (oldest first)
    messages.reverse()
    return messages


def message_to_dict(msg: Message) -> dict:
    """Serialize a Message ORM object to a JSON-safe dict."""
    return {
        "id": msg.id,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat(),
        "user_id": msg.user_id,
        "username": msg.author.username if msg.author else "unknown",
        "room_id": msg.room_id,
    }


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────

@router.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    Protected WebSocket endpoint for real-time chat.

    Connect with: ws://localhost:8000/ws/{room_id}?token=<jwt_token>

    On connection:
      - Verifies JWT token → rejects unauthenticated connections (closes with 1008).
      - Verifies room exists.
      - Sends last 20 messages (cursor-based) to the newly connected client.

    On message:
      - Saves message to PostgreSQL.
      - Broadcasts to all clients in the same room.

    On disconnect:
      - Gracefully removes connection from the room.
    """
    db: Session = SessionLocal()

    try:
        # ── Step 1: Verify JWT token ─────────────────────────────────────────
        payload = decode_access_token(token)
        if payload is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        username = payload.get("sub")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = db.query(User).filter(User.username == username).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # ── Step 2: Verify room exists ───────────────────────────────────────
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # ── Step 3: Accept connection & register ─────────────────────────────
        await websocket.accept()
        manager.connect(room_id, websocket)

        # ── Step 4: Send recent message history (cursor-based) ───────────────
        recent_messages = get_recent_messages(db, room_id, limit=20)
        await websocket.send_text(json.dumps({
            "type": "history",
            "messages": [message_to_dict(m) for m in recent_messages],
            "room": {"id": room.id, "name": room.name},
        }))

        # ── Step 5: Notify room of new connection ────────────────────────────
        await manager.broadcast(room_id, {
            "type": "system",
            "message": f"{user.username} joined the room.",
        })

        # ── Step 6: Listen for incoming messages ─────────────────────────────
        while True:
            data = await websocket.receive_text()

            # Ignore empty messages
            if not data.strip():
                continue

            # Persist message to PostgreSQL
            new_message = Message(
                content=data.strip(),
                user_id=user.id,
                room_id=room_id,
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # Broadcast to all clients in the room (including sender)
            await manager.broadcast(room_id, {
                "type": "message",
                **message_to_dict(new_message),
            })

    except WebSocketDisconnect:
        # ── Step 7: Clean up on disconnect ───────────────────────────────────
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, {
            "type": "system",
            "message": f"{user.username} left the room.",
        })
    except Exception as e:
        # Catch unexpected errors — close gracefully
        manager.disconnect(room_id, websocket)
    finally:
        db.close()
