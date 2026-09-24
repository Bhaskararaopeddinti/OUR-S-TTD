"""
OURS TTD – AI Queue Intelligence Service
Provides predictive queue analysis including best times, crowd trends, and AI-generated advice.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import calendar

# Historical patterns based on time of day, day of week, and season
TIME_PATTERNS = {
    # Early morning (2:30 AM - 6:00 AM) - Generally less crowded
    (2, 6): {"crowd_level": "Low", "wait_factor": 0.7, "recommendation": "Excellent time for darshan"},
    # Morning peak (6:00 AM - 10:00 AM) - High crowd
    (6, 10): {"crowd_level": "High", "wait_factor": 1.3, "recommendation": "Expect long queues"},
    # Mid-morning (10:00 AM - 12:00 PM) - Moderate crowd
    (10, 12): {"crowd_level": "Moderate", "wait_factor": 1.0, "recommendation": "Moderate wait times"},
    # Post-lunch (12:00 PM - 3:00 PM) - Lower crowd
    (12, 15): {"crowd_level": "Low", "wait_factor": 0.8, "recommendation": "Good time, shorter queues"},
    # Afternoon (3:00 PM - 6:00 PM) - Moderate to High
    (15, 18): {"crowd_level": "Moderate", "wait_factor": 1.1, "recommendation": "Moderate wait expected"},
    # Evening (6:00 PM - 9:00 PM) - High crowd
    (18, 21): {"crowd_level": "High", "wait_factor": 1.25, "recommendation": "Peak evening hours"},
    # Night (9:00 PM - 2:30 AM) - Low crowd
    (21, 2): {"crowd_level": "Low", "wait_factor": 0.75, "recommendation": "Night darshan available"},
}

DAY_PATTERNS = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 
    4: "Friday", 5: "Saturday", 6: "Sunday"
}

# Festival seasons with higher crowd
FESTIVAL_SEASONS = {
    "Brahmotsavam": {"months": [9, 10], "crowd_multiplier": 2.5, "description": "Annual 9-day festival"},
    "Vaikunta Ekadasi": {"months": [1], "crowd_multiplier": 2.0, "description": "Sacred festival day"},
    "Rathasapthami": {"months": [2], "crowd_multiplier": 1.8, "description": "Chariot festival"},
    "New Year": {"months": [1], "days": [1], "crowd_multiplier": 2.2, "description": "New Year crowd"},
    "Weekend": {"days": [5, 6], "crowd_multiplier": 1.4, "description": "Weekend rush"},
}


def get_current_time_info() -> Dict:
    """Get current time information for prediction."""
    now = datetime.now()
    return {
        "hour": now.hour,
        "day_of_week": now.weekday(),
        "day_of_month": now.day,
        "month": now.month,
        "is_weekend": now.weekday() >= 5,
        "current_time": now.strftime("%H:%M"),
    }


def get_time_pattern(hour: int) -> Dict:
    """Get crowd pattern for a specific hour."""
    for (start, end), pattern in TIME_PATTERNS.items():
        if start <= hour < end or (start > end and (hour >= start or hour < end)):
            return pattern
    return {"crowd_level": "Moderate", "wait_factor": 1.0, "recommendation": "Normal crowd expected"}


def check_festival_impact(time_info: Dict) -> List[Dict]:
    """Check if current time falls during festival seasons."""
    impacts = []
    month = time_info["month"]
    day_of_week = time_info["day_of_week"]
    day_of_month = time_info["day_of_month"]
    
    for festival, info in FESTIVAL_SEASONS.items():
        if month in info.get("months", []):
            if "days" in info:
                if day_of_month in info["days"]:
                    impacts.append({
                        "festival": festival,
                        "multiplier": info["crowd_multiplier"],
                        "description": info["description"]
                    })
            else:
                impacts.append({
                    "festival": festival,
                    "multiplier": info["crowd_multiplier"],
                    "description": info["description"]
                })
        elif "days" in info and day_of_week in info["days"]:
            impacts.append({
                "festival": festival,
                "multiplier": info["crowd_multiplier"],
                "description": info["description"]
            })
    
    return impacts


def _format_slot_time(start_str: str, end_str: str) -> str:
    """Format '18:00' and '20:00' into '6:00 PM – 8:00 PM'."""
    def _to_12h(t_str: str) -> str:
        try:
            parts = t_str.strip().split(":")
            h = int(parts[0]) % 24
            m = int(parts[1]) if len(parts) > 1 else 0
            suffix = "AM" if h < 12 else "PM"
            h_12 = h % 12
            if h_12 == 0:
                h_12 = 12
            return f"{h_12}:{m:02d} {suffix}" if m != 0 else f"{h_12}:00 {suffix}"
        except Exception:
            return t_str

    return f"{_to_12h(start_str)} – {_to_12h(end_str)}"


def _get_status_level_and_emoji(crowd: int, festival: bool = False) -> tuple[str, str, str]:
    """Return (status_level, status_with_emoji, badge_class)."""
    adjusted = crowd * (1.2 if festival else 1.0)
    if adjusted < 2000:
        return "Low", "🟢 LOW", "low"
    elif adjusted < 5000:
        return "Moderate", "🟡 MODERATE", "moderate"
    elif adjusted < 9000:
        return "High", "🔴 HIGH", "high"
    else:
        return "Very High", "🟣 VERY HIGH", "very-high"


def predict_queue_status(current_wait_minutes: int = None, current_density: str = "Moderate", db=None) -> dict:
    """
    Enhanced AI-powered queue prediction with time, day, and admin pilgrim flow data.
    Returns comprehensive predictive intelligence matching exact OURS TTD specifications.
    """
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = day_of_week >= 5
    month = now.month

    admin_crowd_data = None
    all_today_slots = []
    has_reliable_data = False
    data_source_label = "AI Estimated Data"
    data_source_code = "ai_prediction"

    # 0. Check Live CCTV Vision Worker first
    try:
        from backend.services.cctv_vision import cctv_worker
        cctv_live = cctv_worker.get_status()
        incoming_v = cctv_live.get("incoming") or 0
        outgoing_v = cctv_live.get("outgoing") or 0
        observed_v = cctv_live.get("observed_count") or 0
        is_active = cctv_live.get("is_running") or cctv_live.get("status") in ("COMPLETED", "PROCESSING")
        if is_active and (observed_v > 0 or incoming_v > 0 or outgoing_v > 0):
            has_reliable_data = True
            data_source_label = cctv_live.get("source", "Demo CCTV AI Data")
            data_source_code = cctv_live.get("source_db", "demo_cctv_ai")
            admin_crowd_data = {
                "estimated_crowd": cctv_live.get("estimated_crowd", observed_v),
                "observed_count": observed_v,
                "queue_status": cctv_live.get("queue_status", "LOW"),
                "incoming_pilgrims": incoming_v,
                "outgoing_pilgrims": outgoing_v,
                "net_pilgrims": cctv_live.get("net_flow") or (incoming_v - outgoing_v),
                "trend": cctv_live.get("trend") or "STABLE",
                "festival": False,
                "slot": f"{(hour//2)*2:02d}:00 – {(hour//2)*2+2:02d}:00",
                "source": data_source_code,
                "source_label": data_source_label,
            }
    except Exception as cctv_e:
        import logging
        logging.getLogger(__name__).debug("Could not read live CCTV worker: %s", cctv_e)

    # 1. If not running, check Database (CCTV records or PilgrimFlowData)
    if not admin_crowd_data and db:
        try:
            from datetime import date as dt_date
            from backend.models import PilgrimFlowData, CCTVCrowdRecord
            from sqlalchemy import desc

            today_str = dt_date.today().strftime("%Y-%m-%d")

            # Check for latest CCTV records
            latest_cctv = (
                db.query(CCTVCrowdRecord)
                .order_by(desc(CCTVCrowdRecord.timestamp))
                .first()
            )

            # Query all slots for today
            all_today_slots = (
                db.query(PilgrimFlowData)
                .filter(PilgrimFlowData.date == today_str)
                .order_by(PilgrimFlowData.start_time)
                .all()
            )

            if not all_today_slots:
                latest_entry = db.query(PilgrimFlowData).order_by(desc(PilgrimFlowData.date), desc(PilgrimFlowData.start_time)).first()
                if latest_entry:
                    all_today_slots = (
                        db.query(PilgrimFlowData)
                        .filter(PilgrimFlowData.date == latest_entry.date)
                        .order_by(PilgrimFlowData.start_time)
                        .all()
                    )

            def _to_naive(dt):
                if dt is None:
                    return None
                return dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt

            cctv_ts = _to_naive(latest_cctv.timestamp) if latest_cctv else None
            slot_ts = _to_naive(all_today_slots[-1].created_at) if all_today_slots else None

            if latest_cctv and (not all_today_slots or (cctv_ts and slot_ts and cctv_ts >= slot_ts)):
                has_reliable_data = True
                if latest_cctv.source == "authorized_cctv":
                    data_source_label = "Authorized CCTV Stream"
                elif latest_cctv.source in ("demo_cctv_video", "demo_cctv_ai"):
                    data_source_label = "Demo CCTV AI Data"
                elif latest_cctv.source in ("cctv_image", "admin_image"):
                    data_source_label = "Admin Crowd Photo Analysis"
                else:
                    data_source_label = "CCTV AI Data"

                data_source_code = latest_cctv.source
                crowd_val = latest_cctv.observed_count if latest_cctv.observed_count > 0 else max(0, latest_cctv.net_flow)
                admin_crowd_data = {
                    "estimated_crowd": crowd_val,
                    "observed_count": latest_cctv.observed_count,
                    "queue_status": latest_cctv.queue_status,
                    "incoming_pilgrims": latest_cctv.incoming_count,
                    "outgoing_pilgrims": latest_cctv.outgoing_count,
                    "net_pilgrims": latest_cctv.net_flow,
                    "trend": latest_cctv.trend,
                    "festival": False,
                    "slot": f"{latest_cctv.interval_start} – {latest_cctv.interval_end}" if latest_cctv.interval_start else "Live",
                    "source": data_source_code,
                    "source_label": data_source_label,
                }
            elif all_today_slots:
                has_reliable_data = True
                latest_flow = all_today_slots[-1]
                src = getattr(latest_flow, "source", "manual") or "manual"
                data_source_code = src
                if src == "authorized_cctv":
                    data_source_label = "Authorized CCTV Stream"
                elif src in ("demo_cctv_video", "demo_cctv_ai"):
                    data_source_label = "Demo CCTV AI Data"
                elif src in ("cctv_image", "admin_image"):
                    data_source_label = "Admin Crowd Photo Analysis"
                else:
                    data_source_label = "Live Admin Data"

                admin_crowd_data = {
                    "estimated_crowd": latest_flow.estimated_crowd,
                    "observed_count": latest_flow.incoming_pilgrims,
                    "queue_status": latest_flow.queue_status,
                    "incoming_pilgrims": latest_flow.incoming_pilgrims,
                    "outgoing_pilgrims": latest_flow.outgoing_pilgrims,
                    "net_pilgrims": latest_flow.net_pilgrims,
                    "festival": bool(latest_flow.festival),
                    "slot": _format_slot_time(latest_flow.start_time, latest_flow.end_time),
                    "raw_start": latest_flow.start_time,
                    "raw_end": latest_flow.end_time,
                    "date": latest_flow.date,
                    "source": data_source_code,
                    "source_label": data_source_label,
                    "total_slots_recorded": len(all_today_slots)
                }
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug("Could not fetch queue database data: %s", e)

    # 1. CURRENT QUEUE STATUS CALCULATION
    current_crowd = 0
    incoming_count = 0
    outgoing_count = 0
    raw_status = "Data unavailable"
    is_festival = False
    current_time_period = _format_slot_time(f"{(hour//2)*2:02d}:00", f"{(hour//2)*2+2:02d}:00")

    if admin_crowd_data:
        current_crowd = admin_crowd_data["estimated_crowd"]
        incoming_count = admin_crowd_data["incoming_pilgrims"]
        outgoing_count = admin_crowd_data["outgoing_pilgrims"]
        raw_status = admin_crowd_data.get("queue_status") or "MODERATE"
        is_festival = admin_crowd_data.get("festival", False)
        current_time_period = admin_crowd_data.get("slot") or current_time_period
    else:
        current_crowd = 0
        incoming_count = 0
        outgoing_count = 0
        raw_status = "Data unavailable"
        has_reliable_data = False

    # Status level, emoji, and waiting condition
    if not has_reliable_data:
        status_level, status_badge, badge_class = "Unavailable", "Data unavailable", "no-data"
        waiting_condition = "Data unavailable"
        predicted_wait = None
        crowd_trend_label = "STABLE"
    else:
        # Deterministic queue classification based on observed/estimated crowd
        if current_crowd < 15:
            status_level = "Low"
            status_badge = "🟢 LOW"
            badge_class = "low"
            waiting_condition = "Minimal (30–45 mins)"
            predicted_wait = 45
        elif current_crowd < 35:
            status_level = "Moderate"
            status_badge = "🟡 MODERATE"
            badge_class = "moderate"
            waiting_condition = "Moderate (1.5–2 hrs)"
            predicted_wait = 120
        elif current_crowd < 65:
            status_level = "High"
            status_badge = "🔴 HIGH"
            badge_class = "high"
            waiting_condition = "Long (3–4 hrs)"
            predicted_wait = 210
        elif current_crowd < 100:
            status_level = "Very High"
            status_badge = "🟣 VERY HIGH"
            badge_class = "very-high"
            waiting_condition = "Heavy Rush (5–7 hrs)"
            predicted_wait = 360
        else:
            status_level = "Critical"
            status_badge = "🟣 CRITICAL"
            badge_class = "critical"
            waiting_condition = "Peak Rush (8+ hrs)"
            predicted_wait = 480

        # Override from verified admin entry if specified
        if admin_crowd_data and admin_crowd_data.get("queue_status"):
            norm_qs = str(admin_crowd_data["queue_status"]).upper().replace("🟢", "").replace("🟡", "").replace("🔴", "").replace("🟣", "").strip()
            if norm_qs in ("LOW", "MODERATE", "HIGH", "VERY HIGH", "CRITICAL"):
                status_level = norm_qs.title()
                emoji_map = {"LOW": "🟢 LOW", "MODERATE": "🟡 MODERATE", "HIGH": "🔴 HIGH", "VERY HIGH": "🟣 VERY HIGH", "CRITICAL": "🟣 CRITICAL"}
                status_badge = emoji_map.get(norm_qs, f"🟡 {norm_qs}")

        # Trend calculation based on flow difference
        net_diff = (incoming_count or 0) - (outgoing_count or 0)
        if net_diff > 1:
            crowd_trend_label = "Increasing"
        elif net_diff < -1:
            crowd_trend_label = "Decreasing"
        else:
            crowd_trend_label = "Stable"

    # 2. PREDICTED QUEUE CONDITION (Clearly distinguished from Current Queue Status)
    if not has_reliable_data:
        predicted_condition = "Prediction unavailable – more data required."
        predicted_crowd_level = "Data unavailable"
    else:
        if crowd_trend_label == "Increasing":
            if status_level == "Low":
                predicted_crowd_level = "MODERATE"
            elif status_level == "Moderate":
                predicted_crowd_level = "HIGH"
            else:
                predicted_crowd_level = "VERY HIGH"
            predicted_condition = f"Queue is expected to increase to {predicted_crowd_level} due to positive devotee inflow (+{net_diff})."
        elif crowd_trend_label == "Decreasing":
            if status_level in ("Very High", "Critical"):
                predicted_crowd_level = "HIGH"
            elif status_level == "High":
                predicted_crowd_level = "MODERATE"
            else:
                predicted_crowd_level = "LOW"
            predicted_condition = f"Queue is easing towards {predicted_crowd_level} as departure rate exceeds arrivals ({net_diff})."
        else:
            predicted_crowd_level = status_level.upper()
            predicted_condition = f"Queue is expected to remain {predicted_crowd_level} with steady inflow/outflow balance."

    # 3. BEST TIME TO JOIN QUEUE ANALYSIS
    if has_reliable_data and all_today_slots and len(all_today_slots) >= 2:
        best_slot = min(all_today_slots, key=lambda s: s.estimated_crowd)
        best_time_data = {
            "has_data": True,
            "time_window": _format_slot_time(best_slot.start_time, best_slot.end_time),
            "recommendation": f"Based on recent available data, a lower crowd period was observed around {_format_slot_time(best_slot.start_time, best_slot.end_time)}.",
            "reasons": [
                "Lowest recorded crowd period today",
                "Manageable queue compartment clearance rate",
                "Based on recorded pilgrim flow data"
            ]
        }
    elif has_reliable_data:
        # Off-peak hours based on verified temple schedule patterns
        best_time_data = {
            "has_data": True,
            "time_window": "12:00 PM – 3:00 PM or 9:00 PM – 11:30 PM",
            "recommendation": "Based on recent available data, lower crowd periods typically occur post-lunch (12:00–3:00 PM) or late evening.",
            "reasons": [
                "Off-peak compartment clearance window",
                "Verified TTD daily schedule patterns"
            ]
        }
    else:
        best_time_data = {
            "has_data": False,
            "time_window": None,
            "recommendation": "Not enough historical data to recommend a reliable time.",
            "message": "Not enough historical data to recommend a reliable time."
        }

    # 4. PRECAUTIONS TAILORED TO CURRENT QUEUE
    precautions = [
        "Carry original Aadhaar/Government ID card and Darshan tokens for physical verification.",
        "Keep hydrated using free RO water dispensing points inside queue compartments.",
        "Traditional modest dress code is strictly mandatory (Dhoti/Kurta for men, Saree/Churidar with Dupatta for women).",
        "Deposit mobile phones, smart watches, and electronic luggage at authorized counters before entering.",
        "Special queues and battery vehicle assistance are available for senior citizens and differently-abled pilgrims."
    ]
    if status_level in ("High", "Very High", "Critical"):
        precautions.insert(0, "High crowd alert: Keep children close, carry dry snacks, and follow VQC compartment instructions.")

    # 5. CROWD TREND — NEXT 6 HOURS
    crowd_trend_6h = []
    if has_reliable_data:
        current_sim_crowd = current_crowd
        base_hour = hour
        for i in range(1, 4):
            slot_start_h = (base_hour + (i - 1) * 2) % 24
            slot_end_h = (slot_start_h + 2) % 24
            slot_label = _format_slot_time(f"{slot_start_h:02d}:00", f"{slot_end_h:02d}:00")

            if 2 <= slot_start_h < 6:
                rate_factor = -0.15
            elif 6 <= slot_start_h < 12:
                rate_factor = 0.20
            elif 12 <= slot_start_h < 16:
                rate_factor = -0.05
            elif 16 <= slot_start_h < 21:
                rate_factor = 0.18
            else:
                rate_factor = -0.25

            if is_festival:
                rate_factor += 0.12

            projected_crowd = max(5, int(current_sim_crowd * (1 + rate_factor)))
            current_sim_crowd = projected_crowd

            s_level, s_badge, s_class = _get_status_level_and_emoji(projected_crowd, is_festival)
            proj_wait = max(20, int(projected_crowd * 3))

            crowd_trend_6h.append({
                "time": slot_label,
                "expected_crowd": projected_crowd,
                "status": s_badge,
                "status_level": s_level,
                "predicted_wait_minutes": proj_wait
            })

    # 6. AI PREDICTION SUMMARY
    if not has_reliable_data:
        ai_prediction = {
            "expected_crowd": "Data unavailable",
            "status_badge": "Data unavailable",
            "points": [
                "Prediction unavailable – more data required.",
                "Live CCTV AI or admin flow records have not yet been recorded for this period.",
                "Please verify physical display boards at Vaikuntam Queue Complex."
            ]
        }
    else:
        ai_prediction = {
            "expected_crowd": predicted_crowd_level,
            "status_badge": status_badge,
            "points": [
                predicted_condition,
                f"Current observed queue status is {status_level.upper()} with ~{predicted_wait} min estimated wait.",
                "Action: Enter queue now." if status_level in ("Low", "Moderate") else "Action: Consider waiting for an off-peak slot if possible."
            ]
        }

    return {
        # Current Queue Status
        "current_crowd_level": status_level,
        "queue_status": status_level.upper(),
        "queue_status_badge": status_badge,
        "waiting_condition": waiting_condition,
        "incoming_devotees": incoming_count if has_reliable_data else None,
        "outgoing_devotees": outgoing_count if has_reliable_data else None,
        "current_time_period": current_time_period if has_reliable_data else "Current",
        "crowd_trend": crowd_trend_label,
        "estimated_crowd": current_crowd if has_reliable_data else None,
        "observed_count": admin_crowd_data.get("observed_count") if admin_crowd_data else None,
        "predicted_wait_minutes": predicted_wait,

        # Distinction: Predicted Queue Condition
        "predicted_queue_condition": predicted_condition,
        "predicted_crowd_level": predicted_crowd_level if has_reliable_data else "Unavailable",

        # Best Time & Precautions
        "best_time_to_join": best_time_data,
        "precautions": precautions,

        # Trend & Summary
        "crowd_trend_next_6_hours": crowd_trend_6h,
        "ai_prediction_summary": ai_prediction,
        "ai_advice": precautions,

        # Source Tracking
        "admin_data_used": has_reliable_data,
        "admin_crowd_data": admin_crowd_data,
        "data_source": data_source_label,
        "data_source_code": data_source_code,
        "prediction_timestamp": now.isoformat()
    }



def predict(current_wait: int, current_density: str) -> int:
    """
    Legacy function for backward compatibility.
    Returns simple predicted wait time based on density factor.
    """
    factor = {"Low": .85, "Moderate": 1, "High": 1.18, "Very High": 1.38}.get(current_density, 1)
    return max(10, round(current_wait * factor))
