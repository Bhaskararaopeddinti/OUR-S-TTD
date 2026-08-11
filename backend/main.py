"""
OURS TTD – FastAPI Application Entry Point
Handles startup, seeding, CORS, WebSockets, and static file serving.
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Load .env ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from backend.database import Base, engine, SessionLocal, test_connection
from backend.models import (
    QueueStatus, Facility, User, NavigationLocation,
    Notification
)
from backend.auth import hash_password
from backend.routers import auth_routes, core, transport_routes
from backend.routers.navigation import router as locations_router, navigation_router
from backend.routers import admin_routes
from backend.models import TransportRoute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="OURS TTD API",
    version="2.0.0",
    description="AI Smart Pilgrim Assistant – production-ready API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)



@app.get("/api/docs", include_in_schema=False)
async def redirect_api_docs():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

# ── CORS ───────────────────────────────────────────────────────────────────
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
# API ROUTES FIRST - routers have their own prefixes defined
app.include_router(auth_routes.router)
app.include_router(core.router)
app.include_router(transport_routes.router)
app.include_router(locations_router)
app.include_router(navigation_router)
app.include_router(admin_routes.router)

# ── WebSocket Hub ──────────────────────────────────────────────────────────
clients: set[WebSocket] = set()

@app.websocket("/ws/live")
async def live_ws(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()   # keep-alive
    except WebSocketDisconnect:
        clients.discard(ws)

async def broadcast(payload: dict):
    """Broadcast JSON to all connected WebSocket clients."""
    msg = json.dumps(payload)
    dead = set()
    for ws in clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    clients.difference_update(dead)

# ── Database Seeding ───────────────────────────────────────────────────────
NAV_LOCATIONS = [
    dict(name="Srivari Temple Main Gate", category="temple", description="Main entrance to Sri Venkateswara Swamy Temple", latitude=13.6839, longitude=79.3476),
    dict(name="Vaikuntam Queue Complex I (VQC I)", category="queue", description="Main pilgrim waiting complex", latitude=13.6842, longitude=79.3478),
    dict(name="Vaikuntam Queue Complex II (VQC II)", category="queue", description="Second pilgrim waiting complex", latitude=13.6841, longitude=79.3480),
    dict(name="MTVAC Annaprasadam", category="food", description="Matrusri Tarigonda Vengamamba Annaprasada Complex – free meals", latitude=13.6845, longitude=79.3482),
    dict(name="Aswini Hospital", category="medical", description="24/7 hospital near Seshadri Nagar", latitude=13.6825, longitude=79.3450),
    dict(name="Laddu Counter (Main)", category="laddu", description="Primary laddu distribution complex", latitude=13.6850, longitude=79.3490),
    dict(name="Phone Deposit Centre A", category="phone_deposit", description="Mobile phone deposit near VQC I", latitude=13.6843, longitude=79.3472),
    dict(name="Alipiri Footpath Start", category="footpath", description="3,550 steps – 3 to 4 hour climb", latitude=13.6550, longitude=79.3380),
    dict(name="Srivari Mettu Footpath Start", category="footpath", description="2,100 steps – 2 hour climb", latitude=13.6480, longitude=79.3310),
    dict(name="Kalyanakatta (Tonsure)", category="tonsure", description="Free hair offering complex", latitude=13.6855, longitude=79.3500),
    dict(name="Rambagicha Bus Stand", category="transport", description="Main bus stand for Tirumala", latitude=13.6810, longitude=79.3430),
    dict(name="PAC-3 Accommodation", category="accommodation", description="Pilgrim Accommodation Complex 3", latitude=13.6820, longitude=79.3460),
    dict(name="Drinking Water Points (VQC)", category="water", description="Free purified water near queue complex", latitude=13.6840, longitude=79.3475),
    dict(name="Alipiri Parking", category="parking", description="Main parking area at Alipiri base", latitude=13.6300, longitude=79.3200),
]

def migrate_users_columns(db):
    """Ensure newly added User columns exist in SQLite database."""
    try:
        from sqlalchemy import text
        res = db.execute(text("PRAGMA table_info(users)")).fetchall()
        cols = {row[1] for row in res}
        if "is_active" not in cols:
            db.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            logger.info("Migrated SQLite: added is_active to users table")
        if "reset_token" not in cols:
            db.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)"))
            logger.info("Migrated SQLite: added reset_token to users table")
        if "reset_token_expires" not in cols:
            db.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME"))
            logger.info("Migrated SQLite: added reset_token_expires to users table")
        db.commit()
    except Exception as e:
        logger.warning("Users column migration check: %s", e)

def seed_db():
    """Seed initial data – runs only on first startup (idempotent)."""
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        migrate_users_columns(db)
        # Demo admin
        admin_user = db.query(User).filter_by(email="admin@oursttd.demo").first()
        if not admin_user:
            admin = User(
                name="Demo Admin",
                email="admin@oursttd.demo",
                password_hash=hash_password("DemoAdmin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            logger.info("Demo admin user created.")
        elif admin_user.role != "admin":
            admin_user.role = "admin"
            admin_user.is_active = True
            db.commit()
            logger.info("Updated demo admin user role to admin.")

        # Queue status placeholder
        if not db.query(QueueStatus).first():
            db.add(QueueStatus(
                wait_minutes=135,
                crowd_density="High",
                people_count=7420,
                location="Sarva Darshan"
            ))

        # Facilities
        if not db.query(Facility).first():
            db.add_all([
                Facility(kind="food", name="Annaprasadam Dining Hall", distance_m=420, wait_minutes=12, hours="7 AM–10 PM"),
                Facility(kind="laddu", name="Laddu Counter 2", distance_m=280, wait_minutes=18),
                Facility(kind="medical", name="Ashwini Hospital Help Desk", distance_m=650, wait_minutes=3),
                Facility(kind="restroom", name="Vaikuntam Restroom Block", distance_m=190),
                Facility(kind="phone", name="Phone Deposit Centre A", distance_m=250, wait_minutes=8),
                Facility(kind="water", name="Drinking Water Point", distance_m=120),
                Facility(kind="wheelchair", name="Wheelchair Help Desk", distance_m=300),
            ])

        # Navigation locations
        if not db.query(NavigationLocation).first():
            for loc in NAV_LOCATIONS:
                db.add(NavigationLocation(**loc))

        # Transport routes
        if not db.query(TransportRoute).first():
            db.add_all([
                TransportRoute(
                    source_location="Tirupati Bus Stand",
                    destination_location="Tirumala",
                    vehicle_type="GOVERNMENT_BUS",
                    operator="APSRTC",
                    route_name="Tirupati Central Bus Stand → Tirumala Ghat Road",
                    estimated_duration="45 - 60 mins",
                    fare="₹65 / person",
                    operating_hours="24 Hours Active",
                    frequency="Every 2-3 mins",
                    status="Available",
                    source="TTD Official Verified"
                ),
                TransportRoute(
                    source_location="CRO Tirumala",
                    destination_location="VQC Queue Complex",
                    vehicle_type="TTD_BUS",
                    operator="TTD Devasthanams",
                    route_name="TTD Free Dharma Ratham (Internal Shuttle)",
                    estimated_duration="10 - 20 mins",
                    fare="FREE",
                    operating_hours="24 Hours Active",
                    frequency="Continuous",
                    status="Available",
                    source="100% Free TTD Service"
                ),
                TransportRoute(
                    source_location="Srivari Mettu",
                    destination_location="Tirumala",
                    vehicle_type="WALKING",
                    operator="TTD Footpath Trek",
                    route_name="Srivari Mettu Traditional Trek (2,388 Steps)",
                    estimated_duration="2 - 3 Hours",
                    fare="Free (Traditional Trek)",
                    operating_hours="6:00 AM - 5:00 PM",
                    frequency="Continuous",
                    status="Open",
                    source="TTD Verified Footpath"
                )
            ])

        db.commit()
        logger.info("Database seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.error("Seeding error: %s", e)
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    # Test database connection first
    if not test_connection():
        logger.error("Database connection failed. Application may not function correctly.")
    
    # Create tables
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
    
    # Seed database
    try:
        seed_db()
        logger.info("Database seeding completed.")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")


    # Seed comprehensive bus/transport demo routes
    try:
        from backend.seed_bus_routes import seed_bus_routes
        seed_bus_routes()
        logger.info("Bus route seeding completed.")
    except Exception as e:
        logger.warning("Bus route seeding skipped: %s", e)

    logger.info("OURS TTD API started. Gemini key: %s",
                "configured" if os.getenv("GEMINI_API_KEY") else "not set (keyword fallback)")


# ── Static Files (Frontend) ────────────────────────────────────────────────
frontend_dir = ROOT / "frontend"
for folder in ["css", "js", "pages", "images", "assets"]:
    folder_path = frontend_dir / folder
    if folder_path.exists():
        app.mount(f"/{folder}", StaticFiles(directory=str(folder_path)), name=folder)

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(frontend_dir / "manifest.json")

# Serve index.html at root
@app.get("/")
async def serve_index():
    return FileResponse(frontend_dir / "index.html")

