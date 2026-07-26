# OURS TTD — AI Smart Pilgrim Assistant

An accessible, temple-inspired digital companion for the Tirumala journey. It is a **guidance and demo platform**, not an official TTD booking service.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://localhost:8000` (the FastAPI app serves the frontend). API documentation is at `/docs`.

### Configuration

Copy `.env.example` to `.env` and set `DATABASE_URL`, `SECRET_KEY`, and optionally `OPENAI_API_KEY`. SQLite is used automatically for a no-setup local demo; deploy with a PostgreSQL URL such as `postgresql+psycopg://user:pass@host/db`.

## Architecture

`frontend/` is a dependency-free PWA UI. `backend/` contains FastAPI routers, SQLAlchemy entities, JWT security, and AI-ready services. Live queue data is broadcast through `/ws/live`; static hosting is mounted from the project root. Seed data is generated on first launch.

## Deployment

Use the start command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. Set `DATABASE_URL`, `SECRET_KEY`, and `CORS_ORIGINS` in Render/Railway. For production, replace demo seed credentials and configure a managed PostgreSQL database.
