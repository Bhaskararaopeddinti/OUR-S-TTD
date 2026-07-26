from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="pilgrim")
    language: Mapped[str] = mapped_column(String(20), default="English")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped["PilgrimProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class PilgrimProfile(Base):
    __tablename__ = "pilgrim_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    medical_conditions: Mapped[str] = mapped_column(Text, default="")
    emergency_contact: Mapped[str] = mapped_column(String(160), default="")
    user: Mapped[User] = relationship(back_populates="profile")

class QueueStatus(Base):
    __tablename__ = "queue_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String(80), default="Sarva Darshan")
    wait_minutes: Mapped[int] = mapped_column(Integer)
    crowd_density: Mapped[str] = mapped_column(String(20))
    people_count: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(120))
    distance_m: Mapped[int] = mapped_column(Integer)
    wait_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hours: Mapped[str] = mapped_column(String(80), default="Open 24 hours")
    available: Mapped[bool] = mapped_column(Boolean, default=True)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
