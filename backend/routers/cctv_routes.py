"""
OURS TTD — CCTV AI Crowd Monitoring API Router
Handles video upload, starting/stopping AI analysis, querying live status,
streaming live annotated CCTV frames, and retrieving historical crowd records.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, CCTVCrowdRecord, PilgrimFlowData
from backend.auth import get_current_admin
from backend.services.cctv_vision import cctv_worker, DEFAULT_DEMO_VIDEO, FALLBACK_DEMO_VIDEO

router = APIRouter(prefix="/api/cctv", tags=["CCTV AI Crowd Monitoring"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "cctv"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class CCTVStartRequest(BaseModel):
    video_filename: Optional[str] = None
    location_name: Optional[str] = None
    camera_location: Optional[str] = None   # alias used by frontend
    direction_mode: str = "left_to_right"
    interval_minutes: int = 15
    camera_id: str = "CAM_01_DEMO"

    def resolved_location(self) -> str:
        """Return whichever location field was sent."""
        return self.camera_location or self.location_name or "Sarva Darshan VQC I"


# ─────────────────────────────────────────────────────────────────────────────
# 1. POST /api/cctv/upload (Admin Video Upload)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload")
async def upload_cctv_video(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    """
    Admin uploads a CCTV video for AI analysis.
    Validates file extension (.mp4, .avi, .mov, .mkv) and saves to server.
    """
    allowed_exts = {".mp4", ".avi", ".mov", ".mkv"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(400, f"Unsupported video format '{ext}'. Allowed: {', '.join(allowed_exts)}")

    # Sanitize filename
    safe_filename = Path(file.filename).name.replace(" ", "_")
    target_path = UPLOAD_DIR / safe_filename

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save video: {str(e)}")

    file_size_mb = target_path.stat().st_size / (1024 * 1024)

    return {
        "success": True,
        "filename": safe_filename,
        "original_filename": file.filename,
        "size_mb": round(file_size_mb, 2),
        "path": str(target_path),
        "message": "CCTV video uploaded successfully. Ready for AI analysis.",
        "source": "Demo CCTV AI Data"
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. POST /api/cctv/start (Start AI Video Analysis)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/start")
def start_cctv_analysis(
    req: CCTVStartRequest,
    admin: User = Depends(get_current_admin)
):
    """
    Start the CCTV AI video processing worker on the selected video.
    Defaults to the reference demo video if no file is specified.
    """
    selected_path = None
    if req.video_filename:
        # Check uploaded videos first
        uploaded = UPLOAD_DIR / req.video_filename
        if uploaded.exists():
            selected_path = str(uploaded)
        # Check demo media folder
        demo_named = Path(__file__).resolve().parent.parent / "demo_media" / req.video_filename
        if demo_named.exists():
            selected_path = str(demo_named)

    if not selected_path:
        if DEFAULT_DEMO_VIDEO.exists():
            selected_path = str(DEFAULT_DEMO_VIDEO)
        elif FALLBACK_DEMO_VIDEO.exists():
            selected_path = str(FALLBACK_DEMO_VIDEO)

    if not selected_path or not os.path.exists(selected_path):
        raise HTTPException(404, "Reference CCTV video file not found. Please upload a video first.")

    res = cctv_worker.start(
        video_path=selected_path,
        location_name=req.resolved_location(),
        direction_mode=req.direction_mode,
        interval_minutes=req.interval_minutes,
        camera_id=req.camera_id
    )

    if not res.get("success"):
        raise HTTPException(400, res.get("message", "Failed to start CCTV analysis."))

    return res


# ─────────────────────────────────────────────────────────────────────────────
# 3. POST /api/cctv/stop (Stop AI Video Analysis)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/stop")
def stop_cctv_analysis(admin: User = Depends(get_current_admin)):
    """Gracefully stop running CCTV AI analysis."""
    return cctv_worker.stop()


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /api/cctv/status (Current Worker Status & Live Metrics)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/status")
def get_cctv_status():
    """Return live worker status and metrics for admin and dashboards."""
    return cctv_worker.get_status()


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /api/cctv/current (Public / Dashboard Snapshot)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/current")
def get_cctv_current(db: Session = Depends(get_db)):
    """
    Public endpoint returning latest CCTV AI crowd snapshot.
    Falls back to most recent CCTVCrowdRecord or PilgrimFlowData in DB.
    """
    live_status = cctv_worker.get_status()
    if live_status.get("is_running"):
        return {
            "source": "demo_cctv_ai",
            "source_display": "Demo CCTV AI Data",
            "status": live_status["status"],
            "location": live_status["location_name"],
            "incoming": live_status["incoming"],
            "outgoing": live_status["outgoing"],
            "observed_count": live_status["observed_count"],
            "estimated_crowd": live_status["estimated_crowd"],
            "net_flow": live_status["net_flow"],
            "trend": live_status["trend"],
            "queue_status": live_status["queue_status"],
            "confidence": live_status["confidence"],
            "is_live_stream": True,
            "last_updated": live_status["last_updated"]
        }

    # If worker is not currently running, fetch the latest stored CCTV record
    latest_rec = (
        db.query(CCTVCrowdRecord)
        .order_by(desc(CCTVCrowdRecord.timestamp))
        .first()
    )

    if latest_rec:
        return {
            "source": latest_rec.source,
            "source_display": "Demo CCTV AI Data" if latest_rec.source == "demo_cctv_ai" else "CCTV AI Data",
            "status": "completed",
            "location": latest_rec.location_name,
            "incoming": latest_rec.incoming_count,
            "outgoing": latest_rec.outgoing_count,
            "observed_count": latest_rec.observed_count,
            "estimated_crowd": max(0, 1200 + latest_rec.net_flow),
            "net_flow": latest_rec.net_flow,
            "trend": latest_rec.trend,
            "queue_status": latest_rec.queue_status,
            "confidence": latest_rec.confidence,
            "is_live_stream": False,
            "last_updated": latest_rec.timestamp.isoformat()
        }

    return {
        "source": "none",
        "source_display": "No crowd data currently available.",
        "status": "idle",
        "incoming": 0,
        "outgoing": 0,
        "observed_count": 0,
        "estimated_crowd": 0,
        "net_flow": 0,
        "trend": "STABLE",
        "queue_status": "MODERATE",
        "confidence": 0.90,
        "is_live_stream": False,
        "last_updated": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. GET /api/cctv/recent (Recent Aggregated Records)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/recent")
def get_cctv_recent(limit: int = 20, db: Session = Depends(get_db)):
    """Retrieve recent aggregated time-slot records from CCTV analysis."""
    records = (
        db.query(CCTVCrowdRecord)
        .order_by(desc(CCTVCrowdRecord.timestamp))
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "camera_id": r.camera_id,
            "location_name": r.location_name,
            "timestamp": r.timestamp.isoformat(),
            "interval": f"{r.interval_start}–{r.interval_end}" if r.interval_start else "Live",
            "incoming_count": r.incoming_count,
            "outgoing_count": r.outgoing_count,
            "observed_count": r.observed_count,
            "net_flow": r.net_flow,
            "queue_status": r.queue_status,
            "trend": r.trend,
            "confidence": r.confidence,
            "source": r.source,
            "video_filename": r.video_filename
        }
        for r in records
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET /api/cctv/trend (Crowd Trend Analytics)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/trend")
def get_cctv_trend(db: Session = Depends(get_db)):
    """Retrieve trend analysis and summary metrics."""
    status = cctv_worker.get_status()
    records = (
        db.query(CCTVCrowdRecord)
        .order_by(desc(CCTVCrowdRecord.timestamp))
        .limit(10)
        .all()
    )

    flow_history = [
        {
            "time": r.timestamp.strftime("%H:%M"),
            "net_flow": r.net_flow,
            "incoming": r.incoming_count,
            "outgoing": r.outgoing_count,
            "observed": r.observed_count
        }
        for r in reversed(records)
    ]

    return {
        "current_trend": status["trend"],
        "queue_status": status["queue_status"],
        "observed_count": status["observed_count"],
        "incoming": status["incoming"],
        "outgoing": status["outgoing"],
        "net_flow": status["net_flow"],
        "history": flow_history,
        "source": "Demo CCTV AI Data"
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. GET /api/cctv/stream (MJPEG Live Stream)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/stream")
def stream_cctv_video():
    """
    MJPEG Live stream endpoint for the Admin Monitoring Console.
    Streams annotated frames with bounding boxes, person IDs, and counting line in real time.
    """
    def frame_generator():
        while True:
            frame_bytes = cctv_worker.get_jpeg_frame()
            if frame_bytes is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            time.sleep(0.04)  # ~25 FPS stream pacing

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
