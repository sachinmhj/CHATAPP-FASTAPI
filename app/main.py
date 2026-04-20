from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.rooms.router import router as rooms_router

# ─── Create all database tables on startup ────
Base.metadata.create_all(bind=engine)

# ─── FastAPI Application -----
app = FastAPI(
    title="Chat App API",
    description=(
        "Real-time chat application backend built with FastAPI + PostgreSQL.\n\n"
        "## Features\n"
        "- JWT Authentication with Role-Based Access Control (RBAC)\n"
        "- Real-time WebSocket chat with multi-room support\n"
        "- Cursor-based message pagination\n\n"
        "## How to use\n"
        "1. `POST /auth/signup` — create an account\n"
        "2. `POST /auth/login` — get your JWT token\n"
        "3. Use the token in the `Authorization: Bearer <token>` header\n"
        "4. `POST /rooms/` (admin only) — create a chat room\n"
        "5. Connect to `ws://localhost:8000/ws/{room_id}?token=<jwt>` to chat\n"
    ),
    version="1.0.0",
)

# ─── CORS Middleware ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ────
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(chat_router)
