"""
OURS TTD — CCTV AI Vision Service
Automatic CCTV/video-based people counting, person tracking, virtual line crossing detection,
time-based crowd aggregation, and real-time streaming for queue intelligence.

NOTE: All outputs from video processing are tagged strictly as "Demo CCTV AI Data"
unless an authorized live TTD CCTV stream is connected.
"""

import os
import time
import math
import logging
import threading
from datetime import datetime, date as dt_date, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Absolute paths
ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_PATH = ROOT / "yolov8n.pt"

# Default reference video path
DEFAULT_DEMO_VIDEO = Path(__file__).resolve().parent.parent / "demo_media" / "demo_cctv.mp4"
FALLBACK_DEMO_VIDEO = Path(__file__).resolve().parent.parent / "demo_media" / "WhatsApp Video 2026-08-30 at 5.29.14 PM.mp4"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Simple / Centroid Object Tracker & Track State
# ─────────────────────────────────────────────────────────────────────────────
class TrackedPerson:
    """Represents a single tracked individual across video frames."""

    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], centroid: Tuple[int, int]):
        self.track_id = track_id
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.centroid = centroid  # (cx, cy)
        self.history: List[Tuple[int, int]] = [centroid]  # past centroids
        self.counted_in: bool = False
        self.counted_out: bool = False
        self.last_seen_frame: int = 0
        self.disappeared: int = 0
        self.first_seen: float = time.time()
        self.confidence: float = 0.90

    def update(self, bbox: Tuple[int, int, int, int], centroid: Tuple[int, int], frame_idx: int, conf: float = 0.90):
        self.bbox = bbox
        self.centroid = centroid
        self.history.append(centroid)
        if len(self.history) > 60:
            self.history.pop(0)
        self.last_seen_frame = frame_idx
        self.disappeared = 0
        self.confidence = conf


class SimpleObjectTracker:
    """
    Centroid & IoU-based multi-object tracker for people across frames.
    Maintains persistent IDs and prevents ID switching.
    """

    def __init__(self, max_disappeared: int = 25, max_distance: float = 85.0):
        self.next_id: int = 1
        self.tracks: Dict[int, TrackedPerson] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, detections: List[Tuple[Tuple[int, int, int, int], float]], frame_idx: int) -> List[TrackedPerson]:
        """
        detections: list of ((x1, y1, x2, y2), confidence) for person class only.
        """
        if not detections:
            # Mark all existing tracks as disappeared
            to_remove = []
            for track_id, track in self.tracks.items():
                track.disappeared += 1
                if track.disappeared > self.max_disappeared:
                    to_remove.append(track_id)
            for track_id in to_remove:
                del self.tracks[track_id]
            return list(self.tracks.values())

        input_centroids = []
        input_bboxes = []
        input_confs = []
        for bbox, conf in detections:
            x1, y1, x2, y2 = bbox
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            input_centroids.append((cx, cy))
            input_bboxes.append(bbox)
            input_confs.append(conf)

        if not self.tracks:
            # Register all incoming detections as new tracks
            for i, centroid in enumerate(input_centroids):
                track = TrackedPerson(self.next_id, input_bboxes[i], centroid)
                track.last_seen_frame = frame_idx
                track.confidence = input_confs[i]
                self.tracks[self.next_id] = track
                self.next_id += 1
            return list(self.tracks.values())

        # Match existing tracks to new detections by Euclidean distance
        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[tid].centroid for tid in track_ids]

        # Compute pairwise distance matrix
        D = np.zeros((len(track_centroids), len(input_centroids)), dtype=np.float32)
        for r, tc in enumerate(track_centroids):
            for c, ic in enumerate(input_centroids):
                D[r, c] = math.hypot(tc[0] - ic[0], tc[1] - ic[1])

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            if D[row, col] > self.max_distance:
                continue

            track_id = track_ids[row]
            self.tracks[track_id].update(
                input_bboxes[col], input_centroids[col], frame_idx, input_confs[col]
            )
            used_rows.add(row)
            used_cols.add(col)

        unused_rows = set(range(len(track_centroids))) - used_rows
        unused_cols = set(range(len(input_centroids))) - used_cols

        # Increment disappeared for unmatched existing tracks
        for row in unused_rows:
            track_id = track_ids[row]
            self.tracks[track_id].disappeared += 1
            if self.tracks[track_id].disappeared > self.max_disappeared:
                del self.tracks[track_id]

        # Register new detections as new tracks
        for col in unused_cols:
            track = TrackedPerson(self.next_id, input_bboxes[col], input_centroids[col])
            track.last_seen_frame = frame_idx
            track.confidence = input_confs[col]
            self.tracks[self.next_id] = track
            self.next_id += 1

        return list(self.tracks.values())


# ─────────────────────────────────────────────────────────────────────────────
# 2. Virtual Counting Line & Crossing Logic
# ─────────────────────────────────────────────────────────────────────────────
def _ccw(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int]) -> float:
    """Counter-clockwise 2D orientation test."""
    return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0])


