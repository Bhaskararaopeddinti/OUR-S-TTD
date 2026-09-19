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
    mode: str = "demo_video"                 # "demo_video" or "rtsp_stream"
    video_filename: Optional[str] = None
    rtsp_url: Optional[str] = None           # e.g. "rtsp://camera_ip:554/live"
    location_name: Optional[str] = None
    camera_location: Optional[str] = None   # alias used by frontend
    direction_mode: str = "left_to_right"
    interval_minutes: int = 15
    camera_id: str = "CAM_01_DEMO"

    def resolved_location(self) -> str:
        """Return whichever location field was sent."""
        return self.camera_location or self.location_name or "Sarva Darshan VQC I"


# ─────────────────────────────────────────────────────────────────────────────
# 1. POST /api/cctv/upload (Admin Media Upload - Video or Image)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload")
async def upload_cctv_video(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    """
    Admin uploads a CCTV video or image for AI analysis.
    Validates file extension (.mp4, .avi, .mov, .mkv, .jpg, .jpeg, .png, .webp) and size.
    """
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv"}
    allowed_exts = image_exts | video_exts
    
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed videos: {', '.join(video_exts)} or images: {', '.join(image_exts)}"
        )

    media_type = "image" if ext in image_exts else "video"

    # Sanitize filename
    safe_filename = Path(file.filename).name.replace(" ", "_")
    target_path = UPLOAD_DIR / safe_filename

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save {media_type}: {str(e)}")

    file_size_bytes = target_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Size limit checks: 150MB for video, 25MB for image
    max_mb = 25.0 if media_type == "image" else 150.0
    if file_size_mb > max_mb:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File too large ({file_size_mb:.1f}MB). Maximum allowed is {max_mb}MB.")

    return {
        "success": True,
        "filename": safe_filename,
        "original_filename": file.filename,
        "media_type": media_type,
        "size_mb": round(file_size_mb, 2),
        "path": str(target_path),
        "message": f"CCTV {media_type} uploaded successfully. Ready for AI analysis.",
        "source": "Demo CCTV AI Data"
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. POST /api/cctv/start (Start AI Media Analysis - Video, Image, or RTSP Stream)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/start")
def start_cctv_analysis(
    req: CCTVStartRequest,
    admin: User = Depends(get_current_admin)
):
    """
    Start the CCTV AI video/image processing worker in either:
    - Mode 1: Demo Media Mode (source: demo_cctv_video or cctv_image)
    - Mode 2: Live IP CCTV Mode via RTSP stream (source: authorized_cctv)
    """
    if req.mode == "rtsp_stream" or (req.rtsp_url and req.rtsp_url.strip()):
        rtsp_clean = (req.rtsp_url or "").strip()
        if not rtsp_clean:
            raise HTTPException(status_code=400, detail="Live CCTV stream is not configured. Please provide an RTSP URL.")
        if not (rtsp_clean.startswith("rtsp://") or rtsp_clean.startswith("http://") or rtsp_clean.startswith("https://")):
            raise HTTPException(status_code=400, detail="Invalid RTSP/Stream URL. Must start with rtsp://, http://, or https://")

        res = cctv_worker.start(
            mode="rtsp_stream",
            rtsp_url=rtsp_clean,
            location_name=req.resolved_location(),
            direction_mode=req.direction_mode,
            interval_minutes=req.interval_minutes,
            camera_id=req.camera_id
        )
    else:
        selected_path = None
        if req.video_filename:
            # Check uploaded media first
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
            raise HTTPException(status_code=404, detail="Reference CCTV media file not found. Please upload a video or image first.")

        res = cctv_worker.start(
            mode="demo_video",
            video_path=selected_path,
            location_name=req.resolved_location(),
            direction_mode=req.direction_mode,
            interval_minutes=req.interval_minutes,
            camera_id=req.camera_id
        )

    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to start CCTV analysis."))

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
            "source_display": live_status.get("source_label", "Demo CCTV AI Data"),
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
        # Determine estimated crowd from observed or net flow without fake constants
        crowd_est = latest_rec.observed_count if latest_rec.observed_count > 0 else max(0, latest_rec.net_flow)
        return {
            "source": latest_rec.source,
            "source_display": "Demo CCTV AI Data" if latest_rec.source in ("demo_cctv_video", "cctv_image", "demo_cctv_ai") else "CCTV AI Data",
            "status": "completed",
            "location": latest_rec.location_name,
            "incoming": latest_rec.incoming_count,
            "outgoing": latest_rec.outgoing_count,
            "observed_count": latest_rec.observed_count,
            "estimated_crowd": crowd_est,
            "net_flow": latest_rec.net_flow,
            "trend": latest_rec.trend,
            "queue_status": latest_rec.queue_status,
            "confidence": latest_rec.confidence,
            "is_live_stream": False,
            "last_updated": latest_rec.timestamp.isoformat()
        }

    # Check if manual pilgrim flow records exist
    latest_flow = (
        db.query(PilgrimFlowData)
        .order_by(desc(PilgrimFlowData.date), desc(PilgrimFlowData.start_time))
        .first()
    )
    if latest_flow:
        net = latest_flow.incoming_pilgrims - latest_flow.outgoing_pilgrims
        return {
            "source": latest_flow.source or "manual_entry",
            "source_display": "Official Pilgrim Data" if latest_flow.source in ("manual", "manual_entry") else "Pilgrim Flow Data",
            "status": "completed",
            "location": "Sarva Darshan VQC I",
            "incoming": latest_flow.incoming_pilgrims,
            "outgoing": latest_flow.outgoing_pilgrims,
            "observed_count": latest_flow.estimated_crowd,
            "estimated_crowd": latest_flow.estimated_crowd,
            "net_flow": net,
            "trend": "INCREASING" if net > 50 else ("DECREASING" if net < -50 else "STABLE"),
            "queue_status": latest_flow.queue_status or "MODERATE",
            "confidence": 0.95,
            "is_live_stream": False,
            "last_updated": latest_flow.created_at.isoformat() if latest_flow.created_at else datetime.utcnow().isoformat()
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
        "queue_status": "No crowd data available",
        "confidence": 0.0,
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
