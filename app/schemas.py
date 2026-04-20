from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.user


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


# ─── Room Schemas ─────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Message Schemas ──────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: int
    content: str
    timestamp: datetime
    user_id: int
    room_id: int
    username: Optional[str] = None  # Joined from User

    class Config:
        from_attributes = True


class PaginatedMessages(BaseModel):
    messages: List[MessageResponse]
    next_cursor: Optional[int] = None   # ID to use as cursor for next page
    has_more: bool