def check_line_crossing(
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    line_start: Tuple[int, int],
    line_end: Tuple[int, int],
    direction_mode: str = "left_to_right",
    deadzone: float = 2.0
) -> Tuple[bool, Optional[str]]:
    """
    Determines if person movement from p1 to p2 crossed virtual line (line_start -> line_end).
    Returns (crossed: bool, direction: 'IN' | 'OUT' | None).
    Accurately handles Left -> Right (IN) and Right -> Left (OUT).
    """
    # 1. Broad-phase bounding box rejection
    min_px, max_px = min(p1[0], p2[0]) - 8, max(p1[0], p2[0]) + 8
    min_py, max_py = min(p1[1], p2[1]) - 8, max(p1[1], p2[1]) + 8
    min_lx, max_lx = min(line_start[0], line_end[0]), max(line_start[0], line_end[0])
    min_ly, max_ly = min(line_start[1], line_end[1]), max(line_start[1], line_end[1])

    if max_px < min_lx or min_px > max_lx or max_py < min_ly or min_py > max_ly:
        return False, None

    # 2. Narrow-phase 2D orientation segment intersection
    d1 = _ccw(line_start, line_end, p1)
    d2 = _ccw(line_start, line_end, p2)
    d3 = _ccw(p1, p2, line_start)
    d4 = _ccw(p1, p2, line_end)

    straddles_line = (d1 * d2 < -deadzone)
    straddles_segment = (d3 * d4 <= 0)

    if straddles_line and straddles_segment:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        if direction_mode in ("left_to_right", "right_to_left"):
            # Horizontal motion evaluation
            if dx > 0:
                dir_label = "IN" if direction_mode == "left_to_right" else "OUT"
            elif dx < 0:
                dir_label = "OUT" if direction_mode == "left_to_right" else "IN"
            else:
                dir_label = "IN" if d2 < 0 else "OUT"
        else:
            # Vertical motion evaluation
            if dy > 0:
                dir_label = "IN" if direction_mode == "top_to_bottom" else "OUT"
            elif dy < 0:
                dir_label = "OUT" if direction_mode == "top_to_bottom" else "IN"
            else:
                dir_label = "IN" if d2 < 0 else "OUT"

        return True, dir_label

    return False, None


def suppress_nested_boxes(
    detections: List[Tuple[Tuple[int, int, int, int], float]],
    ios_threshold: float = 0.70
) -> List[Tuple[Tuple[int, int, int, int], float]]:
    """
    Remove nested duplicate detections (e.g. torso inside full body) of the same person.
    Uses Intersection over Smaller (IoS). If a smaller box is largely inside a larger one,
    we suppress the lower-confidence duplicate.
    """
    if len(detections) <= 1:
        return detections
    sorted_dets = sorted(detections, key=lambda d: d[1], reverse=True)
    kept = []
    for bbox, conf in sorted_dets:
        x1, y1, x2, y2 = bbox
        area = max(1, (x2 - x1) * (y2 - y1))
        is_duplicate = False
        for k_bbox, k_conf in kept:
            kx1, ky1, kx2, ky2 = k_bbox
            k_area = max(1, (kx2 - kx1) * (ky2 - ky1))
            ix1, iy1 = max(x1, kx1), max(y1, ky1)
            ix2, iy2 = min(x2, kx2), min(y2, ky2)
            iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
            inter = iw * ih
            if inter > 0:
                ios = inter / min(area, k_area)
                if ios >= ios_threshold:
                    is_duplicate = True
                    break
        if not is_duplicate:
            kept.append((bbox, conf))
    return kept


