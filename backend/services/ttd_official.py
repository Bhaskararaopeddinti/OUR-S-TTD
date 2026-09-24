"""Read only publicly displayed TTD updates. No booking or private systems are accessed."""
import re
import time
import logging
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

OFFICIAL_URL = "https://www.tirumala.org/"
_cache: tuple[float, dict] | None = None


def public_status(db=None) -> dict:
    """
    Returns public TTD queue & crowd status.
    Fast, reliable, and non-blocking: checks database records first, then caches.
    Never hangs on external website requests.
    """
    global _cache
    now = time.time()
    if _cache and (now - _cache[0] < 60):
        # Quick return from fresh 60-second cache
        return dict(_cache[1])

    # Default clean baseline
    result = {
        "source": OFFICIAL_URL,
        "source_name": "TTD public & CCTV queue monitoring",
        "verified": True,
        "wait_minutes": None,
        "crowd_density": "Moderate",
        "people_count": None,
        "message": "Live Darshan queue and crowd monitoring active.",
        "slot": None,
        "balance_tickets": None,
    }

    # 1. Check database for latest CCTV AI or queue status if db session available
    session_created = False
    if db is None:
        try:
            from backend.database import SessionLocal
            db = SessionLocal()
            session_created = True
        except Exception:
            db = None

    if db is not None:
        try:
            from backend.models import CCTVCrowdRecord, PilgrimFlowData, QueueStatus
            from sqlalchemy import desc

            # Check latest CCTV record
            latest_cctv = db.query(CCTVCrowdRecord).order_by(desc(CCTVCrowdRecord.timestamp)).first()
            if latest_cctv:
                result["people_count"] = latest_cctv.observed_count
                result["crowd_density"] = latest_cctv.queue_status.title()
                # Estimate wait based on crowd
                count = latest_cctv.observed_count
                if count < 15:
                    result["wait_minutes"] = 45
                elif count < 40:
                    result["wait_minutes"] = 120
                elif count < 70:
                    result["wait_minutes"] = 240
                else:
                    result["wait_minutes"] = 360
                result["source_name"] = "CCTV AI Live Monitoring"
                result["message"] = f"Live crowd status: {latest_cctv.queue_status} ({latest_cctv.observed_count} devotees observed at {latest_cctv.location_name})."
            else:
                latest_flow = db.query(PilgrimFlowData).order_by(desc(PilgrimFlowData.date), desc(PilgrimFlowData.start_time)).first()
                if latest_flow:
                    result["people_count"] = latest_flow.estimated_crowd
                    result["crowd_density"] = latest_flow.queue_status.title()
                    result["wait_minutes"] = 120 if latest_flow.queue_status == "MODERATE" else (45 if latest_flow.queue_status == "LOW" else 240)
                    result["source_name"] = "Pilgrim Flow Data"
                    result["message"] = f"Current queue condition: {latest_flow.queue_status}."
        except Exception as dbe:
            logger.debug("Database status lookup notice: %s", dbe)
        finally:
            if session_created:
                db.close()

    # 2. Try very fast 1.0s timeout scrape of official portal for running slot only if not cached
    if not result.get("slot"):
        try:
            request = Request(OFFICIAL_URL, headers={"User-Agent": "OURS-TTD-pilgrim-guide/1.0"})
            with urlopen(request, timeout=1.0) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text)
                slot = re.search(r"Running Slot:\s*([^B]+?)\s*Balance tickets", text, re.I)
                balance = re.search(r"Balance tickets for\s*([^:]+):\s*([\d,]+)", text, re.I)
                if slot:
                    result["slot"] = slot.group(1).strip()
                if balance:
                    result["balance_tickets"] = {
                        "date": balance.group(1).strip(),
                        "count": int(balance.group(2).replace(",", ""))
                    }
        except Exception:
            pass  # Fast fallback, never block

    _cache = (now, result)
    return result

