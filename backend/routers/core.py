"""
OURS TTD — Core API Router
All pilgrim-facing and admin endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import (
    Facility, EmergencyAlert, Feedback, User, Booking,
    ChatHistory, Notification, HealthReminder, LostFound,
    NavigationLocation, PilgrimProfile
)
from backend.schemas import (
    ChatIn, SOSIn, FeedbackIn, TranslateIn, NearbyFacilitiesIn,
    BookingIn, BookingUpdate, LostFoundIn, LostFoundUpdate,
    HealthReminderIn, HealthReminderUpdate, NotificationMarkRead,
    ProfileUpdate
)
from backend.services.ai_service import pilgrim_reply
from backend.services.queue_prediction import predict, predict_queue_status
from backend.services.recommendation import recommendations
from backend.services.translation import supported_languages
from backend.services.google_translation import translate_text, get_language_code
from backend.services.location_service import find_nearby_facilities, format_distance, get_facility_directions
from backend.services.notification_service import generate_smart_notifications, get_notification_summary
from backend.auth import current_claims, get_current_user, get_current_admin
from backend.services.ttd_official import public_status
from backend.services.facilities_data import FACILITIES

router = APIRouter(prefix="/api", tags=["Pilgrim services"])


# ──────────────────────── Queue ────────────────────────
@router.get("/queue")
def queue():
    """Public TTD status with AI-powered predictive intelligence."""
    status = public_status()
    
    # Add AI predictive intelligence
    prediction = predict_queue_status(
        current_wait_minutes=status.get("wait_minutes", 120),
        current_density=status.get("crowd_density", "Moderate")
    )
    
    return {
        **status,
        "ai_prediction": prediction,
        "prediction_disclaimer": "Predictions based on historical patterns and time analysis. Verify with TTD officials for real-time updates."
    }


# ──────────────────────── Facilities ────────────────────────
@router.get("/facilities")
def facilities(kind: str | None = None):
    """Facility directory for the UI; no artificial distance or availability is returned."""
    rows = [x for x in FACILITIES if not kind or x["kind"] == kind]
    return {
        "verification": "Project-supplied facility information — verify operational details with TTD before travel.",
        "facilities": rows
    }


# ──────────────────────── Nearby Facilities (GPS) ────────────────────────
@router.get("/nearby")
def nearby_facilities(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    max_distance: float | None = Query(None, description="Max distance in metres"),
    kind: str | None = None,
):
    """
    Return facilities sorted by walking time from the provided GPS coordinates.
    Uses crowd-aware routing with Haversine formula for distance calculation.
    """
    rows = [x for x in FACILITIES if not kind or x["kind"] == kind]
    nearby = find_nearby_facilities(latitude, longitude, rows, max_distance)
    # Attach human-readable distance label
    for f in nearby:
        f["distance_label"] = format_distance(f.get("distance_m", 0))
    return {
        "count": len(nearby),
        "user_location": {"latitude": latitude, "longitude": longitude},
        "facilities": nearby,
        "routing_type": "Crowd-aware (sorted by walking time)"
    }


# ──────────────────────── Facility Directions ────────────────────────
@router.get("/directions/{facility_kind}")
def facility_directions(
    facility_kind: str,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """
    Get detailed directions to a specific facility type with crowd-aware recommendations.
    """
    # Find the first facility of the requested kind
    facility = next((f for f in FACILITIES if f["kind"] == facility_kind), None)
    if not facility:
        raise HTTPException(404, f"Facility type '{facility_kind}' not found")
    
    directions = get_facility_directions(latitude, longitude, facility)
    return directions


# ──────────────────────── AI Chat ────────────────────────
@router.post("/chat")
def chat(data: ChatIn, db: Session = Depends(get_db)):
    """AI-powered pilgrim assistant powered by Gemini API."""
    res = pilgrim_reply(
        message=data.message,
        language=data.language,
        history=data.history,
        db=db
    )
    reply_text = res.get("reply", "")

    # Save conversation to history (anonymous if no auth)
    try:
        db.add(ChatHistory(role="user", message=data.message, language=data.language))
        db.add(ChatHistory(role="assistant", message=reply_text, language=data.language))
        db.commit()
    except Exception:
        db.rollback()

    return res


# ──────────────────────── SOS ────────────────────────
@router.post("/sos")
def sos(data: SOSIn, db: Session = Depends(get_db)):
    alert = EmergencyAlert(**data.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {
        "id": alert.id,
        "status": "dispatched",
        "message": "Your alert has been shared with the support desk. Stay in a safe visible place. TTD Helpline: 155257."
    }


# ──────────────────────── Recommendations ────────────────────────
@router.get("/recommendations")
def recommend():
    return recommendations()


# ──────────────────────── Languages ────────────────────────
@router.get("/languages")
def languages():
    return supported_languages()


# ──────────────────────── Notices ────────────────────────
@router.get("/notices")
def notices():
    return [
        {"title": "Temple etiquette", "body": "Traditional, modest attire is requested. Please follow volunteer directions."},
        {"title": "Keep hydrated", "body": "Water points are available throughout the queue complex."},
        {"title": "Phone deposit", "body": "Deposit mobile phones before entering the temple area. Retain your receipt token."},
        {"title": "TTD Helpline", "body": "For any emergency or assistance, call 155257."},
    ]


# ──────────────────────── Translation ────────────────────────
@router.post("/translate")
def translate(data: TranslateIn):
    target_code = get_language_code(data.target_language)
    translated = translate_text(data.text, target_code)
    return {"original": data.text, "translated": translated, "target_language": data.target_language}


# ──────────────────────── Feedback ────────────────────────
@router.post("/feedback")
def feedback(data: FeedbackIn, db: Session = Depends(get_db)):
    row = Feedback(**data.model_dump())
    db.add(row)
    db.commit()
    return {"message": "Thank you for your feedback."}


# ──────────────────────── Bookings ────────────────────────
@router.post("/bookings")
def create_booking(data: BookingIn, claims=Depends(current_claims), db: Session = Depends(get_db)):
    """Create a booking request (pending TTD integration)."""
    booking = Booking(
        user_id=int(claims["sub"]),
        booking_type=data.booking_type,
        date=data.date,
        slot=data.slot,
        notes=data.notes or "Available after official TTD API integration.",
        status="pending_integration"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {
        "id": booking.id,
        "status": booking.status,
        "message": "Booking request recorded. Official booking will be available after TTD API integration.",
        "booking_type": booking.booking_type,
        "date": booking.date
    }


@router.get("/bookings")
def list_bookings(claims=Depends(current_claims), db: Session = Depends(get_db)):
    """List bookings for the authenticated user."""
    user_id = int(claims["sub"])
    bookings = db.query(Booking).filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "booking_type": b.booking_type,
            "date": b.date,
            "slot": b.slot,
            "status": b.status,
            "notes": b.notes,
            "created_at": b.created_at.isoformat()
        }
        for b in bookings
    ]


# ──────────────────────── Lost & Found ────────────────────────
@router.post("/lostfound")
def create_lost_found(data: LostFoundIn, db: Session = Depends(get_db)):
    """Report a lost/found item or person."""
    report = LostFound(**data.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return {
        "id": report.id,
        "status": report.status,
        "message": "Your report has been filed. TTD support has been notified."
    }


@router.get("/lostfound")
def list_lost_found(
    report_type: str | None = None,
    category: str | None = None,
    status: str = "open",
    db: Session = Depends(get_db)
):
    """Search lost & found reports."""
    q = db.query(LostFound).filter_by(status=status)
    if report_type:
        q = q.filter_by(report_type=report_type)
    if category:
        q = q.filter_by(category=category)
    reports = q.order_by(LostFound.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "report_type": r.report_type,
            "category": r.category,
            "description": r.description,
            "location": r.location,
            "contact_info": r.contact_info,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        }
        for r in reports
    ]


# ──────────────────────── Health Reminders ────────────────────────
@router.post("/health/reminders")
def create_health_reminder(data: HealthReminderIn, claims=Depends(current_claims), db: Session = Depends(get_db)):
    """Set a health reminder (hydration, medication, rest)."""
    reminder = HealthReminder(
        user_id=int(claims["sub"]),
        **data.model_dump()
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {
        "id": reminder.id,
        "reminder_type": reminder.reminder_type,
        "interval_minutes": reminder.interval_minutes,
        "message": reminder.message,
        "active": reminder.active
    }


@router.get("/health/reminders")
def list_health_reminders(claims=Depends(current_claims), db: Session = Depends(get_db)):
    user_id = int(claims["sub"])
    reminders = db.query(HealthReminder).filter_by(user_id=user_id, active=True).all()
    return [
        {
            "id": r.id,
            "reminder_type": r.reminder_type,
            "interval_minutes": r.interval_minutes,
            "message": r.message,
            "active": r.active
        }
        for r in reminders
    ]


# ──────────────────────── Notifications ────────────────────────
@router.get("/notifications")
def list_notifications(claims=Depends(current_claims), db: Session = Depends(get_db)):
    user_id = int(claims["sub"])
    notes = db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "category": n.category,
            "read": n.read,
            "created_at": n.created_at.isoformat()
        }
        for n in notes
    ]


@router.get("/notifications/smart")
def smart_notifications():
    """Generate intelligent notifications based on current context."""
    # Get current queue status for context
    queue_status = public_status()
    
    # Generate smart notifications
    notifications = generate_smart_notifications(
        queue_status=queue_status,
        weather_data={"temp": 24, "condition": "partly_cloudy"}  # Demo weather data
    )
    
    return {
        "notifications": notifications,
        "summary": get_notification_summary(notifications),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/notifications/read")
def mark_notifications_read(data: NotificationMarkRead, claims=Depends(current_claims), db: Session = Depends(get_db)):
    user_id = int(claims["sub"])
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.id.in_(data.notification_ids)
    ).update({"read": True}, synchronize_session=False)
    db.commit()
    return {"message": "Notifications marked as read."}


# ──────────────────────── Navigation / Map Locations ────────────────────────
@router.get("/maps/locations")
def map_locations(category: str | None = None, db: Session = Depends(get_db)):
    """Return stored GPS locations for Google Maps integration."""
    q = db.query(NavigationLocation)
    if category:
        q = q.filter_by(category=category)
    locations = q.all()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "category": loc.category,
            "description": loc.description,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "icon": loc.icon
        }
        for loc in locations
    ]


# ──────────────────────── User Profile ────────────────────────
@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "language": current_user.language,
        "phone": current_user.phone,
        "is_active": getattr(current_user, 'is_active', True),
        "age": profile.age if profile else None,
        "blood_group": profile.blood_group if profile else "",
        "medical_conditions": profile.medical_conditions if profile else "",
        "emergency_contact": profile.emergency_contact if profile else "",
        "wheelchair_required": profile.wheelchair_required if profile else False,
    }


@router.put("/profile")
def update_profile(data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        current_user.name = data.name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.language is not None:
        current_user.language = data.language

    # Profile fields
    if not current_user.profile:
        current_user.profile = PilgrimProfile(user_id=current_user.id)

    if data.age is not None:
        current_user.profile.age = data.age
    if data.blood_group is not None:
        current_user.profile.blood_group = data.blood_group
    if data.medical_conditions is not None:
        current_user.profile.medical_conditions = data.medical_conditions
    if data.emergency_contact is not None:
        current_user.profile.emergency_contact = data.emergency_contact
    if data.wheelchair_required is not None:
        current_user.profile.wheelchair_required = data.wheelchair_required

    db.commit()
    return {"message": "Profile updated successfully."}


# ──────────────────────── Admin Analytics ────────────────────────
@router.get("/admin/analytics")
def analytics(admin_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {
        "total_pilgrims": db.query(User).filter_by(role="pilgrim").count(),
        "total_users": db.query(User).count(),
        "active_queue": 0,
        "emergency_alerts_open": db.query(EmergencyAlert).filter_by(status="open").count(),
        "emergency_alerts_total": db.query(EmergencyAlert).count(),
        "lost_found_open": db.query(LostFound).filter_by(status="open").count(),
        "total_bookings": db.query(Booking).count(),
        "total_feedback": db.query(Feedback).count(),
        "total_chats": db.query(ChatHistory).filter_by(role="user").count(),
    }


@router.get("/admin/emergencies")
def admin_emergencies(admin_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    alerts = db.query(EmergencyAlert).order_by(EmergencyAlert.created_at.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "description": a.description,
            "status": a.status,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]
