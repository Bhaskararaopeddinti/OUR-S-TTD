from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Facility, EmergencyAlert, Feedback, User
from backend.schemas import ChatIn, SOSIn, FeedbackIn
from backend.services.ai_service import pilgrim_reply
from backend.services.queue_prediction import predict
from backend.services.recommendation import recommendations
from backend.services.translation import supported_languages
from backend.auth import current_claims
from backend.services.ttd_official import public_status
from backend.services.facilities_data import FACILITIES
router = APIRouter(prefix="/api", tags=["Pilgrim services"])

@router.get("/queue")
def queue():
    """Public TTD status only; queue timing is intentionally not estimated from synthetic data."""
    return public_status()
@router.get("/facilities")
def facilities(kind: str | None = None):
    """Facility directory for the UI; no artificial distance or availability is returned."""
    rows = [x for x in FACILITIES if not kind or x["kind"] == kind]
    return {"verification":"Project-supplied facility information — verify operational details with TTD before travel.", "facilities": rows}
@router.post("/chat")
def chat(data: ChatIn): return {"reply": pilgrim_reply(data.message, data.language), "language": data.language}
@router.post("/sos")
def sos(data: SOSIn, db: Session = Depends(get_db)):
    alert = EmergencyAlert(**data.model_dump()); db.add(alert); db.commit(); db.refresh(alert)
    return {"id":alert.id,"status":"dispatched","message":"Your alert has been shared with the support desk. Stay in a safe visible place."}
@router.get("/recommendations")
def recommend(): return recommendations()
@router.get("/languages")
def languages(): return supported_languages()
@router.get("/notices")
def notices(): return [{"title":"Temple etiquette","body":"Traditional, modest attire is requested. Please follow volunteer directions."},{"title":"Keep hydrated","body":"Water points are available throughout the queue complex."}]
@router.get("/admin/analytics")
def analytics(claims=Depends(current_claims), db: Session=Depends(get_db)):
    if claims["role"] != "admin": raise HTTPException(403, "Admin access required")
    return {"total_pilgrims":db.query(User).count(),"active_queue":7420,"emergency_alerts":db.query(EmergencyAlert).filter_by(status="open").count(),"medical_requests":12,"food_demand":68,"volunteers":39}
@router.post("/feedback")
def feedback(data: FeedbackIn, db: Session = Depends(get_db)):
    row=Feedback(**data.model_dump()); db.add(row); db.commit(); return {"message":"Thank you for your feedback."}
