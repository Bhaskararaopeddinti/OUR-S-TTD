from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Ensure .env loaded from project root ─────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from backend.database import Base, engine, SessionLocal, test_connection, database_kind
from backend.models import (
    QueueStatus, Facility, User, NavigationLocation,
    Notification
)
from backend.auth import hash_password
from backend.routers import auth_routes, core, transport_routes, cctv_routes
from backend.routers.navigation import router as locations_router, navigation_router
from backend.routers import admin_routes
from backend.models import TransportRoute
from backend.services.broadcast import broadcast_manager

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
# NOTE: Starlette/FastAPI does NOT allow allow_origins=["*"] with allow_credentials=True.
# When origins include wildcard, we use allow_origin_regex to cover all origins.
cors_raw = os.getenv("CORS_ORIGINS", "*").strip()
if not cors_raw or cors_raw == "*":
    # Use regex to cover all http/https origins — safe for development and staging
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
    cors_origins.extend(["http://localhost:8000", "http://127.0.0.1:8000",
                         "http://localhost:3000", "http://localhost:5500", "http://127.0.0.1:5500"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(set(cors_origins)),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ── Routers ────────────────────────────────────────────────────────────────
# API ROUTES FIRST - routers have their prefixes defined
app.include_router(auth_routes.router)
app.include_router(core.router)
app.include_router(transport_routes.router)
app.include_router(locations_router)
app.include_router(navigation_router)
app.include_router(admin_routes.router)
app.include_router(cctv_routes.router)


# ── WebSocket Hub ──────────────────────────────────────────────────────────
@app.websocket("/ws/live")
async def live_ws(ws: WebSocket):
    await broadcast_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   # keep-alive
    except WebSocketDisconnect:
        broadcast_manager.disconnect(ws)

async def broadcast(payload: dict):
    """Broadcast JSON to all connected WebSocket clients."""
    await broadcast_manager.broadcast(payload)

# Inject broadcast function into admin_routes for real-time updates
admin_routes.set_broadcast_function(broadcast_manager.broadcast_sync)

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

def run_database_migrations(db):
    """Ensure newly added columns exist in both SQLite and PostgreSQL databases."""
    from sqlalchemy import text
    try:
        if db.bind.dialect.name == "sqlite":
            # 1. Users table
            res = db.execute(text("PRAGMA table_info(users)")).fetchall()
            cols = {row[1] for row in res}
            if "is_active" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            if "reset_token" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)"))
            if "reset_token_expires" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME"))
            if "last_login" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))

            # 2. PilgrimFlowData table
            res_p = db.execute(text("PRAGMA table_info(pilgrim_flow_data)")).fetchall()
            cols_p = {row[1] for row in res_p}
            if "source" not in cols_p:
                db.execute(text("ALTER TABLE pilgrim_flow_data ADD COLUMN source VARCHAR(40) DEFAULT 'manual'"))

            db.commit()
            logger.info("✓ SQLite column migrations checked and up to date.")
        elif db.bind.dialect.name == "postgresql":
            # PostgreSQL column migrations
            db.execute(text("ALTER TABLE pilgrim_flow_data ADD COLUMN IF NOT EXISTS source VARCHAR(40) DEFAULT 'manual';"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(100);"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;"))
            db.commit()
            logger.info("✓ PostgreSQL column migrations checked and up to date.")
    except Exception as e:
        db.rollback()
        logger.warning("Database column migration check notice: %s", e)

