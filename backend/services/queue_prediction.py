"""
OURS TTD – AI Queue Intelligence Service
Provides predictive queue analysis including best times, crowd trends, and AI-generated advice.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import calendar
import random

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
        if cctv_live.get("is_running") or (cctv_live.get("incoming", 0) > 0 or cctv_live.get("outgoing", 0) > 0):
            has_reliable_data = True
            data_source_label = cctv_live.get("source", "Demo CCTV AI Data")
            data_source_code = cctv_live.get("source_db", "demo_cctv_ai")
            admin_crowd_data = {
                "estimated_crowd": cctv_live["estimated_crowd"],
                "observed_count": cctv_live["observed_count"],
                "queue_status": cctv_live["queue_status"],
                "incoming_pilgrims": cctv_live["incoming"],
                "outgoing_pilgrims": cctv_live["outgoing"],
                "net_pilgrims": cctv_live["net_flow"],
                "trend": cctv_live["trend"],
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

            if latest_cctv and (not all_today_slots or latest_cctv.timestamp > all_today_slots[-1].created_at):
                has_reliable_data = True
                data_source_label = "Demo CCTV AI Data" if latest_cctv.source == "demo_cctv_ai" else "CCTV AI Data"
                data_source_code = latest_cctv.source
                admin_crowd_data = {
                    "estimated_crowd": max(0, 1200 + latest_cctv.net_flow),
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
                data_source_label = "Demo CCTV AI Data" if src == "demo_cctv_ai" else ("Live Admin Data" if src == "manual" else "CCTV AI Data")
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
    raw_status = "MODERATE"
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
        current_crowd = 3200
        incoming_count = 1200
        outgoing_count = 950


    # Status level, emoji, and waiting condition
    status_level, status_badge, badge_class = _get_status_level_and_emoji(current_crowd, is_festival)
    if admin_crowd_data and admin_crowd_data.get("queue_status"):
        norm_qs = admin_crowd_data["queue_status"].upper()
        if norm_qs in ("LOW", "🟢 LOW"):
            status_level, status_badge, badge_class = "Low", "🟢 LOW", "low"
        elif norm_qs in ("MODERATE", "🟡 MODERATE"):
            status_level, status_badge, badge_class = "Moderate", "🟡 MODERATE", "moderate"
        elif norm_qs in ("HIGH", "🔴 HIGH"):
            status_level, status_badge, badge_class = "High", "🔴 HIGH", "high"
        elif norm_qs in ("VERY HIGH", "CRITICAL", "🟣 VERY HIGH"):
            status_level, status_badge, badge_class = "Very High", "🟣 VERY HIGH", "very-high"

    # Waiting condition string
    if status_level == "Low":
        waiting_condition = "Minimal (under 1 hr)"
        predicted_wait = max(15, int(current_crowd / 100))
    elif status_level == "Moderate":
        waiting_condition = "Moderate (2–3 hrs)"
        predicted_wait = max(60, int(current_crowd / 60))
    elif status_level == "High":
        waiting_condition = "Long (4–6 hrs)"
        predicted_wait = max(180, int(current_crowd / 40))
    else:
        waiting_condition = "Very Long (8+ hrs)"
        predicted_wait = max(360, int(current_crowd / 30))

    # Trend string
    net_diff = incoming_count - outgoing_count
    if net_diff > 250:
        crowd_trend_label = "Increasing"
    elif net_diff < -200:
        crowd_trend_label = "Decreasing"
    else:
        crowd_trend_label = "Stable"

    # 2. CROWD TREND — NEXT 6 HOURS (3 consecutive 2-hour slots)
    crowd_trend_6h = []
    current_sim_crowd = current_crowd
    base_hour = hour

    for i in range(1, 4):
        slot_start_h = (base_hour + (i - 1) * 2) % 24
        slot_end_h = (slot_start_h + 2) % 24
        slot_label = _format_slot_time(f"{slot_start_h:02d}:00", f"{slot_end_h:02d}:00")

        # Time of day factors
        if 2 <= slot_start_h < 6:
            rate_factor = -0.15  # Early morning clearing
        elif 6 <= slot_start_h < 12:
            rate_factor = 0.20   # Morning rush
        elif 12 <= slot_start_h < 16:
            rate_factor = -0.05  # Afternoon lull
        elif 16 <= slot_start_h < 21:
            rate_factor = 0.18   # Evening peak
        else:
            rate_factor = -0.25  # Night clearing

        if is_festival:
            rate_factor += 0.12

        projected_crowd = max(400, int(current_sim_crowd * (1 + rate_factor)))
        current_sim_crowd = projected_crowd

        s_level, s_badge, s_class = _get_status_level_and_emoji(projected_crowd, is_festival)
        proj_wait = max(15, int(projected_crowd / 45))

        crowd_trend_6h.append({
            "time": slot_label,
            "expected_crowd": projected_crowd,
            "status": s_badge,
            "status_level": s_level,
            "predicted_wait_minutes": proj_wait
        })

    # 3. BEST TIME TO JOIN QUEUE ANALYSIS
    best_time_data = None
    if has_reliable_data and all_today_slots:
        # Find the slot with minimum estimated crowd / maximum net outflow
        best_slot = min(all_today_slots, key=lambda s: s.estimated_crowd)
        best_time_data = {
            "has_data": True,
            "time_window": _format_slot_time(best_slot.start_time, best_slot.end_time),
            "reasons": [
                "Lower expected crowd",
                "More outgoing devotees",
                "Better incoming/outgoing balance"
            ]
        }
    elif crowd_trend_6h:
        # Pick lowest slot from 6h projection
        lowest_proj = min(crowd_trend_6h, key=lambda x: x["expected_crowd"])
        best_time_data = {
            "has_data": True,
            "time_window": lowest_proj["time"],
            "reasons": [
                "Lower expected crowd",
                "More outgoing devotees",
                "Better incoming/outgoing balance"
            ]
        }
    else:
        best_time_data = {
            "has_data": False,
            "time_window": None,
            "message": "Not enough data to determine the best time."
        }

    # 4. AI-GENERATED QUEUE ADVICE
    ai_advice = [
        "Avoid the queue during peak crowd periods.",
        "Consider joining during the lower-crowd time slot.",
        "Keep water and essential items with you.",
        "Follow TTD queue instructions.",
        "Check the latest queue status before joining."
    ]

    # 5. AI PREDICTION
    next_trend_str = "increase" if crowd_trend_label == "Increasing" else "remain stable" if crowd_trend_label == "Stable" else "decrease"
    ai_prediction = {
        "expected_crowd": status_level.upper(),
        "status_badge": status_badge,
        "points": [
            f"Crowd is expected to {next_trend_str} during the next time slot.",
            "Queue waiting time may increase." if crowd_trend_label == "Increasing" else "Queue waiting time expected to remain manageable.",
            "Recommended action: Consider joining during the next low-crowd period." if status_level in ("High", "Very High") else "Recommended action: Good window to enter queue."
        ]
    }

    # 6. FESTIVAL IMPACT
    if is_festival:
        festival_impact = {
            "is_active": True,
            "title": "Festival: YES",
            "points": [
                "Expected crowd impact: High",
                "Queue demand: Increased",
                "Recommendation: Plan Darshan earlier."
            ]
        }
    else:
        festival_impact = {
            "is_active": False,
            "title": "Festival Impact: Normal",
            "points": [
                "Standard devotee inflow rate",
                "Normal compartment clearance cycles"
            ]
        }

    return {
        # Master Prompt Section 5: Current Queue Status
        "current_crowd_level": status_level,
        "queue_status": status_level.upper(),
        "queue_status_badge": status_badge,
        "waiting_condition": waiting_condition,
        "incoming_devotees": incoming_count,
        "outgoing_devotees": outgoing_count,
        "current_time_period": current_time_period,
        "crowd_trend": crowd_trend_label,
        "estimated_crowd": current_crowd,
        "predicted_wait_minutes": predicted_wait,

        # Master Prompt Section 6: Next 6 Hours Crowd Trend
        "crowd_trend_next_6_hours": crowd_trend_6h,

        # Master Prompt Section 7: Best Time to Join
        "best_time_to_join": best_time_data,

        # Master Prompt Section 8: AI-Generated Advice
        "ai_advice": ai_advice,

        # Master Prompt Section 9: AI Prediction
        "ai_prediction_summary": ai_prediction,

        # Master Prompt Section 10: Festival Impact
        "festival_impact_summary": festival_impact,

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
    Returns simple predicted wait time.
    """
    variance = random.randint(-8, 12)
    factor = {"Low": .85, "Moderate": 1, "High": 1.18, "Very High": 1.38}.get(current_density, 1)
    return max(10, round(current_wait * factor + variance))
