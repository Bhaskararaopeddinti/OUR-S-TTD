"""
OURS TTD — Pydantic Schemas
Request/response validation models for all API endpoints.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
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

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    language: Optional[str] = "English"
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserOut] = None

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    medical_conditions: Optional[str] = None
    emergency_contact: Optional[str] = None
    wheelchair_required: Optional[bool] = None


# ──── Facilities ────
class FacilityUpdate(BaseModel):
    status: Optional[str] = "Operational"
    available: Optional[bool] = True
    wait_minutes: Optional[int] = 0


# ──── Chat ────
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "English"
    conversation_id: Optional[str] = None
    history: Optional[list[dict]] = None


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


# ──── Password Reset ────
class ForgotPasswordIn(BaseModel):
    email: EmailStr


# ──── Transport Routes ────
class TransportRouteIn(BaseModel):
    source_location: str = Field(min_length=2, max_length=120)
    destination_location: str = Field(min_length=2, max_length=120)
    vehicle_type: str = Field(min_length=2, max_length=40)
    operator: str = Field(default="APSRTC")
    route_name: str = Field(min_length=2, max_length=160)
    route_description: Optional[str] = ""
    estimated_duration: str = Field(default="45 mins")
    fare: str = Field(default="Free")
    operating_hours: str = Field(default="24/7 Active")
    frequency: str = Field(default="Continuous")
    status: str = Field(default="Available")
    data_status: str = Field(default="VERIFIED")
    source: str = Field(default="Official TTD Verified")
    source_url: str = Field(default="https://ttdevasthanams.ap.gov.in")

class TransportRouteUpdate(BaseModel):
    source_location: Optional[str] = None
    destination_location: Optional[str] = None
    vehicle_type: Optional[str] = None
    operator: Optional[str] = None
    route_name: Optional[str] = None
    route_description: Optional[str] = None
    estimated_duration: Optional[str] = None
    fare: Optional[str] = None
    operating_hours: Optional[str] = None
    frequency: Optional[str] = None
    status: Optional[str] = None
    data_status: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None



# ──── Crowd Upload & Analysis ────
class CrowdUploadIn(BaseModel):
    location_id: int = 1
    location_name: str = "Vaikuntam Queue Complex (VQC)"
    image_base64: Optional[str] = None
    manual_crowd_level: Optional[str] = None  # LOW, MODERATE, HIGH, VERY HIGH


# ──── Notifications ────
class NotificationMarkRead(BaseModel):
    notification_ids: list[int] = []


# ──── Admin Pilgrim Flow Data ────
class PilgrimFlowDataIn(BaseModel):
    date: str = Field(min_length=10, max_length=10)          # YYYY-MM-DD
    start_time: str = Field(min_length=4, max_length=5)       # HH:MM
    end_time: str = Field(min_length=4, max_length=5)         # HH:MM
    incoming_pilgrims: int = Field(ge=0, description="Must be >= 0")
    outgoing_pilgrims: int = Field(ge=0, description="Must be >= 0")
    festival: bool = False

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD format.") from exc
        return value

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("Time must use HH:MM (24-hour) format.") from exc
        return value

    @model_validator(mode="after")
    def validate_two_hour_slot(self):
        start = datetime.strptime(self.start_time, "%H:%M")
        end = datetime.strptime(self.end_time, "%H:%M")
        duration = (end - start).total_seconds() / 3600
        if duration <= 0:
            duration += 24
        if duration != 2:
            raise ValueError("Time slot must be exactly two hours.")
        if start.minute or end.minute or start.hour % 2:
            raise ValueError("Time slots must start and end on even-hour boundaries.")
        return self

class PilgrimFlowDataOut(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    incoming_pilgrims: int
    outgoing_pilgrims: int
    net_pilgrims: int
    estimated_crowd: int
    festival: bool
    queue_status: str
    queue_pressure: float
    created_at: str

class QueueAnalysisOut(BaseModel):
    current_crowd: int
    queue_status: str
    queue_pressure: float
    incoming_rate: int
    outgoing_rate: int
    net_rate: int
    trend: str
    prediction: str
    festival: bool
    total_incoming_today: int
    total_outgoing_today: int
    slots_recorded: int

class AdminDashboardOut(BaseModel):
    server_date: str
    server_time: str
    total_pilgrims_today: int
    current_crowd: int
    total_incoming: int
    total_outgoing: int
    queue_status: str
    predicted_crowd: int
    festival: bool
    slots_recorded: int
