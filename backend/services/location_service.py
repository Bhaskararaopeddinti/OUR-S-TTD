"""
OURS TTD – Smart Route & Facility Assistant Service
Provides crowd-aware routing, walking time estimates, and facility recommendations.
"""
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Average walking speed: 4.5 km/h for normal conditions, adjusted for crowd
NORMAL_WALKING_SPEED_KMH = 4.5
CROWDED_WALKING_SPEED_KMH = 2.5

# Crowd density multipliers for different areas
AREA_CROWD_FACTORS = {
    "temple": 1.8,      # High crowd near temple
    "queue": 2.0,       # Very high crowd in queue areas
    "food": 1.4,        # Moderate crowd at food areas
    "laddu": 1.6,       # High crowd at laddu counters
    "transport": 1.3,   # Moderate crowd at transport
    "accommodation": 1.2, # Low-moderate crowd at accommodation
    "medical": 1.1,     # Low crowd at medical
    "footpath": 1.5,    # Moderate crowd on footpaths
    "default": 1.0      # Normal crowd
}


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula (in meters)."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def estimate_walking_time(distance_m: float, category: str = "default", 
                         current_hour: int = None) -> Dict:
    """
    Estimate walking time considering distance, crowd, and time of day.
    Returns time in minutes and crowd-adjusted speed.
    """
    # Get current hour if not provided
    if current_hour is None:
        current_hour = datetime.now().hour
    
    # Determine crowd factor based on area category and time
    base_crowd_factor = AREA_CROWD_FACTORS.get(category, AREA_CROWD_FACTORS["default"])
    
    # Time-based crowd adjustment
    time_crowd_factor = 1.0
    if 6 <= current_hour < 10:  # Morning peak
        time_crowd_factor = 1.3
    elif 18 <= current_hour < 21:  # Evening peak
        time_crowd_factor = 1.25
    elif 12 <= current_hour < 15:  # Post-lunch (less crowded)
        time_crowd_factor = 0.8
    
    total_crowd_factor = base_crowd_factor * time_crowd_factor
    
    # Adjust walking speed based on crowd
    if total_crowd_factor > 1.5:
        walking_speed = CROWDED_WALKING_SPEED_KMH
    else:
        walking_speed = NORMAL_WALKING_SPEED_KMH / total_crowd_factor
    
    # Calculate time in minutes
    distance_km = distance_m / 1000
    time_hours = distance_km / walking_speed
    time_minutes = int(time_hours * 60)
    
    return {
        "walking_time_minutes": time_minutes,
        "walking_time_formatted": format_walking_time(time_minutes),
        "crowd_factor": round(total_crowd_factor, 2),
        "crowd_level": get_crowd_level(total_crowd_factor),
        "recommended_pace": get_pace_recommendation(total_crowd_factor)
    }


def format_walking_time(minutes: int) -> str:
    """Format walking time for display."""
    if minutes < 60:
        return f"{minutes} min"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"


def get_crowd_level(factor: float) -> str:
    """Get crowd level description from factor."""
    if factor < 1.2:
        return "Low"
    elif factor < 1.5:
        return "Moderate"
    elif factor < 1.8:
        return "High"
    else:
        return "Very High"


def get_pace_recommendation(factor: float) -> str:
    """Get walking pace recommendation based on crowd."""
    if factor < 1.2:
        return "Normal walking pace"
    elif factor < 1.5:
        return "Moderate pace, expect some delays"
    elif factor < 1.8:
        return "Slow pace, allow extra time"
    else:
        return "Very slow, plan for significant delays"


def find_nearby_facilities(user_lat: float, user_lon: float, facilities: List[Dict], 
                          max_distance: Optional[float] = None, 
                          current_hour: int = None) -> List[Dict]:
    """
    Find nearby facilities sorted by distance with walking time estimates.
    Includes crowd-aware routing recommendations.
    """
    nearby = []
    
    if current_hour is None:
        current_hour = datetime.now().hour
    
    for facility in facilities:
        if "latitude" not in facility or "longitude" not in facility:
            continue
            
        distance = calculate_distance(
            user_lat, user_lon,
            facility["latitude"], facility["longitude"]
        )
        
        if max_distance is not None and distance > max_distance:
            continue
        
        # Get category for crowd estimation
        category = facility.get("kind", "default")
        
        # Estimate walking time
        walking_info = estimate_walking_time(distance, category, current_hour)
        
        facility_with_info = facility.copy()
        facility_with_info["distance_m"] = round(distance)
        facility_with_info["walking_time"] = walking_info
        
        nearby.append(facility_with_info)
    
    # Sort by walking time (more practical than pure distance)
    nearby.sort(key=lambda x: x["walking_time"]["walking_time_minutes"])
    
    return nearby


