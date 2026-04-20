# 💬 Chat Application Backend

A real-time chat application backend built with **Python**, **FastAPI**, and **PostgreSQL**.

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally on your machine.

### 1. Prerequisites
Ensure you have the following installed:
- **Python 3.10+**
- **PostgreSQL**
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/sachinmhj/CHATAPP-FASTAPI.git
cd CHATAPP-FASTAPI
```

### 3. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Database Setup
Create a new PostgreSQL database:
```bash
createdb chatapp
```

### 6. Environment Configuration
Create a `.env` file in the root directory and add your configuration. You can use the template below:
```bash
cp .env.example .env
```
Update the `DATABASE_URL` in `.env` to match your local PostgreSQL credentials:
`DATABASE_URL=postgresql://<user>@localhost:5432/chatapp`

### 7. Run the Application
Start the Uvicorn server:
```bash
uvicorn app.main:app --reload
```

---

## 📡 API Documentation
Once the server is running, you can access the interactive Swagger documentation at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Key Endpoints:
- **Auth**: `/auth/signup`, `/auth/login`, `/auth/me`
- **Rooms**: `/rooms/` (Create and List rooms)
- **Chat**: `/ws/{room_id}` (WebSocket real-time chat)

---

## 🔌 WebSocket Testing
To test the real-time chat:
1. Obtain a JWT token via `/auth/login`.
2. Connect to the WebSocket using a client like Postman or the browser:
   `ws://localhost:8000/ws/{room_id}?token=YOUR_JWT_TOKEN`
