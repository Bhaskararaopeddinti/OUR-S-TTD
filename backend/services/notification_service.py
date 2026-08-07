"""
OURS TTD – Smart Notification Service
Provides intelligent notifications for queue changes, festivals, weather, and temple announcements.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Notification categories and their priorities
NOTIFICATION_CATEGORIES = {
    "queue": {"priority": "high", "icon": "⏳", "title_prefix": "Queue Update"},
    "festival": {"priority": "high", "icon": "🎉", "title_prefix": "Festival Alert"},
    "weather": {"priority": "medium", "icon": "🌤️", "title_prefix": "Weather Alert"},
    "temple": {"priority": "high", "icon": "🛕", "title_prefix": "Temple Notice"},
    "emergency": {"priority": "critical", "icon": "🚨", "title_prefix": "Emergency"},
    "booking": {"priority": "medium", "icon": "📋", "title_prefix": "Booking Reminder"},
    "health": {"priority": "medium", "icon": "💚", "title_prefix": "Health Reminder"},
    "laddu": {"priority": "low", "icon": "🍬", "title_prefix": "Laddu Collection"},
    "mobile": {"priority": "medium", "icon": "📵", "title_prefix": "Phone Deposit"},
    "general": {"priority": "low", "icon": "📢", "title_prefix": "Information"}
}

# Demo notification templates
QUEUE_NOTIFICATIONS = [
    "Queue is now shorter! Current wait time reduced to approximately {wait_minutes} minutes.",
    "Good time to join the queue! Crowd level is {crowd_level} at the moment.",
    "Queue moving faster than expected. Consider joining now for shorter wait times.",
    "Peak crowd expected in the next hour. Join now or wait until {best_time}."
]

FESTIVAL_NOTIFICATIONS = {
    "Brahmotsavam": [
        "🎉 Brahmotsavam festival begins! Expect heavy crowds. Plan accordingly.",
        "🎉 Brahmotsavam procession today. Special darshan arrangements in place.",
        "🎉 Brahmotsavam final day - Garuda Seva. Expect maximum crowds."
    ],
    "Vaikunta Ekadasi": [
        "🎉 Vaikunta Ekadasi tomorrow - Special darshan throughout the day.",
        "🎉 Vaikunta Ekadasi today - Paramapatha Vaasal opening at scheduled time."
    ],
    "Rathasapthami": [
        "🎉 Rathasapthami festival - Chariot procession on Mada Streets.",
        "🎉 Rathasapthami special arrangements - Check for route changes."
    ]
}

WEATHER_NOTIFICATIONS = [
    "🌤️ Weather update: {temp}°C expected. Pleasant conditions for darshan.",
    "⛈️ Rain expected in the next 2 hours. Carry umbrella or raincoat.",
    "☀️ Hot weather expected ({temp}°C). Stay hydrated and use sunscreen.",
    "🌧️ Light rain continuing. Indoor waiting areas available at VQC."
]

TEMPLE_NOTIFICATIONS = [
    "🛕 Temple opening time: 2:30 AM. Plan your darshan accordingly.",
    "🛕 Temple will be closed for {duration} hours for special rituals.",
    "🛕 Special seva being performed today. Normal darshan may have delays.",
    "🛕 Free laddu distribution counter timings: 6 AM - 10 PM.",
    "🛕 Hair offering (Kalyanakatta) open from 4 AM to 10 PM today."
]

EMERGENCY_NOTIFICATIONS = [
    "🚨 Emergency: Medical assistance needed at {location}. Volunteers requested.",
    "🚨 Weather emergency: Heavy rain alert. Seek shelter in designated areas.",
    "🚨 Crowd management: Avoid {area} due to overcrowding. Use alternate routes.",
    "🚨 Security alert: Report suspicious activity to nearest help desk."
]

BOOKING_NOTIFICATIONS = [
    "📋 Reminder: Your {booking_type} booking is scheduled for {date} at {time}.",
    "📋 Booking available: {booking_type} slots open for {date}. Book now!",
    "📋 Booking reminder: Collect your darshan tokens 2 hours before scheduled time.",
    "📋 Accommodation available: PAC-{number} has rooms for immediate occupancy."
]

HEALTH_NOTIFICATIONS = [
    "💧 Hydration reminder: Drink water now to stay healthy during darshan.",
    "💊 Medication reminder: Time to take your prescribed medication.",
    "😴 Rest reminder: Take a short break. Rest areas available nearby.",
    "🍛 Meal reminder: Annaprasadam available at MTVAC and VQC compartments."
]

LADDU_NOTIFICATIONS = [
    "🍬 Laddu collection reminder: Collect your free laddu after darshan.",
    "🍬 Additional laddus available for purchase at Main Laddu Complex.",
    "🍬 Laddu counter closing soon: Collect before {time}.",
    "🍬 Special laddu distribution today for {festival} devotees."
]

MOBILE_NOTIFICATIONS = [
    "📵 Phone deposit reminder: Deposit mobile phones before entering temple.",
    "📵 Collect your deposited phone from counter {number} before leaving.",
    "📵 Phone deposit centres open: VQC I, VQC II, PAC-3, PAC-5.",
    "📵 Remember your deposit token! Required for phone collection."
]


def get_current_context() -> Dict:
    """Get current context for intelligent notification generation."""
    now = datetime.now()
    hour = now.hour
    
    return {
        "current_time": now.strftime("%H:%M"),
        "current_hour": hour,
        "day_of_week": now.weekday(),
        "is_weekend": now.weekday() >= 5,
        "month": now.month,
        "is_festival_season": now.month in [1, 2, 9, 10],  # Major festival months
    }


def generate_queue_notification(queue_status: Dict) -> Optional[Dict]:
    """Generate intelligent queue notification based on current status."""
    context = get_current_context()
    
    # Determine if queue is shorter than usual
    wait_minutes = queue_status.get("predicted_wait_minutes", 120)
    crowd_level = queue_status.get("current_crowd_level", "Moderate")
    
    # Only notify if conditions are favorable
    if crowd_level in ["Low", "Moderate"] and wait_minutes < 90:
        template = random.choice(QUEUE_NOTIFICATIONS)
        message = template.format(
            wait_minutes=wait_minutes,
            crowd_level=crowd_level.lower(),
            best_time="2:30 AM" if context["current_hour"] >= 18 else "12:00 PM"
        )
        
        return {
            "category": "queue",
            "title": "Queue Update",
            "body": message,
            "priority": "high",
            "icon": "⏳",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_festival_notification() -> Optional[Dict]:
    """Generate festival notification based on current date."""
    context = get_current_context()
    month = context["month"]
    
    festival_notifications = []
    
    if month in [9, 10]:  # Brahmotsavam season
        festival_notifications.extend(FESTIVAL_NOTIFICATIONS["Brahmotsavam"])
    elif month == 1:  # Vaikunta Ekadasi and New Year
        festival_notifications.extend(FESTIVAL_NOTIFICATIONS["Vaikunta Ekadasi"])
        if context["day_of_month"] == 1:
            festival_notifications.append("🎉 New Year crowd expected. Plan for longer wait times.")
    elif month == 2:  # Rathasapthami
        festival_notifications.extend(FESTIVAL_NOTIFICATIONS["Rathasapthami"])
    
    if festival_notifications and random.random() < 0.3:  # 30% chance during festival season
        return {
            "category": "festival",
            "title": "Festival Alert",
            "body": random.choice(festival_notifications),
            "priority": "high",
            "icon": "🎉",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_weather_notification(weather_data: Dict = None) -> Optional[Dict]:
    """Generate weather notification based on conditions."""
    if not weather_data:
        # Generate demo weather data
        weather_data = {
            "temp": random.randint(18, 32),
            "condition": random.choice(["sunny", "cloudy", "rainy", "partly_cloudy"])
        }
    
    temp = weather_data.get("temp", 25)
    condition = weather_data.get("condition", "sunny")
    
    # Only notify for significant weather
    if condition == "rainy" or temp > 30 or temp < 20:
        if condition == "rainy":
            template = WEATHER_NOTIFICATIONS[1]  # Rain alert
        elif temp > 30:
            template = WEATHER_NOTIFICATIONS[2]  # Hot weather
        else:
            template = WEATHER_NOTIFICATIONS[3]  # Light rain/cold
        
        return {
            "category": "weather",
            "title": "Weather Alert",
            "body": template.format(temp=temp),
            "priority": "medium",
            "icon": "🌤️",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_temple_notification() -> Optional[Dict]:
    """Generate temple announcement notification."""
    context = get_current_context()
    hour = context["current_hour"]
    
    # Time-based temple notifications
    if hour == 2:  # Temple opening time
        return {
            "category": "temple",
            "title": "Temple Notice",
            "body": TEMPLE_NOTIFICATIONS[0],
            "priority": "high",
            "icon": "🛕",
            "timestamp": datetime.now().isoformat()
        }
    elif hour == 22:  # Evening reminder
        return {
            "category": "temple",
            "title": "Temple Notice",
            "body": TEMPLE_NOTIFICATIONS[3],
            "priority": "medium",
            "icon": "🛕",
            "timestamp": datetime.now().isoformat()
        }
    
    # Random temple notifications (10% chance)
    if random.random() < 0.1:
        return {
            "category": "temple",
            "title": "Temple Notice",
            "body": random.choice(TEMPLE_NOTIFICATIONS),
            "priority": "medium",
            "icon": "🛕",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_booking_notification(booking_data: Dict = None) -> Optional[Dict]:
    """Generate booking-related notification."""
    if booking_data:
        # Specific booking reminder
        return {
            "category": "booking",
            "title": "Booking Reminder",
            "body": BOOKING_NOTIFICATIONS[0].format(**booking_data),
            "priority": "medium",
            "icon": "📋",
            "timestamp": datetime.now().isoformat()
        }
    
    # General booking availability (5% chance)
    if random.random() < 0.05:
        return {
            "category": "booking",
            "title": "Booking Available",
            "body": random.choice(BOOKING_NOTIFICATIONS[1:]),
            "priority": "medium",
            "icon": "📋",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_health_notification(reminder_type: str = None) -> Optional[Dict]:
    """Generate health reminder notification."""
    if reminder_type:
        # Specific health reminder
        if reminder_type == "hydration":
            template = HEALTH_NOTIFICATIONS[0]
        elif reminder_type == "medication":
            template = HEALTH_NOTIFICATIONS[1]
        elif reminder_type == "rest":
            template = HEALTH_NOTIFICATIONS[2]
        elif reminder_type == "food":
            template = HEALTH_NOTIFICATIONS[3]
        else:
            template = random.choice(HEALTH_NOTIFICATIONS)
        
        return {
            "category": "health",
            "title": "Health Reminder",
            "body": template,
            "priority": "medium",
            "icon": "💚",
            "timestamp": datetime.now().isoformat()
        }
    
    # Random health reminder (3% chance)
    if random.random() < 0.03:
        return {
            "category": "health",
            "title": "Health Reminder",
            "body": random.choice(HEALTH_NOTIFICATIONS),
            "priority": "medium",
            "icon": "💚",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_laddu_notification() -> Optional[Dict]:
    """Generate laddu collection notification."""
    context = get_current_context()
    hour = context["current_hour"]
    
    # Laddu counter closing reminder
    if hour == 21:  # 9 PM
        return {
            "category": "laddu",
            "title": "Laddu Collection",
            "body": LADDU_NOTIFICATIONS[2].format(time="10 PM"),
            "priority": "low",
            "icon": "🍬",
            "timestamp": datetime.now().isoformat()
        }
    
    # Random laddu notification (5% chance)
    if random.random() < 0.05:
        return {
            "category": "laddu",
            "title": "Laddu Collection",
            "body": random.choice(LADDU_NOTIFICATIONS[:2]),
            "priority": "low",
            "icon": "🍬",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_mobile_notification() -> Optional[Dict]:
    """Generate mobile deposit reminder notification."""
    context = get_current_context()
    hour = context["current_hour"]
    
    # Morning reminder for phone deposit
    if hour in [5, 6, 7]:
        return {
            "category": "mobile",
            "title": "Phone Deposit Reminder",
            "body": MOBILE_NOTIFICATIONS[0],
            "priority": "medium",
            "icon": "📵",
            "timestamp": datetime.now().isoformat()
        }
    
    # Evening reminder for phone collection
    if hour in [20, 21, 22]:
        return {
            "category": "mobile",
            "title": "Phone Collection Reminder",
            "body": MOBILE_NOTIFICATIONS[1].format(number=random.randint(1, 5)),
            "priority": "medium",
            "icon": "📵",
            "timestamp": datetime.now().isoformat()
        }
    
    return None


def generate_smart_notifications(queue_status: Dict = None, 
                                 weather_data: Dict = None,
                                 booking_data: Dict = None,
                                 health_reminder: str = None) -> List[Dict]:
    """
    Generate all relevant smart notifications based on current context.
    Returns a list of notification dictionaries.
    """
    notifications = []
    
    # Queue notification
    if queue_status:
        queue_notif = generate_queue_notification(queue_status)
        if queue_notif:
            notifications.append(queue_notif)
    
    # Festival notification
    festival_notif = generate_festival_notification()
    if festival_notif:
        notifications.append(festival_notif)
    
    # Weather notification
    weather_notif = generate_weather_notification(weather_data)
    if weather_notif:
        notifications.append(weather_notif)
    
    # Temple notification
    temple_notif = generate_temple_notification()
    if temple_notif:
        notifications.append(temple_notif)
    
    # Booking notification
    booking_notif = generate_booking_notification(booking_data)
    if booking_notif:
        notifications.append(booking_notif)
    
    # Health notification
    health_notif = generate_health_notification(health_reminder)
    if health_notif:
        notifications.append(health_notif)
    
    # Laddu notification
    laddu_notif = generate_laddu_notification()
    if laddu_notif:
        notifications.append(laddu_notif)
    
    # Mobile notification
    mobile_notif = generate_mobile_notification()
    if mobile_notif:
        notifications.append(mobile_notif)
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    notifications.sort(key=lambda x: priority_order.get(x["priority"], 4))
    
    return notifications


def get_notification_summary(notifications: List[Dict]) -> Dict:
    """Get a summary of notifications by category."""
    summary = {}
    for notif in notifications:
        category = notif["category"]
        if category not in summary:
            summary[category] = {
                "count": 0,
                "highest_priority": "low",
                "latest": None
            }
        summary[category]["count"] += 1
        
        priority_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        if priority_order.get(notif["priority"], 0) > priority_order.get(summary[category]["highest_priority"], 0):
            summary[category]["highest_priority"] = notif["priority"]
        
        if not summary[category]["latest"] or notif["timestamp"] > summary[category]["latest"]:
            summary[category]["latest"] = notif["timestamp"]
    
    return summary