def find_optimal_route(start_lat: float, start_lon: float, 
                      destinations: List[Dict], 
                      current_hour: int = None) -> Dict:
    """
    Find optimal route visiting multiple destinations.
    Returns route order, total time, and step-by-step directions.
    """
    if not destinations:
        return {"error": "No destinations provided"}
    
    if current_hour is None:
        current_hour = datetime.now().hour
    
    # Simple nearest-neighbor algorithm for route optimization
    unvisited = destinations.copy()
    route = []
    current_lat, current_lon = start_lat, start_lon
    total_distance = 0
    total_time = 0
    
    while unvisited:
        # Find nearest unvisited destination
        nearest = None
        nearest_dist = float('inf')
        
        for dest in unvisited:
            dist = calculate_distance(current_lat, current_lon, 
                                     dest["latitude"], dest["longitude"])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = dest
        
        if nearest:
            # Calculate walking time to this destination
            category = nearest.get("kind", "default")
            walking_info = estimate_walking_time(nearest_dist, category, current_hour)
            
            route_step = {
                "destination": nearest,
                "distance_m": round(nearest_dist),
                "walking_time": walking_info,
                "from_location": {"lat": current_lat, "lon": current_lon}
            }
            
            route.append(route_step)
            total_distance += nearest_dist
            total_time += walking_info["walking_time_minutes"]
            
            # Update current position
            current_lat = nearest["latitude"]
            current_lon = nearest["longitude"]
            unvisited.remove(nearest)
    
    return {
        "route": route,
        "total_distance_m": round(total_distance),
        "total_time_minutes": total_time,
        "total_time_formatted": format_walking_time(total_time),
        "number_of_stops": len(route),
        "route_optimization": "Nearest-neighbor algorithm (efficient for practical use)"
    }


def find_least_crowded_path(user_lat: float, user_lon: float, 
                            target_facilities: List[Dict],
                            current_hour: int = None) -> Dict:
    """
    Find the least crowded path to target facilities.
    Compares multiple route options based on crowd factors.
    """
    if current_hour is None:
        current_hour = datetime.now().hour
    
    route_options = []
    
    for facility in target_facilities:
        if "latitude" not in facility or "longitude" not in facility:
            continue
        
        distance = calculate_distance(user_lat, user_lon, 
                                     facility["latitude"], facility["longitude"])
        category = facility.get("kind", "default")
        
        walking_info = estimate_walking_time(distance, category, current_hour)
        
        route_options.append({
            "facility": facility,
            "distance_m": round(distance),
            "walking_time": walking_info,
            "crowd_score": walking_info["crowd_factor"]
        })
    
    # Sort by crowd score (lower is better)
    route_options.sort(key=lambda x: x["crowd_score"])
    
    # Get the best option
    best_option = route_options[0] if route_options else None
    
    return {
        "recommended_path": best_option,
        "all_options": route_options,
        "recommendation_reason": f"Least crowded option with {best_option['walking_time']['crowd_level']} crowd level" if best_option else "No valid routes found"
    }


def format_distance(distance_m: int) -> str:
    """Format distance for display."""
    if distance_m < 1000:
        return f"{distance_m} m"
    else:
        km = distance_m / 1000
        return f"{km:.1f} km"


def get_facility_directions(user_lat: float, user_lon: float, 
                            facility: Dict) -> Dict:
    """
    Get detailed directions to a facility including:
    - Distance and walking time
    - Crowd-aware recommendations
    - Nearby landmarks
    - Alternative routes if crowded
    """
    distance = calculate_distance(user_lat, user_lon, 
                                  facility["latitude"], facility["longitude"])
    category = facility.get("kind", "default")
    
    current_hour = datetime.now().hour
    walking_info = estimate_walking_time(distance, category, current_hour)
    
    # Generate crowd-aware advice
    advice = []
    crowd_level = walking_info["crowd_level"]
    
    if crowd_level == "Very High":
        advice.append("⚠️ Very high crowd expected. Consider visiting during off-peak hours (2:30-6 AM or 12-3 PM).")
        advice.append("🚶 Allow extra time and follow volunteer directions.")
    elif crowd_level == "High":
        advice.append("⚠️ High crowd expected. Moderate pace recommended.")
    else:
        advice.append("✅ Normal crowd conditions. Good time to visit.")
    
    # Add facility-specific advice
    if category == "food":
        advice.append("🍛 Free Annaprasadam available. Peak meal times: 8-10 AM, 12-2 PM, 7-9 PM.")
    elif category == "laddu":
        advice.append("🍬 One free laddu per darshan token. Additional laddus available for purchase.")
    elif category == "phone":
        advice.append("📵 Mobile phones prohibited in temple. Deposit here and retain receipt token.")
    elif category == "medical":
        advice.append("🏥 24/7 medical facility available. Emergency: Call 155257.")
    
    return {
        "facility": facility,
        "distance_m": round(distance),
        "distance_formatted": format_distance(round(distance)),
        "walking_time": walking_info,
        "crowd_level": crowd_level,
        "advice": advice,
        "coordinates": {
            "destination": {"lat": facility["latitude"], "lon": facility["longitude"]},
            "current": {"lat": user_lat, "lon": user_lon}
        }
    }
