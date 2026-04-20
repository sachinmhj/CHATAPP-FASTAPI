# 💬 Chat App — Backend Developer Assignment

A real-time chat application backend built with **Python**, **FastAPI**, and **PostgreSQL**.

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Server | Uvicorn (ASGI) |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Real-time | WebSockets (FastAPI native) |

---

## 📦 Project Structure

```
chat-app/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # DB models: User, Room, Message
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth/
│   │   ├── router.py        # POST /auth/signup, /auth/login
│   │   ├── utils.py         # Password hashing + JWT creation
│   │   └── dependencies.py  # Reusable RBAC dependency
│   ├── chat/
│   │   └── router.py        # WebSocket /ws/{room_id}
│   └── rooms/
│       └── router.py        # Room CRUD + message history
├── .env                     # Local secrets (NOT committed)
├── .env.example             # Env template (safe to commit)
├── requirements.txt
└── README.md
```

---

## ⚙️ How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/sachinmhj/chat-app.git
cd chat-app
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database
```bash
createdb chatapp
```

### 5. Configure environment variables
```bash
cp .env.example .env
# Then edit .env and fill in your real DATABASE_URL and SECRET_KEY
```

Your `.env` should look like:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatapp
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 6. Start the server
```bash
uvicorn app.main:app --reload
```

> The app will automatically create all database tables on first run.

### 7. Open the interactive API docs
```
http://localhost:8000/docs
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | ❌ | Register a new user |
| POST | `/auth/login` | ❌ | Login and get JWT token |
| GET | `/auth/me` | ✅ Any user | Get current user info |
| GET | `/auth/admin-only` | ✅ Admin only | RBAC demo endpoint |

### Rooms
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/rooms/` | ✅ Admin only | Create a new room |
| GET | `/rooms/` | ✅ Any user | List all rooms |
| GET | `/rooms/{room_id}` | ✅ Any user | Get room details |
| GET | `/rooms/{room_id}/messages` | ✅ Any user | Get message history (cursor-paginated) |

### WebSocket
| Protocol | Endpoint | Description |
|---|---|---|
| WS | `/ws/{room_id}?token=<jwt>` | Real-time chat |

---

## 🔌 WebSocket Usage

Connect using any WebSocket client:
```
ws://localhost:8000/ws/1?token=<your_jwt_token>
```

**On connect** — you receive recent message history:
```json
{
  "type": "history",
  "messages": [...],
  "room": { "id": 1, "name": "General" }
}
```

**Send a message** — just send plain text:
```
Hello everyone!
```

**Broadcast received by all clients in the room:**
```json
{
  "type": "message",
  "id": 42,
  "content": "Hello everyone!",
  "username": "sachin",
  "timestamp": "2026-04-20T06:30:00",
  "room_id": 1
}
```

---

## 📄 Cursor-Based Pagination

Message history uses **cursor-based pagination** (not offset).

**Why cursor over offset?**
- OFFSET is unstable — new messages shift pages on re-query
- Cursor (`WHERE id < cursor`) is stable, predictable, and faster at scale

**Usage:**
```
# First page (latest 20 messages)
GET /rooms/1/messages?limit=20

# Next page (pass the lowest ID from the previous response as cursor)
GET /rooms/1/messages?limit=20&cursor=150
```

---

## 🔐 Security Design

| Concern | Approach |
|---|---|
| Password storage | bcrypt hashed via `passlib` — never stored plain |
| JWT signing | HS256 with expiry embedded in token |
| RBAC | Reusable `require_role()` dependency — not hardcoded per route |
| WebSocket auth | JWT passed as query param, connection rejected (code 1008) if invalid |
| Unauthenticated access | All routes except `/auth/signup` and `/auth/login` require a valid token |

---

## 🧩 Group B Choice — PostgreSQL Persistence & Data Modelling

I chose **Task 1: PostgreSQL Persistence & Data Modelling** because:

1. **Natural overlap** — The models (User, Room, Message) are required by Group A anyway, so building them fully is a no-brainer.
2. **Demonstrates database depth** — Proper FK constraints, ORM relationships, and cursor pagination show real backend knowledge.
3. **Cursor pagination is production-grade** — Unlike offset pagination, cursor-based is used in real systems (Slack, Discord) because it doesn't shift on new data.

### Models
- **User** → `id, username, email, hashed_password, role`
- **Room** → `id, name, description, created_at`
- **Message** → `id, content, timestamp, user_id (FK), room_id (FK)`

All foreign key constraints are enforced at the **database level** via SQLAlchemy's `ForeignKey()`.

---

## ✅ Submission Checklist

- [x] Project runs from a fresh clone with no errors
- [x] `.env.example` included (no real secrets)
- [x] All Group A tasks complete (env, JWT auth, WebSocket)
- [x] One Group B task complete (PostgreSQL persistence + cursor pagination)
- [x] README explains how to run the project locally
- [x] Code is clean, readable, and consistently formatted
