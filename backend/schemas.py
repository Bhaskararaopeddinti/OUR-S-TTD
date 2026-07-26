from pydantic import BaseModel, EmailStr, Field
from typing import Optional

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
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    language: str = "English"
class SOSIn(BaseModel):
    alert_type: str
    description: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(max_length=1000, default="")
class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_language: str = "English"
class NearbyFacilitiesIn(BaseModel):
    latitude: float
    longitude: float
    max_distance: Optional[float] = None
