from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import Base, engine, SessionLocal
from backend.models import QueueStatus, Facility, User
from backend.auth import hash_password
from backend.routers import auth_routes, core

app = FastAPI(title="OURS TTD API", version="1.0.0", description="AI Smart Pilgrim Assistant demo APIs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_routes.router); app.include_router(core.router)
clients: set[WebSocket] = set()

def seed():
    Base.metadata.create_all(engine)
    db=SessionLocal()
    if not db.query(QueueStatus).first(): db.add(QueueStatus(wait_minutes=135,crowd_density="High",people_count=7420))
    if not db.query(User).filter_by(email="admin@oursttd.demo").first(): db.add(User(name="Demo Admin",email="admin@oursttd.demo",password_hash=hash_password("DemoAdmin123"),role="admin"))
    if not db.query(Facility).first(): db.add_all([Facility(kind="food",name="Annaprasadam Dining Hall",distance_m=420,wait_minutes=12,hours="7 AM–10 PM"),Facility(kind="laddu",name="Laddu Counter 2",distance_m=280,wait_minutes=18),Facility(kind="medical",name="Ashwini Hospital Help Desk",distance_m=650,wait_minutes=3),Facility(kind="restroom",name="Vaikuntam Restroom Block",distance_m=190),Facility(kind="phone",name="Phone Deposit Centre A",distance_m=250,wait_minutes=8),Facility(kind="water",name="Drinking Water Point",distance_m=120)])
    db.commit(); db.close()
@app.on_event("startup")
async def startup(): seed()
@app.websocket("/ws/live")
async def live(ws: WebSocket):
    await ws.accept(); clients.add(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: clients.discard(ws)

ROOT=Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