def seed_db():
    """Seed initial data – runs only on first startup (idempotent)."""
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        run_database_migrations(db)
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
        else:
            admin_user.role = "admin"
            admin_user.is_active = True
            admin_user.password_hash = hash_password("DemoAdmin123")
            db.commit()
            logger.info("Verified demo admin user credentials and admin role.")

        # Ensure testadmin@example.com (if created) has admin role
        test_admin = db.query(User).filter_by(email="testadmin@example.com").first()
        if test_admin and test_admin.role != "admin":
            test_admin.role = "admin"
            test_admin.is_active = True
            db.commit()
            logger.info("Promoted testadmin@example.com to admin role.")

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
                    route_name="Tirupati Central Bus Stand to Tirumala Ghat Road",
                    estimated_duration="45 - 60 mins",
                    fare="Rs.65 / person",
                    operating_hours="24 Hours Active",
                    frequency="Every 2-3 mins",
                    status="Available",
                    source="TTD Official Verified"
                ),
                TransportRoute(
                    source_location="Tirumala",
                    destination_location="Tirupati Bus Stand",
                    vehicle_type="GOVERNMENT_BUS",
                    operator="APSRTC",
                    route_name="Tirumala to Tirupati Central Bus Stand (Return)",
                    estimated_duration="45 - 60 mins",
                    fare="Rs.65 / person",
                    operating_hours="24 Hours Active",
                    frequency="Every 2-3 mins",
                    status="Available",
                    source="TTD Official Verified"
                ),
                TransportRoute(
                    source_location="Tirupati Railway Station",
                    destination_location="Tirumala",
                    vehicle_type="TTD_BUS",
                    operator="TTD Devasthanams",
                    route_name="Tirupati Railway Station to Tirumala via Alipiri",
                    estimated_duration="60 - 75 mins",
                    fare="FREE",
                    operating_hours="4:00 AM - 10:00 PM",
                    frequency="Every 15 mins",
                    status="Available",
                    source="100% Free TTD Service"
                ),
                TransportRoute(
                    source_location="Tirumala",
                    destination_location="Tirupati Railway Station",
                    vehicle_type="TTD_BUS",
                    operator="TTD Devasthanams",
                    route_name="Tirumala to Tirupati Railway Station (Return)",
                    estimated_duration="60 - 75 mins",
                    fare="FREE",
                    operating_hours="4:00 AM - 10:00 PM",
                    frequency="Every 15 mins",
                    status="Available",
                    source="100% Free TTD Service"
                ),
                TransportRoute(
                    source_location="Alipiri Checkpost",
                    destination_location="Tirumala",
                    vehicle_type="WALKING",
                    operator="TTD Footpath Trek",
                    route_name="Alipiri Footpath (3,550 Steps)",
                    estimated_duration="3 - 4 Hours",
                    fare="Free (Traditional Trek)",
                    operating_hours="24 Hours Active",
                    frequency="Continuous",
                    status="Open",
                    source="TTD Verified Footpath"
                ),
                TransportRoute(
                    source_location="Tirumala",
                    destination_location="Alipiri Checkpost",
                    vehicle_type="WALKING",
                    operator="TTD Footpath Trek",
                    route_name="Tirumala to Alipiri Footpath (Descent)",
                    estimated_duration="2 - 3 Hours",
                    fare="Free (Traditional Trek)",
                    operating_hours="24 Hours Active",
                    frequency="Continuous",
                    status="Open",
                    source="TTD Verified Footpath"
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
    
    # Log database type
    db_type = database_kind()
    logger.info(f"Database type: {db_type}")
    if db_type == "postgresql":
        logger.info("✓ Connected to Supabase PostgreSQL")
    else:
        logger.info("✓ Connected to SQLite (development mode)")
    
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

    from backend.services.ai_service import get_gemini_api_key
    gemini_key_present = bool(get_gemini_api_key())
    configured_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    logger.info("GEMINI_API_KEY configured: %s", gemini_key_present)
    logger.info("GEMINI_MODEL configured: %s", configured_model)
    logger.info("OURS TTD API started successfully.")


# ── Static Files (Frontend & Uploads) ──────────────────────────────────────
frontend_dir = ROOT / "frontend"
for folder in ["css", "js", "pages", "images", "assets", "icons"]:
    folder_path = frontend_dir / folder
    if folder_path.exists():
        app.mount(f"/{folder}", StaticFiles(directory=str(folder_path)), name=folder)

uploads_dir = ROOT / "backend" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(frontend_dir / "manifest.json")

@app.get("/favicon.svg", include_in_schema=False)
async def serve_favicon_svg():
    """Serve SVG favicon to suppress browser 404."""
    svg_path = frontend_dir / "favicon.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon_ico():
    """Serve favicon.ico – fall back to SVG if .ico not present."""
    ico_path = frontend_dir / "favicon.ico"
    if ico_path.exists():
        return FileResponse(str(ico_path), media_type="image/x-icon")
    # Return the SVG as fallback (browsers accept SVG for modern favicon)
    svg_path = frontend_dir / "favicon.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Non-sensitive application, database, AI, and CCTV worker health status."""
    connected = test_connection()
    from backend.services.ai_service import get_gemini_api_key
    gemini_key_present = bool(get_gemini_api_key())

    # CCTV worker status (non-blocking)
    cctv_status = "idle"
    try:
        from backend.services.cctv_vision import cctv_worker
        ws = cctv_worker.get_status()
        cctv_status = ws.get("status", "idle").lower()
    except Exception:
        cctv_status = "unavailable"

    return {
        "status": "healthy" if connected else "degraded",
        "database": "connected" if connected else "unavailable",
        "database_type": database_kind(),
        "gemini_configured": gemini_key_present,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        "cctv_worker_status": cctv_status,
    }

@app.get("/health", tags=["Health"], include_in_schema=False)
async def health_check_root():
    """Render health check endpoint — returns ok if server is running."""
    return {"status": "ok"}

# Serve index.html at root and /index.html
@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
async def serve_index():
    return FileResponse(frontend_dir / "index.html")


