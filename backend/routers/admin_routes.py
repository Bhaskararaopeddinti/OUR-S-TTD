"""
OURS TTD — Admin API Router
Pilgrim flow data entry, queue analysis, session management.
All endpoints require admin role authentication.
"""
import uuid
from datetime import datetime, date as dt_date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, PilgrimFlowData, AdminSession
from backend.auth import get_current_admin, get_current_user
from backend.schemas import (
    PilgrimFlowDataIn, PilgrimFlowDataOut,
    AdminDashboardOut, QueueAnalysisOut
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/users")
def list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Admin-only list of safe user details; never returns password fields."""
    users = db.query(User).order_by(desc(User.created_at)).all()
    return [{
        "id": user.id, "name": user.name, "email": user.email,
        "role": user.role, "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    } for user in users]


# ─────────────────────────────────────────────────────────────────────────────
# Thresholds for queue pressure calculation
# ─────────────────────────────────────────────────────────────────────────────
CROWD_THRESHOLDS = {
    "LOW":       2000,
    "MODERATE":  5000,
    "HIGH":      9000,
    "VERY_HIGH": 14000,
    # >= 14000 → CRITICAL
}


def calculate_queue_status(estimated_crowd: int, net_rate: int, festival: bool) -> tuple[str, float]:
    """
    Return (queue_status_string, pressure_0_to_1).
    festival flag increases pressure by 30%.
    """
    base_pressure = 0.0

    if estimated_crowd < CROWD_THRESHOLDS["LOW"]:
        status = "LOW"
        base_pressure = estimated_crowd / CROWD_THRESHOLDS["LOW"] * 0.3
    elif estimated_crowd < CROWD_THRESHOLDS["MODERATE"]:
        status = "MODERATE"
        base_pressure = 0.3 + (estimated_crowd - CROWD_THRESHOLDS["LOW"]) / (CROWD_THRESHOLDS["MODERATE"] - CROWD_THRESHOLDS["LOW"]) * 0.2
    elif estimated_crowd < CROWD_THRESHOLDS["HIGH"]:
        status = "HIGH"
        base_pressure = 0.5 + (estimated_crowd - CROWD_THRESHOLDS["MODERATE"]) / (CROWD_THRESHOLDS["HIGH"] - CROWD_THRESHOLDS["MODERATE"]) * 0.2
    elif estimated_crowd < CROWD_THRESHOLDS["VERY_HIGH"]:
        status = "VERY HIGH"
        base_pressure = 0.7 + (estimated_crowd - CROWD_THRESHOLDS["HIGH"]) / (CROWD_THRESHOLDS["VERY_HIGH"] - CROWD_THRESHOLDS["HIGH"]) * 0.2
    else:
        status = "CRITICAL"
        base_pressure = 0.9

    # Rapid net inflow pushes pressure up
    if net_rate > 1000:
        base_pressure = min(1.0, base_pressure + 0.1)
    if festival:
        base_pressure = min(1.0, base_pressure + 0.15)

    return status, round(base_pressure, 3)


def predict_next_slot(recent_slots: list[PilgrimFlowData], festival: bool) -> str:
    """
    Simple trend-based prediction for the upcoming 2-hour slot.
    Uses the last 3 net_pilgrim values to determine trend.
    """
    if not recent_slots:
        return "Insufficient data for prediction."

    nets = [s.net_pilgrims for s in recent_slots[-3:]]
    if len(nets) >= 2:
        trend = sum(nets[i+1] - nets[i] for i in range(len(nets)-1)) / max(len(nets)-1, 1)
    else:
        trend = 0

    current_crowd = recent_slots[-1].estimated_crowd if recent_slots else 0
    current_status = recent_slots[-1].queue_status if recent_slots else "MODERATE"

    if trend > 500:
        direction = "rapidly increasing"
        next_status = "VERY HIGH" if current_status in ("HIGH", "VERY HIGH") else "HIGH"
    elif trend > 100:
        direction = "steadily increasing"
        next_status = "HIGH" if current_status in ("MODERATE", "HIGH") else current_status
    elif trend < -200:
        direction = "decreasing"
        next_status = "MODERATE" if current_status in ("HIGH", "VERY HIGH") else "LOW"
    else:
        direction = "stable"
        next_status = current_status

    festival_note = " Festival conditions add extra crowd pressure." if festival else ""

    return (
        f"Crowd is {direction}. Predicted next slot: {next_status}. "
        f"Current estimated crowd: {current_crowd:,}.{festival_note}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/admin/pilgrim-data
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/pilgrim-data", response_model=PilgrimFlowDataOut)
def submit_pilgrim_data(
    data: PilgrimFlowDataIn,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin submits raw pilgrim arrival/departure counts for a 2-hour slot.
    Backend calculates: net, accumulated crowd, queue status, queue pressure.
    """
    if data.incoming_pilgrims < 0:
        raise HTTPException(400, "Incoming pilgrim count cannot be negative.")
    if data.outgoing_pilgrims < 0:
        raise HTTPException(400, "Outgoing pilgrim count cannot be negative.")

    duplicate = db.query(PilgrimFlowData).filter(
        PilgrimFlowData.date == data.date,
        PilgrimFlowData.start_time == data.start_time,
        PilgrimFlowData.end_time == data.end_time,
    ).first()
    if duplicate:
        raise HTTPException(409, "Data for this date and two-hour time slot already exists.")

    net = data.incoming_pilgrims - data.outgoing_pilgrims

    row = PilgrimFlowData(
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        incoming_pilgrims=data.incoming_pilgrims,
        outgoing_pilgrims=data.outgoing_pilgrims,
        net_pilgrims=net,
        estimated_crowd=0,
        festival=data.festival,
        queue_status="LOW",
        queue_pressure=0.0,
        created_by_admin=admin.id,
    )
    db.add(row)
    db.flush()

    # Recalculate chronologically so the accumulated crowd remains correct
    # even if an admin enters an earlier slot after a later one.
    day_slots = (
        db.query(PilgrimFlowData)
        .filter(PilgrimFlowData.date == data.date)
        .order_by(PilgrimFlowData.start_time)
        .all()
    )
    crowd = 0
    for slot in day_slots:
        slot.net_pilgrims = slot.incoming_pilgrims - slot.outgoing_pilgrims
        crowd = max(0, crowd + slot.net_pilgrims)
        slot.estimated_crowd = crowd
        slot.queue_status, slot.queue_pressure = calculate_queue_status(
            crowd, slot.net_pilgrims, slot.festival
        )
    db.commit()
    db.refresh(row)

    return PilgrimFlowDataOut(
        id=row.id,
        date=row.date,
        start_time=row.start_time,
        end_time=row.end_time,
        incoming_pilgrims=row.incoming_pilgrims,
        outgoing_pilgrims=row.outgoing_pilgrims,
        net_pilgrims=row.net_pilgrims,
        estimated_crowd=row.estimated_crowd,
        festival=row.festival,
        queue_status=row.queue_status,
        queue_pressure=row.queue_pressure,
        created_at=row.created_at.isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/pilgrim-data
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/pilgrim-data")
def get_pilgrim_data(
    date: str | None = None,
    limit: int = 50,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Retrieve stored pilgrim flow data (optionally filtered by date)."""
    q = db.query(PilgrimFlowData)
    if date:
        q = q.filter(PilgrimFlowData.date == date)
    rows = q.order_by(PilgrimFlowData.date, PilgrimFlowData.start_time).limit(limit).all()
    return [
        {
            "id": r.id,
            "date": r.date,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "incoming_pilgrims": r.incoming_pilgrims,
            "outgoing_pilgrims": r.outgoing_pilgrims,
            "net_pilgrims": r.net_pilgrims,
            "estimated_crowd": r.estimated_crowd,
            "festival": r.festival,
            "queue_status": r.queue_status,
            "queue_pressure": r.queue_pressure,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/queue-analysis
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/queue-analysis", response_model=QueueAnalysisOut)
def queue_analysis(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Return live queue analysis derived from admin-entered data."""
    today = dt_date.today().strftime("%Y-%m-%d")
    slots = (
        db.query(PilgrimFlowData)
        .filter(PilgrimFlowData.date == today)
        .order_by(PilgrimFlowData.start_time)
        .all()
    )

    if not slots:
        return QueueAnalysisOut(
            current_crowd=0,
            queue_status="LOW",
            queue_pressure=0.0,
            incoming_rate=0,
            outgoing_rate=0,
            net_rate=0,
            trend="STABLE",
            prediction="No admin data recorded for today.",
            festival=False,
            total_incoming_today=0,
            total_outgoing_today=0,
            slots_recorded=0,
        )

    latest = slots[-1]

    # Trend: compare last two net values
    if len(slots) >= 2:
        delta = slots[-1].net_pilgrims - slots[-2].net_pilgrims
        trend = "INCREASING" if delta > 200 else ("DECREASING" if delta < -200 else "STABLE")
    else:
        trend = "STABLE"

    prediction = predict_next_slot(slots, latest.festival)

    return QueueAnalysisOut(
        current_crowd=latest.estimated_crowd,
        queue_status=latest.queue_status,
        queue_pressure=latest.queue_pressure,
        incoming_rate=latest.incoming_pilgrims,
        outgoing_rate=latest.outgoing_pilgrims,
        net_rate=latest.net_pilgrims,
        trend=trend,
        prediction=prediction,
        festival=latest.festival,
        total_incoming_today=sum(s.incoming_pilgrims for s in slots),
        total_outgoing_today=sum(s.outgoing_pilgrims for s in slots),
        slots_recorded=len(slots),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/queue-prediction (public endpoint — used by user dashboard & AI)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/queue-prediction")
def queue_prediction_public(db: Session = Depends(get_db)):
    """
    Public endpoint for pilgrim dashboard and AI assistant.
    Returns the latest queue status from admin-entered data.
    No authentication required.
    """
    today = dt_date.today().strftime("%Y-%m-%d")
    latest = (
        db.query(PilgrimFlowData)
        .filter(PilgrimFlowData.date == today)
        .order_by(desc(PilgrimFlowData.start_time))
        .first()
    )

    if not latest:
        return {
            "source": "AI_PREDICTION",
            "queue_status": "MODERATE",
            "estimated_crowd": 0,
            "trend": "STABLE",
            "prediction": "Live admin data not yet available. AI prediction active.",
            "festival": False,
            "data_available": False,
        }

    slots = (
        db.query(PilgrimFlowData)
        .filter(PilgrimFlowData.date == today)
        .order_by(PilgrimFlowData.start_time)
        .all()
    )

    if len(slots) >= 2:
        delta = slots[-1].net_pilgrims - slots[-2].net_pilgrims
        trend = "INCREASING" if delta > 200 else ("DECREASING" if delta < -200 else "STABLE")
    else:
        trend = "STABLE"

    trend_arrow = "↑" if trend == "INCREASING" else ("↓" if trend == "DECREASING" else "→")
    recommendation = _get_recommendation(latest.queue_status, latest.festival)

    return {
        "source": "ADMIN_DATA",
        "queue_status": latest.queue_status,
        "estimated_crowd": latest.estimated_crowd,
        "trend": trend,
        "trend_display": f"{trend_arrow} {trend.title()}",
        "prediction": predict_next_slot(slots, latest.festival),
        "festival": latest.festival,
        "data_available": True,
        "last_updated": latest.created_at.isoformat(),
        "recommendation": recommendation,
    }


def _get_recommendation(status: str, festival: bool) -> str:
    recs = {
        "LOW": "Great time to visit! Minimal wait expected.",
        "MODERATE": "Good time to visit. Expect a moderate wait of 2–3 hours.",
        "HIGH": "Busy period. Consider visiting in an off-peak slot to reduce wait time.",
        "VERY HIGH": "Very high crowds. If possible, plan your darshan during early morning or late night slots.",
        "CRITICAL": "Extremely crowded. TTD officials are managing overflow. Consider postponing if possible.",
    }
    base = recs.get(status, "Monitor the queue and follow TTD instructions.")
    if festival:
        base += " (Festival day — higher than usual crowd expected.)"
    return base


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aggregated statistics for the Admin Portal dashboard."""
    today = dt_date.today().strftime("%Y-%m-%d")
    slots_today = (
        db.query(PilgrimFlowData)
        .filter(PilgrimFlowData.date == today)
        .order_by(PilgrimFlowData.start_time)
        .all()
    )

    latest = slots_today[-1] if slots_today else None
    total_in = sum(s.incoming_pilgrims for s in slots_today)
    total_out = sum(s.outgoing_pilgrims for s in slots_today)
    current_crowd = latest.estimated_crowd if latest else 0
    queue_status = latest.queue_status if latest else "N/A"
    festival = latest.festival if latest else False

    # Predict crowd for next slot
    if latest and slots_today:
        nets = [s.net_pilgrims for s in slots_today[-3:]]
        avg_net = sum(nets) / len(nets) if nets else 0
        predicted_crowd = max(0, current_crowd + int(avg_net))
    else:
        predicted_crowd = 0

    now = datetime.utcnow()
    return AdminDashboardOut(
        server_date=now.strftime("%d-%b-%Y"),
        server_time=now.strftime("%H:%M:%S UTC"),
        total_pilgrims_today=total_in,
        current_crowd=current_crowd,
        total_incoming=total_in,
        total_outgoing=total_out,
        queue_status=queue_status,
        predicted_crowd=predicted_crowd,
        festival=festival,
        slots_recorded=len(slots_today),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/admin/logout  (record session out time)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/logout")
def admin_logout(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Record admin logout time for the active session."""
    session = (
        db.query(AdminSession)
        .filter(
            AdminSession.admin_id == admin.id,
            AdminSession.is_active == True
        )
        .order_by(desc(AdminSession.login_time))
        .first()
    )
    if session:
        session.logout_time = datetime.utcnow()
        session.is_active = False
        db.commit()

    return {
        "message": "Admin logout recorded successfully.",
        "logout_time": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/session-info
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/session-info")
def admin_session_info(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Return the current admin session information."""
    session = (
        db.query(AdminSession)
        .filter(AdminSession.admin_id == admin.id, AdminSession.is_active == True)
        .order_by(desc(AdminSession.login_time))
        .first()
    )

    now = datetime.utcnow()
    login_time = session.login_time if session else now
    duration_minutes = int((now - login_time).total_seconds() / 60) if session else 0

    return {
        "admin_id": admin.id,
        "admin_name": admin.name,
        "admin_email": admin.email,
        "session_id": session.session_id if session else "N/A",
        "login_time": login_time.strftime("%H:%M %p"),
        "login_date": login_time.strftime("%d-%b-%Y"),
        "login_time_iso": login_time.isoformat(),
        "server_date": now.strftime("%d-%b-%Y"),
        "server_time": now.strftime("%H:%M:%S UTC"),
        "session_duration_minutes": duration_minutes,
    }
