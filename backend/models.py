"""
OURS TTD — SQLAlchemy Models
All database tables for the pilgrim companion platform.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    """Registered pilgrim, volunteer, or admin user."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="pilgrim")
    language: Mapped[str] = mapped_column(String(20), default="English")
    phone: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reset_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["PilgrimProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_history: Mapped[list["ChatHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    health_reminders: Mapped[list["HealthReminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lost_found_reports: Mapped[list["LostFound"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PilgrimProfile(Base):
    """Extended profile for pilgrims — health, emergency contacts, preferences."""
    __tablename__ = "pilgrim_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_group: Mapped[str] = mapped_column(String(10), default="")
    medical_conditions: Mapped[str] = mapped_column(Text, default="")
    emergency_contact: Mapped[str] = mapped_column(String(160), default="")
    wheelchair_required: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="profile")


class QueueStatus(Base):
    """Live queue status snapshot."""
    __tablename__ = "queue_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String(80), default="Sarva Darshan")
    wait_minutes: Mapped[int] = mapped_column(Integer)
    crowd_density: Mapped[str] = mapped_column(String(20))
    people_count: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmergencyAlert(Base):
    """SOS emergency alert raised by a pilgrim."""
    __tablename__ = "emergency_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alert_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Facility(Base):
    """Known facility/landmark location within Tirumala."""
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(120))
    distance_m: Mapped[int] = mapped_column(Integer)
    wait_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hours: Mapped[str] = mapped_column(String(80), default="Open 24 hours")
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class Booking(Base):
    """Darshan / accommodation / seva booking (designed for future TTD API integration)."""
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    booking_type: Mapped[str] = mapped_column(String(40))  # darshan, accommodation, seva
    date: Mapped[str] = mapped_column(String(20))
    slot: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending_integration")
    notes: Mapped[str] = mapped_column(Text, default="Available after official TTD API integration.")
    qr_data: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="bookings")


class ChatHistory(Base):
    """Conversation log between pilgrim and AI assistant."""
    __tablename__ = "chat_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(10))  # user or assistant
    message: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="English")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User | None] = relationship(back_populates="chat_history")


class Notification(Base):
    """Push notification record for a user."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), default="info")  # info, alert, booking, health
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="notifications")


class HealthReminder(Base):
    """Health reminder (hydration, medication, rest) for a pilgrim."""
    __tablename__ = "health_reminders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reminder_type: Mapped[str] = mapped_column(String(30))  # hydration, medication, rest
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    message: Mapped[str] = mapped_column(String(200), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="health_reminders")


class LostFound(Base):
    """Lost & found item/person report."""
    __tablename__ = "lost_found"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(20))  # lost_item, found_item, lost_person, found_person
    category: Mapped[str] = mapped_column(String(40))  # child, elderly, bag, phone, jewellery, other
    description: Mapped[str] = mapped_column(Text)
    contact_info: Mapped[str] = mapped_column(String(160), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, matched, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User | None] = relationship(back_populates="lost_found_reports")


class Feedback(Base):
    """User feedback/rating for the platform."""
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NavigationLocation(Base):
    """Navigation location for Smart Navigation module with Leaflet.js and OpenStreetMap."""
    __tablename__ = "navigation_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    opening_hours: Mapped[str] = mapped_column(String(100), default="24/7")
    contact_number: Mapped[str] = mapped_column(String(20), default="")
    wheelchair_accessible: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(100), default="TTD Official")
    last_verified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Admin audit trail for security-sensitive actions."""
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransportType(Base):
    """Transport categories (e.g. APSRTC Bus, TTD Free Bus, Dharma Radham, Package Tour, Taxi, Walking)."""
    __tablename__ = "transport_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    operator: Mapped[str] = mapped_column(String(100), default="APSRTC / TTD")
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(100), default="Official TTD")
    source_url: Mapped[str] = mapped_column(String(255), default="https://ttdevasthanams.ap.gov.in")
    last_verified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(40), default="Active")


class TransportRoute(Base):
    """Verified travel and transport route details."""
    __tablename__ = "transport_routes"
    id: Mapped[int] = mapped_column(primary_key=True)
    transport_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_location_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_location_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_location: Mapped[str] = mapped_column(String(120), index=True)
    destination_location: Mapped[str] = mapped_column(String(120), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(40), index=True) # GOVERNMENT_BUS, TTD_BUS, TAXI, AUTO, WALKING, PACKAGE_TOUR
    operator: Mapped[str] = mapped_column(String(100), default="APSRTC")
    route_name: Mapped[str] = mapped_column(String(160))
    route_description: Mapped[str] = mapped_column(Text, default="")
    estimated_duration: Mapped[str] = mapped_column(String(60), default="45 mins")
    fare: Mapped[str] = mapped_column(String(60), default="Free")
    operating_hours: Mapped[str] = mapped_column(String(80), default="24/7 Active")
    frequency: Mapped[str] = mapped_column(String(80), default="Continuous")
    booking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    data_status: Mapped[str] = mapped_column(String(40), default="VERIFIED") # VERIFIED, NEEDS_REVIEW, OUTDATED, INACTIVE
    status: Mapped[str] = mapped_column(String(40), default="Available")
    live_status: Mapped[str] = mapped_column(String(60), default="Live tracking unavailable")
    current_location: Mapped[str] = mapped_column(String(120), default="")
    eta: Mapped[str] = mapped_column(String(40), default="")
    next_stop: Mapped[str] = mapped_column(String(120), default="")
    vehicle_id: Mapped[str] = mapped_column(String(60), default="")
    gps_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="TTD Official Verified")
    source_url: Mapped[str] = mapped_column(String(255), default="https://ttdevasthanams.ap.gov.in")
    last_verified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransportStop(Base):
    """Intermediate or destination stop along a transport route."""
    __tablename__ = "transport_stops"
    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    location_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    transport_type: Mapped[str] = mapped_column(String(40), default="Bus")
    source: Mapped[str] = mapped_column(String(100), default="Official TTD")
    last_verified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class CrowdAnalysis(Base):
    """Computer vision crowd analysis from admin uploaded images."""
    __tablename__ = "crowd_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(Integer, default=1)
    location_name: Mapped[str] = mapped_column(String(120), default="Sarva Darshan VQC")
    image_url: Mapped[str] = mapped_column(Text, default="")
    crowd_level: Mapped[str] = mapped_column(String(20)) # LOW, MODERATE, HIGH, VERY HIGH
    detected_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.92)
    admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QueueRecord(Base):
    """Structured darshan queue record with source tracking."""
    __tablename__ = "queue_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(Integer, default=1)
    location_name: Mapped[str] = mapped_column(String(120), default="Vaikuntam Queue Complex (VQC)")
    crowd_level: Mapped[str] = mapped_column(String(20), default="MODERATE")
    estimated_wait_minutes: Mapped[int] = mapped_column(Integer, default=180)
    source: Mapped[str] = mapped_column(String(40), default="AI_PREDICTION") # ADMIN_IMAGE, MANUAL_ADMIN, OFFICIAL_TTD_API, AI_PREDICTION, DEMO
    confidence: Mapped[float] = mapped_column(Float, default=0.90)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

