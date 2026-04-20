from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Room, Message, User, UserRole
from app.schemas import RoomCreate, RoomResponse, PaginatedMessages, MessageResponse
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/rooms", tags=["Rooms"])


# ─── Create Room (Admin Only) ─────────────────────────────────────────────────

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Create a new chat room.
    Restricted to admin users — demonstrates RBAC dependency in action.
    """
    if db.query(Room).filter(Room.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A room with this name already exists",
        )

    room = Room(name=payload.name, description=payload.description)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


# ─── List All Rooms (Any Authenticated User) ──────────────────────────────────

@router.get("/", response_model=list[RoomResponse])
def list_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all available chat rooms."""
    return db.query(Room).order_by(Room.created_at.desc()).all()


# ─── Get Room by ID ───────────────────────────────────────────────────────────

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific room."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


# ─── Get Message History (Cursor-Based Pagination) ────────────────────────────

@router.get("/{room_id}/messages", response_model=PaginatedMessages)
def get_message_history(
    room_id: int,
    limit: int = Query(default=20, ge=1, le=100, description="Number of messages to fetch"),
    cursor: Optional[int] = Query(default=None, description="Message ID to paginate before (cursor-based)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch paginated message history for a room using cursor-based pagination.

    Why cursor-based instead of offset?
    - OFFSET pagination is unstable: if new messages are added, pages shift.
    - Cursor (ID-based) is stable and efficient even with millions of rows.
    - We use the message ID as the cursor: fetch messages WHERE id < cursor.

    Usage:
    - First page:  GET /rooms/1/messages?limit=20
    - Next page:   GET /rooms/1/messages?limit=20&cursor=<lowest_id_from_prev_page>
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Build cursor-based query — no OFFSET used
    query = db.query(Message).filter(Message.room_id == room_id)
    if cursor is not None:
        query = query.filter(Message.id < cursor)

    # Fetch one extra to determine if there are more pages
    messages = query.order_by(Message.id.desc()).limit(limit + 1).all()

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Return in chronological order (oldest → newest)
    messages.reverse()

    next_cursor = messages[0].id if has_more and messages else None

    return PaginatedMessages(
        messages=[
            MessageResponse(
                id=m.id,
                content=m.content,
                timestamp=m.timestamp,
                user_id=m.user_id,
                room_id=m.room_id,
                username=m.author.username if m.author else None,
            )
            for m in messages
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )
