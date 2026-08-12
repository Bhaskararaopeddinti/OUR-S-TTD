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


def predict_queue_status(current_wait_minutes: int = None, current_density: str = "Moderate", db=None) -> dict:
    """
    Enhanced AI-powered queue prediction with time, day, and festival awareness.
    Returns comprehensive predictive intelligence.
    Now includes admin-entered pilgrim flow data for better accuracy.
    """
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = day_of_week >= 5
    month = now.month
    
    # Try to get admin-entered pilgrim flow data first
    admin_crowd_data = None
    if db:
        try:
            from datetime import date as dt_date
            from backend.models import PilgrimFlowData
            from sqlalchemy import desc
            
            today = dt_date.today().strftime("%Y-%m-%d")
            latest_flow = (
                db.query(PilgrimFlowData)
                .filter(PilgrimFlowData.date == today)
                .order_by(desc(PilgrimFlowData.start_time))
                .first()
            )
            if latest_flow:
                admin_crowd_data = {
                    "estimated_crowd": latest_flow.estimated_crowd,
                    "queue_status": latest_flow.queue_status,
                    "incoming_pilgrims": latest_flow.incoming_pilgrims,
                    "outgoing_pilgrims": latest_flow.outgoing_pilgrims,
                    "net_pilgrims": latest_flow.net_pilgrims,
                    "festival": latest_flow.festival,
                    "slot": f"{latest_flow.start_time}–{latest_flow.end_time}"
                }
                # Override with admin data if available
                current_density = latest_flow.queue_status
                if latest_flow.estimated_crowd > 0:
                    # Estimate wait time based on crowd size (rough approximation: 1000 people ≈ 15 mins)
                    current_wait_minutes = max(15, int(latest_flow.estimated_crowd / 1000 * 15))
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug("Could not fetch admin queue data: %s", e)
    
    # Handle None values for wait time
    if current_wait_minutes is None:
        current_wait_minutes = 120  # Default to 2 hours if not available
    
    # Base crowd multiplier based on time of day
    time_multipliers = {
        0: 0.4,   # 12 AM - 1 AM (very low)
        1: 0.3,   # 1 AM - 2 AM (very low)
        2: 0.5,   # 2 AM - 3 AM (low - temple opening time)
        3: 0.6,   # 3 AM - 4 AM (low)
        4: 0.7,   # 4 AM - 5 AM (moderate)
        5: 0.9,   # 5 AM - 6 AM (moderate)
        6: 1.2,   # 6 AM - 7 AM (high)
        7: 1.4,   # 7 AM - 8 AM (high)
        8: 1.6,   # 8 AM - 9 AM (very high)
        9: 1.5,   # 9 AM - 10 AM (high)
        10: 1.4,  # 10 AM - 11 AM (high)
        11: 1.3,  # 11 AM - 12 PM (moderate-high)
        12: 1.2,  # 12 PM - 1 PM (moderate)
        13: 1.1,  # 1 PM - 2 PM (moderate)
        14: 1.0,  # 2 PM - 3 PM (moderate)
        15: 1.1,  # 3 PM - 4 PM (moderate)
        16: 1.3,  # 4 PM - 5 PM (high)
        17: 1.5,  # 5 PM - 6 PM (very high)
        18: 1.6,  # 6 PM - 7 PM (very high)
        19: 1.4,  # 7 PM - 8 PM (high)
        20: 1.2,  # 8 PM - 9 PM (moderate)
        21: 1.0,  # 9 PM - 10 PM (moderate)
        22: 0.8,  # 10 PM - 11 PM (low-moderate)
        23: 0.6,  # 11 PM - 12 AM (low)
    }
    
    time_multiplier = time_multipliers.get(hour, 1.0)
    
    # Day of week multiplier
    day_multiplier = 1.3 if is_weekend else 1.0
    
    # Festival multiplier based on month
    festival_multipliers = {
        1: 1.5,   # January - Vaikunta Ekadasi, New Year
        2: 1.3,   # February - Rathasapthami
        9: 1.8,   # September - Brahmotsavam
        10: 1.8,  # October - Brahmotsavam
    }
    festival_multiplier = festival_multipliers.get(month, 1.0)
    
    # Overall crowd multiplier
    crowd_multiplier = time_multiplier * day_multiplier * festival_multiplier
    
    # Density-based adjustment
    density_multipliers = {
        "Low": 0.7,
        "Moderate": 1.0,
        "High": 1.5,
        "Very High": 2.0
    }
    density_multiplier = density_multipliers.get(current_density, 1.0)
    
    # Predicted wait time
    predicted_wait = max(15, int(current_wait_minutes * crowd_multiplier * density_multiplier))
    
    # Determine crowd level
    if crowd_multiplier < 0.8:
        current_crowd_level = "Low"
    elif crowd_multiplier < 1.2:
        current_crowd_level = "Moderate"
    elif crowd_multiplier < 1.6:
        current_crowd_level = "High"
    else:
        current_crowd_level = "Very High"
    
    # Generate crowd trend for next 6 hours
    crowd_trend = []
    for i in range(1, 7):
        future_hour = (hour + i) % 24
        future_multiplier = time_multipliers.get(future_hour, 1.0) * day_multiplier * festival_multiplier
        future_density = density_multipliers.get(current_density, 1.0)
        future_wait = max(15, int(current_wait_minutes * future_multiplier * future_density))
        
        if future_multiplier < 0.8:
            future_crowd = "Low"
        elif future_multiplier < 1.2:
            future_crowd = "Moderate"
        elif future_multiplier < 1.6:
            future_crowd = "High"
        else:
            future_crowd = "Very High"
        
        crowd_trend.append({
            "time": f"{future_hour}:00",
            "crowd_level": future_crowd,
            "wait_factor": round(future_multiplier, 2),
            "predicted_wait_minutes": future_wait
        })
    
    # Find best times to join queue in next 24 hours
    best_times = []
    for h in range(24):
        future_hour = (hour + h) % 24
        future_multiplier = time_multipliers.get(future_hour, 1.0) * day_multiplier * festival_multiplier
        
        if future_multiplier < 0.9:  # Low crowd threshold
            recommendation = "Excellent time to join"
        elif future_multiplier < 1.1:
            recommendation = "Good time to join"
        else:
            continue  # Skip high crowd times
        
        best_times.append({
            "time": f"{future_hour}:00",
            "recommendation": recommendation,
            "wait_factor": round(future_multiplier, 2)
        })
    
    # Sort by wait factor and take top 5
    best_times.sort(key=lambda x: x["wait_factor"])
    best_times = best_times[:5]
    
    # Generate AI advice based on current conditions
    ai_advice = []
    
    if current_crowd_level == "Low":
        ai_advice.append("Excellent time to join the queue! Wait times are minimal.")
    elif current_crowd_level == "Moderate":
        ai_advice.append("Good time to join. Expect reasonable wait times.")
    elif current_crowd_level == "High":
        ai_advice.append("Crowd is high. Consider joining in 2-3 hours or early morning.")
    else:  # Very High
        ai_advice.append("Crowd is very high. Best to join after 10 PM or before 5 AM.")
    
    if is_weekend:
        ai_advice.append("Weekend crowd expected. Plan for longer wait times.")
    
    if festival_multiplier > 1.0:
        ai_advice.append(f"Festival season active. Crowd multiplier: ×{festival_multiplier}")
    
    if hour >= 6 and hour <= 10:
        ai_advice.append("Morning peak hours. Consider joining after 11 AM.")
    elif hour >= 16 and hour <= 19:
        ai_advice.append("Evening peak hours. Consider joining after 9 PM.")
    
    # Festival impacts
    festival_impacts = []
    if month in [9, 10]:
        festival_impacts.append({
            "festival": "Brahmotsavam",
            "description": "Annual Brahmotsavam festival - expect maximum crowds",
            "multiplier": festival_multiplier
        })
    elif month == 1:
        festival_impacts.append({
            "festival": "Vaikunta Ekadasi",
            "description": "Vaikunta Ekadasi - special darshan with high attendance",
            "multiplier": festival_multiplier
        })
    elif month == 2:
        festival_impacts.append({
            "festival": "Rathasapthami",
            "description": "Rathasapthami festival - chariot procession on Mada Streets",
            "multiplier": festival_multiplier
        })
    
    # Low crowd recommendation
    if best_times:
        low_crowd_recommendation = f"Best time to join: {best_times[0]['time']} ({best_times[0]['recommendation']})"
    else:
        low_crowd_recommendation = "No optimal low-crowd times in the next 24 hours. Consider early morning (2-5 AM)."
    
    return {
        "predicted_wait_minutes": predicted_wait,
        "current_crowd_level": current_crowd_level,
        "crowd_trend_next_6_hours": crowd_trend,
        "best_times_to_join": best_times,
        "ai_advice": ai_advice,
        "festival_impacts": festival_impacts,
        "low_crowd_recommendation": low_crowd_recommendation,
        "prediction_timestamp": now.isoformat(),
        "admin_data_used": admin_crowd_data is not None,
        "admin_crowd_data": admin_crowd_data,
        "data_source": "Admin-entered data" if admin_crowd_data else "AI Historical Prediction"
    }


def predict(current_wait: int, current_density: str) -> int:
    """
    Legacy function for backward compatibility.
    Returns simple predicted wait time.
    """
    variance = random.randint(-8, 12)
    factor = {"Low": .85, "Moderate": 1, "High": 1.18, "Very High": 1.38}.get(current_density, 1)
    return max(10, round(current_wait * factor + variance))
