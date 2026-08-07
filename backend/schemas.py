"""
OURS TTD — Pydantic Schemas
Request/response validation models for all API endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ──── Authentication ────
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str = "pilgrim"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    medical_conditions: Optional[str] = None
    emergency_contact: Optional[str] = None
    wheelchair_required: Optional[bool] = None


# ──── Chat ────
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "English"
    conversation_id: Optional[str] = None


# ──── Emergency ────
class SOSIn(BaseModel):
    alert_type: str
    description: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ──── Feedback ────
class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(max_length=1000, default="")


# ──── Translation ────
class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_language: str = "English"


# ──── Navigation ────
class NearbyFacilitiesIn(BaseModel):
    latitude: float
    longitude: float
    max_distance: Optional[float] = None


# ──── Navigation Locations (Smart Navigation Module) ────
class NavigationLocationIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=40)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str = Field(max_length=255, default="")
    description: str = Field(max_length=2000, default="")
    opening_hours: str = Field(max_length=100, default="24/7")
    contact_number: str = Field(max_length=20, default="")
    wheelchair_accessible: bool = False
    source: str = Field(max_length=100, default="TTD Official")


class NavigationLocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    category: Optional[str] = Field(None, min_length=2, max_length=40)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    opening_hours: Optional[str] = Field(None, max_length=100)
    contact_number: Optional[str] = Field(None, max_length=20)
    wheelchair_accessible: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=100)


# ──── Booking ────
class BookingIn(BaseModel):
    booking_type: str = Field(pattern=r"^(darshan|accommodation|seva)$")
    date: str = Field(min_length=10, max_length=10)  # YYYY-MM-DD
    slot: str = ""
    notes: str = ""

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


# ──── Lost & Found ────
class LostFoundIn(BaseModel):
    report_type: str = Field(pattern=r"^(lost_item|found_item|lost_person|found_person)$")
    category: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=5, max_length=2000)
    contact_info: str = Field(max_length=160, default="")
    location: str = Field(max_length=120, default="")

class LostFoundUpdate(BaseModel):
    status: Optional[str] = None


# ──── Health ────
class HealthReminderIn(BaseModel):
    reminder_type: str = Field(pattern=r"^(hydration|medication|rest)$")
    interval_minutes: int = Field(ge=10, le=480, default=60)
    message: str = Field(max_length=200, default="")

class HealthReminderUpdate(BaseModel):
    active: Optional[bool] = None
    interval_minutes: Optional[int] = None


# ──── Notifications ────
class NotificationMarkRead(BaseModel):
    notification_ids: list[int] = []