# ─────────────────────────────────────────────────────────────────────────────
# 3. YOLO Model Loader (Ultralytics YOLOv8 Person Detector)
# ─────────────────────────────────────────────────────────────────────────────
class YOLOPersonDetector:
    """Detects people in frames using YOLO (COCO class 0 'person' only)."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        conf_threshold: float = 0.20,
        iou_threshold: float = 0.45
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self.model_path = None
        self.backend_type = "ultralytics_yolo"

        if not model_name:
            if DEFAULT_MODEL_PATH.exists():
                self.model_path = DEFAULT_MODEL_PATH
            else:
                self.model_path = ROOT / "yolov8n.pt"
        else:
            self.model_path = Path(model_name).resolve()

        self._init_model(str(self.model_path))

    def _init_model(self, model_path_str: str):
        path = Path(model_path_str)
        if not path.exists():
            error_msg = f"YOLO model file not found at {path}. Model weights are required."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            from ultralytics import YOLO
            logger.info("Loading YOLO model from verified path: %s", path)
            self.model = YOLO(str(path))
            # Verify person class
            person_cls_name = self.model.names.get(0, "unknown")
            if person_cls_name != "person":
                logger.warning("Class 0 is '%s', expected 'person'", person_cls_name)
            logger.info("✓ YOLO person detection model loaded successfully (Class 0: %s)", person_cls_name)
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)
            raise RuntimeError(f"YOLO model initialization failed: {e}")

    def detect_people(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Run person detection on a BGR frame.
        Returns: list of ((x1, y1, x2, y2), confidence) for COCO class 0 (person).
        Includes aspect-ratio preserving dynamic imgsz and nested-box suppression.
        """
        if frame is None or self.model is None:
            return []

        h, w = frame.shape[:2]
        if h <= 0 or w <= 0:
            return []

        conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        iou = iou_threshold if iou_threshold is not None else self.iou_threshold

        # Preserve aspect ratio and scale up for small people in large images
        imgsz = max(640, min(1280, max(w, h)))
        imgsz = int(np.ceil(imgsz / 32) * 32)

        try:
            results = self.model(
                frame,
                classes=[0],
                conf=conf,
                iou=iou,
                imgsz=imgsz,
                verbose=False
            )
            raw_detections = []
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        if cls_id == 0:  # strictly person
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            box_conf = float(box.conf[0].item())
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(w - 1, x2), min(h - 1, y2)
                            raw_detections.append(((x1, y1, x2, y2), box_conf))

            # Suppress nested duplicates (torso inside full body of same person)
            final_detections = suppress_nested_boxes(raw_detections, ios_threshold=0.70)
            logger.debug(
                "YOLO Person Detection: %dx%d image -> %d raw, %d final persons (conf=%.2f, iou=%.2f)",
                w, h, len(raw_detections), len(final_detections), conf, iou
            )
            return final_detections
        except Exception as e:
            logger.error("YOLO inference failed: %s", e)
            raise RuntimeError(f"YOLO inference error: {e}")

    def annotate_image(
        self,
        frame: np.ndarray,
        detections: List[Tuple[Tuple[int, int, int, int], float]],
        location_name: str = "Sarva Darshan VQC I"
    ) -> np.ndarray:
        """Annotate frame with bounding boxes, confidence badges, centroids, and HUD."""
        try:
            import cv2
        except ImportError:
            return frame

        h, w = frame.shape[:2]
        # Draw bounding boxes
        for i, (bbox, conf) in enumerate(detections, 1):
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)
            label = f"Person #{i} ({int(conf * 100)}%)"
            label_y = max(22, y1 - 8)
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x1, label_y - lh - 6), (x1 + lw + 10, label_y + 4), (0, 255, 128), -1)
            cv2.putText(frame, label, (x1 + 5, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        # Top HUD banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 68), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        cv2.putText(frame, "OURS TTD - AI PERSON DETECTION & CROWD COUNTING", (14, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Location: {location_name} | YOLOv8n (COCO Class 0)", (14, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 220, 240), 1, cv2.LINE_AA)

        count_str = f"DETECTED PEOPLE: {len(detections)}"
        cv2.putText(frame, count_str, (max(10, w - 380), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (50, 255, 120), 2, cv2.LINE_AA)

        status_str = f"Conf: {self.conf_threshold:.2f} | IoU: {self.iou_threshold:.2f}"
        cv2.putText(frame, status_str, (max(10, w - 380), 50), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 220, 240), 1, cv2.LINE_AA)

        return frame


# ─────────────────────────────────────────────────────────────────────────────
# 4. Asynchronous CCTV Video Processing Worker
# ─────────────────────────────────────────────────────────────────────────────
class CCTVVisionWorker:
    """
    Background worker that continuously processes an uploaded CCTV video file, image, or stream,
    performs person detection, tracks people, counts line crossings, aggregates time data,
    stores records in Supabase/PostgreSQL/SQLite, and broadcasts real-time updates.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.should_stop: bool = False
        self.is_image_mode: bool = False

        # Configuration
        self.mode: str = "demo_video"  # "demo_video" or "rtsp_stream"
        self.video_path: str = ""
        self.video_filename: str = ""
        self.rtsp_url: str = ""
        self.location_name: str = "Sarva Darshan VQC I"
        self.location_id: int = 1
        self.camera_id: str = "CAM_01_DEMO"
        self.direction_mode: str = "left_to_right"
        self.interval_minutes: int = 15
        self.source_label: str = "Demo CCTV AI Data"
        self.source_db_code: str = "demo_cctv_video"

        # Virtual counting line (normalized 0.0-1.0)
        self.line_coords_norm: Tuple[Tuple[float, float], Tuple[float, float]] = ((0.5, 0.1), (0.5, 0.9))

        # Runtime Stats & Metrics (Lifecycle states: IDLE, PROCESSING, COMPLETED, STOPPED, ERROR)
        self.status: str = "IDLE"
        self.error_message: str = ""
        self.current_frame_idx: int = 0
        self.total_frames: int = 0
        self.fps: float = 30.0

        self.observed_count: int = 0
        self.incoming_count: int = 0
        self.outgoing_count: int = 0
        self.net_flow: int = 0
        self.estimated_crowd: int = 0
        self.queue_status: str = "LOW"
        self.trend: str = "STABLE"
        self.confidence: float = 0.92
        self.video_quality_warning: bool = False

        # Live Annotated Frame Buffer for MJPEG Stream (Transient, in-memory only)
        self.latest_jpeg_frame: Optional[bytes] = None
        self.last_update_time: datetime = datetime.utcnow()

        # Trend history buffer
        self.recent_net_history: List[int] = []

        # Lazy detector & tracker
        self.detector: Optional[YOLOPersonDetector] = None
        self.tracker: Optional[SimpleObjectTracker] = None

    def start(
        self,
        mode: str = "demo_video",
        video_path: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        location_name: str = "Sarva Darshan VQC I",
        direction_mode: str = "left_to_right",
        interval_minutes: int = 15,
        camera_id: str = "CAM_01_DEMO"
    ) -> Dict[str, Any]:
        """
        Start the CCTV AI processing worker for uploaded video, single image, or RTSP stream.
        """
        with self.lock:
            # Check thread liveness to prevent orphaned lock
            if self.is_running:
                if self.thread and self.thread.is_alive():
                    return {"success": False, "message": "CCTV processing is already running."}
                else:
                    self.is_running = False

            self.mode = mode

            # Handle MODE 2: Live IP CCTV / RTSP Stream
            if mode == "rtsp_stream" or (rtsp_url and rtsp_url.strip()):
                self.rtsp_url = (rtsp_url or "").strip()
                if not self.rtsp_url:
                    return {"success": False, "message": "Live CCTV stream is not configured."}
                self.video_path = self.rtsp_url
                self.video_filename = f"RTSP Stream ({camera_id})"
                self.source_label = "Authorized CCTV Stream"
                self.source_db_code = "authorized_cctv"
            else:
                # Handle MODE 1: Demo Video Mode / Uploaded Media
                self.mode = "demo_video"
                self.source_label = "Demo CCTV AI Data"
                self.source_db_code = "demo_cctv_video"
                if not video_path or not os.path.exists(video_path):
                    if DEFAULT_DEMO_VIDEO.exists():
                        self.video_path = str(DEFAULT_DEMO_VIDEO)
                    elif FALLBACK_DEMO_VIDEO.exists():
                        self.video_path = str(FALLBACK_DEMO_VIDEO)
                    else:
                        return {"success": False, "message": "Reference media not found on server. Please upload a video or image first."}
                else:
                    self.video_path = video_path

                self.video_filename = Path(self.video_path).name

            # Detect whether input is an IMAGE or a VIDEO
            ext = Path(self.video_path).suffix.lower()
            self.is_image_mode = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
            if self.is_image_mode:
                self.source_db_code = "cctv_image"
                self.source_label = "Demo CCTV AI Data (Image)"

            self.location_name = location_name
            self.direction_mode = direction_mode
            self.interval_minutes = interval_minutes if interval_minutes in (15, 30, 60, 120) else 15
            self.camera_id = camera_id
            self.status = "PROCESSING"
            self.error_message = ""
            self.should_stop = False
            self.is_running = True

            # Reset counts for fresh session
            self.incoming_count = 0
            self.outgoing_count = 0
            self.net_flow = 0
            self.observed_count = 0
            self.recent_net_history = []
            self.current_frame_idx = 0

            # Adjust virtual counting line based on direction
            if direction_mode in ("left_to_right", "right_to_left"):
                self.line_coords_norm = ((0.5, 0.05), (0.5, 0.95))
            else:
                self.line_coords_norm = ((0.05, 0.5), (0.95, 0.5))

            if self.is_image_mode:
                self.thread = threading.Thread(target=self._process_image_job, daemon=True)
            else:
                self.thread = threading.Thread(target=self._process_video_loop, daemon=True)
            self.thread.start()

            logger.info("Started CCTV AI Worker [%s] for: %s (Location: %s, Media: %s)",
                        self.source_db_code, self.video_filename, location_name,
                        "IMAGE" if self.is_image_mode else "VIDEO")
            return {
                "success": True,
                "status": "PROCESSING",
                "mode": self.mode,
                "media_type": "IMAGE" if self.is_image_mode else "VIDEO",
                "is_image": self.is_image_mode,
                "video": self.video_filename,
                "location": self.location_name,
                "source": self.source_label,
                "source_db": self.source_db_code,
                "interval_minutes": self.interval_minutes
            }

    def stop(self) -> Dict[str, Any]:
        """Gracefully stop the background CCTV worker and release resources."""
        with self.lock:
            if not self.is_running:
                return {"success": True, "status": self.status, "message": "CCTV processing is not running."}
            self.should_stop = True
            self.status = "STOPPED"

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        with self.lock:
            self.is_running = False

        if self.current_frame_idx > 0:
            try:
                self._save_aggregated_record_to_db()
            except Exception as err:
                logger.warning("Could not persist final CCTV record on stop: %s", err)

        self._broadcast_update()
        logger.info("Stopped CCTV AI Video Worker.")
        return {"success": True, "status": "STOPPED", "message": "CCTV processing stopped."}

    def get_status(self) -> Dict[str, Any]:
        """Return current status and metrics of the CCTV Vision Worker."""
        with self.lock:
            return {
                "status": self.status,
                "is_running": self.is_running,
                "is_image": getattr(self, "is_image_mode", False),
                "media_type": "IMAGE" if getattr(self, "is_image_mode", False) else "VIDEO",
                "video_file": self.video_filename or "demo_cctv.mp4",
                "location_name": self.location_name,
                "camera_id": self.camera_id,
                "direction_mode": self.direction_mode,
                "incoming": None if getattr(self, "is_image_mode", False) else self.incoming_count,
                "outgoing": None if getattr(self, "is_image_mode", False) else self.outgoing_count,
                "incoming_display": "N/A (Still Image)" if getattr(self, "is_image_mode", False) else str(self.incoming_count),
                "outgoing_display": "N/A (Still Image)" if getattr(self, "is_image_mode", False) else str(self.outgoing_count),
                "observed_count": self.observed_count,
                "total_unique_tracked": getattr(self, "total_unique_tracked", self.observed_count),
                "net_flow": None if getattr(self, "is_image_mode", False) else self.net_flow,
                "estimated_crowd": self.estimated_crowd,
                "queue_status": self.queue_status,
                "trend": "N/A" if getattr(self, "is_image_mode", False) else self.trend,
                "confidence": round(self.confidence, 2),
                "source": self.source_label,
                "source_db": self.source_db_code,
                "video_quality_warning": self.video_quality_warning,
                "current_frame": self.current_frame_idx,
                "total_frames": self.total_frames,
                "last_updated": self.last_update_time.isoformat(),
                "error_message": self.error_message if self.status == "ERROR" else None,
            }

    def get_jpeg_frame(self) -> Optional[bytes]:
        """Retrieve latest annotated JPEG frame for live stream."""
        return self.latest_jpeg_frame

    # ─────────────────────────────────────────────────────────────────────────
    # Single Still Image Processing & Headcount Detection
    # ─────────────────────────────────────────────────────────────────────────
    def analyze_image(self, image_path: str, location_name: str = "Sarva Darshan VQC I") -> Dict[str, Any]:
        """
        Synchronously analyze an uploaded photo to detect headcount / people count,
        generate bounding-box annotations, save the annotated image, and update status.
        """
        import cv2
        from pathlib import Path

        img_p = Path(image_path)
        if not img_p.exists() or img_p.stat().st_size == 0:
            with self.lock:
                self.status = "ERROR"
                self.error_message = f"Image file does not exist or is empty: {img_p.name}"
            return {
                "success": False,
                "headcount": 0,
                "observed_count": 0,
                "message": f"Image file not found or empty: {img_p.name}"
            }

        with self.lock:
            self.mode = "demo_video"
            self.is_image_mode = True
            self.video_path = image_path
            self.video_filename = img_p.name
            self.source_label = "Demo CCTV AI Data (Image)"
            self.source_db_code = "cctv_image"
            self.location_name = location_name
            self.direction_mode = "still_photo"
            self.status = "PROCESSING"
            self.is_running = False

        if self.detector is None:
            self.detector = YOLOPersonDetector()

        static_img = cv2.imread(image_path)
        if static_img is None or static_img.shape[0] == 0 or static_img.shape[1] == 0:
            with self.lock:
                self.status = "ERROR"
                self.error_message = f"Unable to decode uploaded image: {img_p.name}"
            return {
                "success": False,
                "headcount": 0,
                "observed_count": 0,
                "message": f"Unable to decode uploaded image: {img_p.name}. Image format may be corrupt or unsupported."
            }

        frame_height, frame_width = static_img.shape[:2]
        self.total_frames = 1
        self.current_frame_idx = 1
        self.fps = 1.0

        detections = self.detector.detect_people(static_img)
        headcount = len(detections)
        self.observed_count = headcount
        self.total_unique_tracked = headcount
        self.incoming_count = 0
        self.outgoing_count = 0
        self.net_flow = 0
        self.estimated_crowd = headcount

        # Queue Status Classification for Still Crowd Image
        if headcount < 10:
            self.queue_status = "LOW"
        elif headcount < 25:
            self.queue_status = "MODERATE"
        elif headcount < 50:
            self.queue_status = "HIGH"
        else:
            self.queue_status = "VERY HIGH"

        self.trend = "STABLE"
        if detections:
            self.confidence = sum(d[1] for d in detections) / len(detections)
        else:
            self.confidence = 0.90

        self.last_update_time = datetime.utcnow()

        # Render image HUD with bounding boxes and clear headcount
        annotated = self._render_image_hud(static_img.copy(), detections, frame_width, frame_height)

        # Save annotated image next to original
        annotated_filename = f"annotated_{img_p.name}"
        annotated_path = img_p.parent / annotated_filename
        try:
            cv2.imwrite(str(annotated_path), annotated)
        except Exception as save_err:
            logger.warning("Could not save annotated image: %s", save_err)

        _, jpeg_buffer = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        self.latest_jpeg_frame = jpeg_buffer.tobytes()

        # Save record to database
        self._save_aggregated_record_to_db()

        with self.lock:
            self.status = "COMPLETED"
            self.is_running = False

        self._broadcast_update()
        logger.info("CCTV Image AI Analysis completed: %d people detected on photo.", headcount)

        return {
            "success": True,
            "headcount": headcount,
            "observed_count": headcount,
            "queue_status": self.queue_status,
            "confidence": round(self.confidence, 2),
            "annotated_filename": annotated_filename,
            "annotated_url": f"/uploads/cctv/{annotated_filename}",
            "message": f"Headcount detected: {headcount} people on photo.",
            "source": self.source_label
        }

    def _process_image_job(self):
        try:
            self.analyze_image(self.video_path, self.location_name)
        except Exception as e:
            logger.error("CCTV Image Worker error: %s", e)
            with self.lock:
                self.status = "ERROR"
                self.error_message = f"Image analysis error: {str(e)}"
                self.is_running = False
            self._broadcast_update()

    def _render_image_hud(
        self,
        frame: np.ndarray,
        detections: List[Tuple[Tuple[int, int, int, int], float]],
        w: int,
        h: int
    ) -> np.ndarray:
        try:
            import cv2
        except ImportError:
            return frame

        # Draw detected persons bounding boxes
        for i, (bbox, conf) in enumerate(detections, 1):
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)
            label = f"Person #{i} ({int(conf * 100)}%)"
            label_y = max(22, y1 - 8)
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x1, label_y - lh - 6), (x1 + lw + 10, label_y + 4), (0, 255, 128), -1)
            cv2.putText(frame, label, (x1 + 5, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
            # Centroid point
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        # Top HUD Banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 68), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        cv2.putText(frame, "OURS TTD - AI PHOTO HEADCOUNT ANALYSIS", (14, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Location: {self.location_name} | YOLOv8n Person Class 0", (14, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 220, 240), 1, cv2.LINE_AA)

        counter_str = f"HEADCOUNT: {self.observed_count} PEOPLE DETECTED"
        cv2.putText(frame, counter_str, (max(10, w - 430), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (50, 255, 120), 2, cv2.LINE_AA)

        status_color = (0, 255, 0) if self.queue_status == "LOW" else ((0, 215, 255) if self.queue_status == "MODERATE" else (0, 0, 255))
        status_str = f"QUEUE STATUS: {self.queue_status}"
        cv2.putText(frame, status_str, (max(10, w - 430), 50), cv2.FONT_HERSHEY_SIMPLEX, 0.50, status_color, 2, cv2.LINE_AA)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    # Video Processing Loop (ByteTrack Persistent Tracking & Line Crossing)
    # ─────────────────────────────────────────────────────────────────────────
    def _process_video_loop(self):
        cap = None
        frame_idx = 0
        try:
            import cv2
            if self.detector is None:
                self.detector = YOLOPersonDetector()

            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                logger.error("Failed to open video file: %s", self.video_path)
                with self.lock:
                    self.status = "ERROR"
                    self.error_message = "Unable to decode video. Please upload a valid .mp4, .avi, or .mov file."
                    self.is_running = False
                self._broadcast_update()
                return

            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1000
            self.fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

            (lx1_norm, ly1_norm), (lx2_norm, ly2_norm) = self.line_coords_norm
            line_start = (int(lx1_norm * frame_width), int(ly1_norm * frame_height))
            line_end = (int(lx2_norm * frame_width), int(ly2_norm * frame_height))

            if frame_width < 400 or frame_height < 300:
                self.video_quality_warning = True

            last_broadcast_time = time.time()
            last_db_save_time = time.time()
            interval_seconds = self.interval_minutes * 60

            # Persistent tracking state dictionaries
            active_tracks: Dict[int, TrackedPerson] = {}
            counted_in_ids = set()
            counted_out_ids = set()
            all_seen_ids = set()

            logger.info(
                "CCTV Video Processing started: %s (%dx%d, %d frames, line: %s to %s)",
                self.video_filename, frame_width, frame_height, self.total_frames, line_start, line_end
            )

            while not self.should_stop:
                ret, frame = cap.read()
                if not ret:
                    if self.mode == "rtsp_stream":
                        time.sleep(0.05)
                        continue
                    # Video completed processing all frames cleanly
                    logger.info("Finished processing all %d frames of video %s", frame_idx, self.video_filename)
                    break

                frame_idx += 1
                self.current_frame_idx = frame_idx

                # 1. ByteTrack Persistent Tracking on Frame (strictly Class 0 Person)
                track_results = self.detector.model.track(
                    frame,
                    classes=[0],
                    conf=self.detector.conf_threshold,
                    iou=self.detector.iou_threshold,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False
                )[0]

                current_frame_detections = 0
                frame_confidences = []

                if track_results.boxes is not None and track_results.boxes.id is not None:
                    boxes = track_results.boxes.xyxy.cpu().numpy().astype(int)
                    track_ids = track_results.boxes.id.int().cpu().numpy().tolist()
                    confs = track_results.boxes.conf.cpu().numpy().tolist()
                    current_frame_detections = len(track_ids)
                    frame_confidences.extend(confs)

                    for b, tid, c in zip(boxes, track_ids, confs):
                        all_seen_ids.add(tid)
                        cx = int((b[0] + b[2]) / 2)
                        cy = int((b[1] + b[3]) / 2)
                        centroid = (cx, cy)
                        bbox_tuple = (int(b[0]), int(b[1]), int(b[2]), int(b[3]))

                        if tid not in active_tracks:
                            track_obj = TrackedPerson(tid, bbox_tuple, centroid)
                            track_obj.last_seen_frame = frame_idx
                            track_obj.confidence = float(c)
                            if tid in counted_in_ids:
                                track_obj.counted_in = True
                            if tid in counted_out_ids:
                                track_obj.counted_out = True
                            active_tracks[tid] = track_obj
                        else:
                            active_tracks[tid].update(bbox_tuple, centroid, frame_idx, float(c))

                        # Evaluate Line Crossing for this track
                        t_obj = active_tracks[tid]
                        if len(t_obj.history) >= 2:
                            p_prev = t_obj.history[-2]
                            p_curr = t_obj.centroid

                            crossed, direction = check_line_crossing(
                                p_prev, p_curr, line_start, line_end, self.direction_mode
                            )

                            if crossed:
                                if direction == "IN" and tid not in counted_in_ids:
                                    counted_in_ids.add(tid)
                                    t_obj.counted_in = True
                                    self.incoming_count += 1
                                    logger.info("Person ID:%d crossed IN (Total IN: %d)", tid, self.incoming_count)
                                elif direction == "OUT" and tid not in counted_out_ids:
                                    counted_out_ids.add(tid)
                                    t_obj.counted_out = True
                                    self.outgoing_count += 1
                                    logger.info("Person ID:%d crossed OUT (Total OUT: %d)", tid, self.outgoing_count)

                # Prune tracks not seen in last 30 frames
                stale_ids = [tid for tid, tobj in active_tracks.items() if frame_idx - tobj.last_seen_frame > 30]
                for sid in stale_ids:
                    del active_tracks[sid]

                # 2. Update Live Metrics
                self.observed_count = current_frame_detections
                self.total_unique_tracked = len(all_seen_ids)
                self.net_flow = self.incoming_count - self.outgoing_count
                self.estimated_crowd = max(self.observed_count, max(0, self.net_flow))

                # Queue classification
                if self.estimated_crowd < 5:
                    self.queue_status = "LOW"
                elif self.estimated_crowd < 15:
                    self.queue_status = "MODERATE"
                elif self.estimated_crowd < 30:
                    self.queue_status = "HIGH"
                elif self.estimated_crowd < 50:
                    self.queue_status = "VERY HIGH"
                else:
                    self.queue_status = "CRITICAL"

                self.recent_net_history.append(self.net_flow)
                if len(self.recent_net_history) > 30:
                    self.recent_net_history.pop(0)

                if len(self.recent_net_history) >= 5:
                    delta = self.recent_net_history[-1] - self.recent_net_history[0]
                    if delta > 1:
                        self.trend = "INCREASING"
                    elif delta < -1:
                        self.trend = "DECREASING"
                    else:
                        self.trend = "STABLE"

                if frame_confidences:
                    self.confidence = sum(frame_confidences) / len(frame_confidences)
                else:
                    self.confidence = 0.90

                self.last_update_time = datetime.utcnow()

                # Render HUD frame with bounding boxes and track trails
                annotated_frame = self._render_hud_frame(
                    frame.copy(), list(active_tracks.values()), line_start, line_end, frame_width, frame_height
                )

                _, jpeg_buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                self.latest_jpeg_frame = jpeg_buffer.tobytes()

                now_t = time.time()
                if now_t - last_broadcast_time >= 1.0:
                    last_broadcast_time = now_t
                    self._broadcast_update()

                if now_t - last_db_save_time >= min(interval_seconds, 60):
                    last_db_save_time = now_t
                    if self.observed_count > 0 or self.incoming_count > 0 or self.outgoing_count > 0:
                        self._save_aggregated_record_to_db()

                # Cooperative sleep for non-blocking UI
                time.sleep(0.005)

        except Exception as e:
            logger.error("CCTV Video Worker error: %s", e)
            with self.lock:
                self.status = "ERROR"
                self.error_message = f"Processing failure: {str(e)}"
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            with self.lock:
                if self.status != "ERROR":
                    self.status = "STOPPED" if self.should_stop else "COMPLETED"
                self.is_running = False

            if self.status == "COMPLETED" and (self.observed_count > 0 or self.incoming_count > 0 or self.outgoing_count > 0):
                try:
                    self._save_aggregated_record_to_db()
                except Exception as err:
                    logger.warning("Could not persist final CCTV record: %s", err)
            self._broadcast_update()
            logger.info("CCTV Video Worker terminated. Final status: %s (Observed: %d, In: %d, Out: %d)",
                        self.status, self.observed_count, self.incoming_count, self.outgoing_count)

    # ─────────────────────────────────────────────────────────────────────────
    # Frame Annotation & Professional HUD Rendering
    # ─────────────────────────────────────────────────────────────────────────
    def _render_hud_frame(
        self,
        frame: np.ndarray,
        tracks: List[TrackedPerson],
        line_start: Tuple[int, int],
        line_end: Tuple[int, int],
        w: int,
        h: int
    ) -> np.ndarray:
        try:
            import cv2
        except ImportError:
            return frame

        # 1. Draw Virtual Counting Line with Glow Effect
        cv2.line(frame, line_start, line_end, (0, 165, 255), 4, cv2.LINE_AA)
        cv2.line(frame, line_start, line_end, (0, 235, 255), 2, cv2.LINE_AA)

        mid_x = int((line_start[0] + line_end[0]) / 2)
        mid_y = int((line_start[1] + line_end[1]) / 2)
        cv2.putText(frame, "COUNTING LINE", (mid_x + 10, mid_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 235, 255), 2)

        # 2. Draw Tracked People Bounding Boxes & Trails
        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            cx, cy = track.centroid

            box_color = (0, 255, 128) if (track.counted_in or track.counted_out) else (255, 191, 0)

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Person ID label
            label = f"ID:{track.track_id}"
            cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + 65, max(20, y1)), box_color, -1)
            cv2.putText(frame, label, (x1 + 4, max(14, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

            # Centroid point
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            # Motion Trail
            if len(track.history) > 1:
                pts = np.array(track.history, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, (255, 255, 0), 1, cv2.LINE_AA)

        # 3. Top HUD Banner (Dark Semi-Transparent Overlay)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 65), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Top Banner Text
        cv2.putText(frame, "OURS TTD - CCTV AI PEOPLE COUNTER", (14, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Source: {self.source_label} | Loc: {self.location_name}", (14, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 220, 240), 1, cv2.LINE_AA)

        # Top Right Live Counters
        counter_str = f"IN: {self.incoming_count} | OUT: {self.outgoing_count} | OBSERVED: {self.observed_count}"
        cv2.putText(frame, counter_str, (max(10, w - 360), 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (50, 255, 120), 2, cv2.LINE_AA)

        status_str = f"QUEUE: {self.queue_status} | TREND: {self.trend}"
        status_color = (0, 255, 0) if self.queue_status == "LOW" else ((0, 215, 255) if self.queue_status == "MODERATE" else (0, 0, 255))
        cv2.putText(frame, status_str, (max(10, w - 360), 48), cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 2, cv2.LINE_AA)

        if self.video_quality_warning:
            cv2.putText(frame, "Low video quality may reduce detection accuracy", (14, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 165, 255), 1, cv2.LINE_AA)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    # Database Persistence & WebSocket Broadcasting
    # ─────────────────────────────────────────────────────────────────────────
    def _save_aggregated_record_to_db(self):
        """Save aggregated counts to Supabase/PostgreSQL/SQLite."""
        if self.status == "ERROR":
            logger.info("Skipping DB save: Worker status is ERROR.")
            return

        if self.observed_count == 0 and self.incoming_count == 0 and self.outgoing_count == 0:
            logger.info("Skipping DB save: No people observed or counted (all counts zero).")
            return

        try:
            from backend.database import SessionLocal
            from backend.models import CCTVCrowdRecord, PilgrimFlowData

            now = datetime.utcnow()
            today_str = dt_date.today().strftime("%Y-%m-%d")
            h_start = (now.hour // 2) * 2
            start_str = f"{h_start:02d}:00"
            end_str = f"{(h_start + 2) % 24:02d}:00"

            db = SessionLocal()
            try:
                # 1. Insert granular CCTVCrowdRecord
                cctv_rec = CCTVCrowdRecord(
                    camera_id=self.camera_id,
                    location_id=self.location_id,
                    location_name=self.location_name,
                    timestamp=now,
                    interval_start=start_str,
                    interval_end=end_str,
                    incoming_count=0 if getattr(self, "is_image_mode", False) else self.incoming_count,
                    outgoing_count=0 if getattr(self, "is_image_mode", False) else self.outgoing_count,
                    observed_count=self.observed_count,
                    net_flow=0 if getattr(self, "is_image_mode", False) else self.net_flow,
                    queue_status=self.queue_status,
                    trend="STABLE" if getattr(self, "is_image_mode", False) else self.trend,
                    confidence=self.confidence,
                    source="cctv_image" if getattr(self, "is_image_mode", False) else self.source_db_code,
                    video_filename=self.video_filename
                )
                db.add(cctv_rec)

                # 2. Synchronize / Upsert PilgrimFlowData for consistent dashboard display
                existing_flow = (
                    db.query(PilgrimFlowData)
                    .filter(
                        PilgrimFlowData.date == today_str,
                        PilgrimFlowData.start_time == start_str,
                        PilgrimFlowData.end_time == end_str
                    )
                    .first()
                )

                if existing_flow:
                    if not getattr(self, "is_image_mode", False):
                        existing_flow.incoming_pilgrims = self.incoming_count
                        existing_flow.outgoing_pilgrims = self.outgoing_count
                        existing_flow.net_pilgrims = self.net_flow
                    existing_flow.estimated_crowd = self.estimated_crowd
                    existing_flow.queue_status = self.queue_status
                    existing_flow.source = "cctv_image" if getattr(self, "is_image_mode", False) else self.source_db_code
                else:
                    new_flow = PilgrimFlowData(
                        date=today_str,
                        start_time=start_str,
                        end_time=end_str,
                        incoming_pilgrims=0 if getattr(self, "is_image_mode", False) else self.incoming_count,
                        outgoing_pilgrims=0 if getattr(self, "is_image_mode", False) else self.outgoing_count,
                        net_pilgrims=0 if getattr(self, "is_image_mode", False) else self.net_flow,
                        estimated_crowd=self.estimated_crowd,
                        festival=False,
                        queue_status=self.queue_status,
                        queue_pressure=0.5 if self.queue_status == "MODERATE" else (0.8 if self.queue_status == "HIGH" else 0.3),
                        source="cctv_image" if getattr(self, "is_image_mode", False) else self.source_db_code,
                        created_by_admin=None
                    )
                    db.add(new_flow)

                db.commit()
                logger.info("Successfully saved CCTV crowd record to DB (Observed: %d, In: %d, Out: %d)",
                            self.observed_count, self.incoming_count, self.outgoing_count)
            except Exception as dbe:
                db.rollback()
                logger.warning("Failed to save CCTV record to database: %s", dbe)
            finally:
                db.close()
        except Exception as e:
            logger.debug("Could not connect to DB for CCTV save: %s", e)

    def _broadcast_update(self):
        """Emit real-time WebSocket update to all connected clients."""
        try:
            from backend.services.broadcast import broadcast_manager

            payload = {
                "type": "cctv_queue_update",
                "data": {
                    "source": self.source_label,
                    "source_code": self.source_db_code,
                    "status": self.status,
                    "location": self.location_name,
                    "is_image": getattr(self, "is_image_mode", False),
                    "observed_count": self.observed_count,
                    "incoming": None if getattr(self, "is_image_mode", False) else self.incoming_count,
                    "outgoing": None if getattr(self, "is_image_mode", False) else self.outgoing_count,
                    "incoming_display": "N/A (Still Image)" if getattr(self, "is_image_mode", False) else str(self.incoming_count),
                    "outgoing_display": "N/A (Still Image)" if getattr(self, "is_image_mode", False) else str(self.outgoing_count),
                    "net_flow": None if getattr(self, "is_image_mode", False) else self.net_flow,
                    "estimated_crowd": self.estimated_crowd,
                    "queue_status": self.queue_status,
                    "trend": "N/A" if getattr(self, "is_image_mode", False) else self.trend,
                    "confidence": round(self.confidence, 2),
                    "last_updated": datetime.utcnow().isoformat(),
                    "video_file": self.video_filename
                }
            }
            broadcast_manager.broadcast_sync(payload)
        except Exception as e:
            logger.debug("WebSocket broadcast error: %s", e)


# Global Singleton CCTV Vision Worker Instance
cctv_worker = CCTVVisionWorker()


def analyze_video_summary(
    video_path: str,
    max_frames: int = 300,
    conf_threshold: float = 0.20,
    iou_threshold: float = 0.45,
    direction_mode: str = "left_to_right"
) -> Dict[str, Any]:
    """
    Fast, authentic synchronous video crowd analysis using ByteTrack.
    Processes up to max_frames frames to measure actual peak observed crowd,
    line crossings (incoming/outgoing), net flow, and total unique tracked individuals.
    Never returns fake or hardcoded numbers.
    """
    import cv2
    v_path = Path(video_path)
    if not v_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(str(v_path))
    if not cap.isOpened():
        raise ValueError(f"Unable to open or decode video file: {v_path.name}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    # Virtual counting line
    if direction_mode in ("left_to_right", "right_to_left"):
        line_start = (int(0.5 * w), int(0.05 * h))
        line_end = (int(0.5 * w), int(0.95 * h))
    else:
        line_start = (int(0.05 * w), int(0.5 * h))
        line_end = (int(0.95 * w), int(0.5 * h))

    detector = YOLOPersonDetector(conf_threshold=conf_threshold, iou_threshold=iou_threshold)

    tracked_histories: Dict[int, List[Tuple[int, int]]] = {}
    counted_in_ids = set()
    counted_out_ids = set()
    all_seen_ids = set()
    peak_observed = 0
    all_confs: List[float] = []

    frame_idx = 0
    try:
        while frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            track_res = detector.model.track(
                frame,
                classes=[0],
                conf=conf_threshold,
                iou=iou_threshold,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False
            )[0]

            cur_count = 0
            if track_res.boxes is not None and track_res.boxes.id is not None:
                boxes = track_res.boxes.xyxy.cpu().numpy().astype(int)
                track_ids = track_res.boxes.id.int().cpu().numpy().tolist()
                confs = track_res.boxes.conf.cpu().numpy().tolist()
                cur_count = len(track_ids)
                all_confs.extend(confs)

                for b, tid in zip(boxes, track_ids):
                    all_seen_ids.add(tid)
                    cx = int((b[0] + b[2]) / 2)
                    cy = int((b[1] + b[3]) / 2)
                    if tid not in tracked_histories:
                        tracked_histories[tid] = []
                    hist = tracked_histories[tid]
                    hist.append((cx, cy))
                    if len(hist) > 30:
                        hist.pop(0)

                    if len(hist) >= 2:
                        crossed, direction = check_line_crossing(
                            hist[-2], hist[-1], line_start, line_end, direction_mode
                        )
                        if crossed:
                            if direction == "IN" and tid not in counted_in_ids:
                                counted_in_ids.add(tid)
                            elif direction == "OUT" and tid not in counted_out_ids:
                                counted_out_ids.add(tid)

            peak_observed = max(peak_observed, cur_count)
    finally:
        cap.release()

    net = len(counted_in_ids) - len(counted_out_ids)
    mean_conf = round(sum(all_confs) / len(all_confs), 2) if all_confs else 0.90

    return {
        "total_frames_processed": frame_idx,
        "total_video_frames": total_frames,
        "peak_observed": peak_observed,
        "incoming": len(counted_in_ids),
        "outgoing": len(counted_out_ids),
        "net_flow": net,
        "total_unique": len(all_seen_ids),
        "confidence": mean_conf,
    }


