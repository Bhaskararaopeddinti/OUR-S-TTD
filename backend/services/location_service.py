import math
from typing import List, Dict, Optional

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

def find_nearby_facilities(user_lat: float, user_lon: float, facilities: List[Dict], max_distance: Optional[float] = None) -> List[Dict]:
    """Find nearby facilities sorted by distance."""
    nearby = []
    
    for facility in facilities:
        if "latitude" not in facility or "longitude" not in facility:
            continue
            
        distance = calculate_distance(
            user_lat, user_lon,
            facility["latitude"], facility["longitude"]
        )
        
        facility_with_distance = facility.copy()
        facility_with_distance["distance_m"] = round(distance)
        
        if max_distance is None or distance <= max_distance:
            nearby.append(facility_with_distance)
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance_m"])
    
    return nearby

def format_distance(distance_m: int) -> str:
    """Format distance for display."""
    if distance_m < 1000:
        return f"{distance_m} m"
    else:
        km = distance_m / 1000
        return f"{km:.1f} km"
