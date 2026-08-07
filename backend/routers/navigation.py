"""
OURS TTD — Navigation Locations Router
REST API for Smart Navigation module with Leaflet.js and OpenStreetMap.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

from backend.database import get_db
from backend.models import NavigationLocation
from backend.schemas import NavigationLocationIn, NavigationLocationUpdate
from backend.auth import current_claims
from math import radians, sin, cos, sqrt, atan2

router = APIRouter(prefix="/api/locations", tags=["Navigation Locations"])
navigation_router = APIRouter(prefix="/api/navigation", tags=["Navigation"])

WALKING_SPEED_M_PER_S = 1.3  # average walking speed in meters per second


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters using Haversine formula."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def format_distance(distance_m: float) -> str:
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f} km"
    return f"{int(distance_m)} m"


def format_duration(seconds: float) -> str:
    minutes = int(round(seconds / 60))
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    remaining = minutes % 60
    return f"{hours} h {remaining} min"


def infer_crowd_level(category: str) -> str:
    mapping = {
        "temple": "High",
        "queue": "Very High",
        "food": "Medium",
        "laddu": "High",
        "phone_deposit": "Low",
        "restroom": "Moderate",
        "water": "Low",
        "medical": "Low",
        "transport": "Moderate",
        "parking": "Low",
        "accommodation": "Moderate",
        "footpath": "High",
        "tonsure": "Medium",
        "police": "Low",
        "information": "Low",
        "lost_found": "Low",
        "cloak_room": "Low"
    }
    return mapping.get(category, "Moderate")


def make_location_payload(loc: NavigationLocation, origin: dict | None = None) -> dict:
    payload = {
        "id": loc.id,
        "name": loc.name,
        "category": loc.category,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "address": loc.address,
        "description": loc.description,
        "opening_hours": loc.opening_hours,
        "contact_number": loc.contact_number,
        "wheelchair_accessible": loc.wheelchair_accessible,
        "source": loc.source,
        "status": "Open",
        "crowd_level": infer_crowd_level(loc.category),
        "last_verified": loc.last_verified.isoformat() if loc.last_verified else None
    }
    if origin:
        distance_m = haversine_distance(origin["latitude"], origin["longitude"], loc.latitude, loc.longitude)
        payload.update({
            "distance_m": round(distance_m, 2),
            "distance_text": format_distance(distance_m),
            "walking_duration_s": int(round(distance_m / WALKING_SPEED_M_PER_S)),
            "walking_time": format_duration(distance_m / WALKING_SPEED_M_PER_S)
        })
    return payload


@router.get("")
def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all navigation locations with pagination, category filter, and search."""
    query = db.query(NavigationLocation)
    
    if category:
        query = query.filter(NavigationLocation.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (NavigationLocation.name.ilike(search_term)) |
            (NavigationLocation.description.ilike(search_term)) |
            (NavigationLocation.address.ilike(search_term))
        )
    
    locations = query.order_by(NavigationLocation.name).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "locations": [make_location_payload(loc) for loc in locations],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories of navigation locations."""
    categories = db.query(NavigationLocation.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}


@router.get("/{location_id}")
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a specific navigation location by ID."""
    location = db.query(NavigationLocation).filter(NavigationLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return {
        "id": location.id,
        "name": location.name,
        "category": location.category,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "address": location.address,
        "description": location.description,
        "opening_hours": location.opening_hours,
        "contact_number": location.contact_number,
        "wheelchair_accessible": location.wheelchair_accessible,
        "source": location.source,
        "last_verified": location.last_verified.isoformat() if location.last_verified else None,
        "created_at": location.created_at.isoformat() if location.created_at else None,
        "updated_at": location.updated_at.isoformat() if location.updated_at else None
    }


@router.get("/category/{category}")
def get_locations_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all locations in a specific category."""
    locations = db.query(NavigationLocation).filter(
        NavigationLocation.category == category
    ).order_by(NavigationLocation.name).offset(skip).limit(limit).all()
    
    return {
        "category": category,
        "locations": [make_location_payload(loc) for loc in locations],
        "count": len(locations)
    }


@router.get("/nearest")
def get_nearest_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    category: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Find nearest locations to given coordinates."""
    query = db.query(NavigationLocation)
    
    if category:
        query = query.filter(NavigationLocation.category == category)
    
    locations = query.all()
    
    # Calculate distances and sort
    locations_with_distance = []
    for loc in locations:
        distance = haversine_distance(latitude, longitude, loc.latitude, loc.longitude)
        locations_with_distance.append({
            "location": loc,
            "distance_m": distance
        })
    
    locations_with_distance.sort(key=lambda x: x["distance_m"])
    
    # Return top results
    results = locations_with_distance[:limit]
    
    return {
        "user_location": {"latitude": latitude, "longitude": longitude},
        "nearest": [make_location_payload(item["location"], origin={"latitude": latitude, "longitude": longitude}) for item in results],
        "count": len(results)
    }


@navigation_router.get("/reverse")
def reverse_geocode(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Reverse geocode a coordinate into a readable place name."""
    query = urlencode({
        "format": "jsonv2",
        "lat": latitude,
        "lon": longitude,
        "addressdetails": 1,
        "zoom": 16
    })
    url = f"https://nominatim.openstreetmap.org/reverse?{query}"
    request = Request(url, headers={
        "User-Agent": "OURS-TTD-Nav/1.0 (contact@example.com)",
        "Accept-Language": "en"
    })
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "display_name": data.get("display_name", "Current Location"),
                "address": data.get("address", {}),
                "raw": data
            }
    except (HTTPError, URLError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Reverse geocoding failed: {exc}")


@navigation_router.get("/nearby")
def get_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    category: Optional[str] = None,
    limit: int = Query(5, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Find the nearest facilities using walking distance estimates."""
    query = db.query(NavigationLocation)
    if category:
        query = query.filter(NavigationLocation.category == category)

    locations = query.all()
    locations_with_distance = []
    for loc in locations:
        distance = haversine_distance(latitude, longitude, loc.latitude, loc.longitude)
        locations_with_distance.append({"location": loc, "distance_m": distance})

    locations_with_distance.sort(key=lambda x: x["distance_m"])
    results = locations_with_distance[:limit]
    return {
        "user_location": {"latitude": latitude, "longitude": longitude},
        "nearest": [make_location_payload(item["location"], origin={"latitude": latitude, "longitude": longitude}) for item in results],
        "count": len(results)
    }


@navigation_router.get("/route")
def get_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    destination_id: Optional[int] = Query(None, ge=1),
    destination_lat: Optional[float] = Query(None, ge=-90, le=90),
    destination_lng: Optional[float] = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db)
):
    """Fetch a walking route using OSRM and return route summary with step-by-step guidance."""
    if destination_id is not None:
        destination = db.query(NavigationLocation).filter(NavigationLocation.id == destination_id).first()
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        destination_lat = destination.latitude
        destination_lng = destination.longitude
        destination_name = destination.name
    elif destination_lat is None or destination_lng is None:
        raise HTTPException(status_code=422, detail="Destination coordinates must be provided")
    else:
        destination_name = "Destination"

    def fetch_osrm(profile: str) -> dict:
        coords = f"{origin_lng},{origin_lat};{destination_lng},{destination_lat}"
        url = f"https://router.project-osrm.org/route/v1/{profile}/{coords}?overview=full&geometries=geojson&steps=true&annotations=distance,duration"
        request = Request(url, headers={"User-Agent": "OURS-TTD-Nav/1.0"})
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())

    route_data = None
    for profile in ["foot", "driving"]:
        try:
            route_data = fetch_osrm(profile)
            if route_data.get("code") == "Ok":
                break
        except Exception:
            route_data = None
    if not route_data or route_data.get("code") != "Ok":
        raise HTTPException(status_code=502, detail="Routing service unavailable")

    route = route_data["routes"][0]
    leg = route["legs"][0]
    now = datetime.now(timezone.utc)
    eta = now + timedelta(seconds=int(route["duration"]))
    instructions = []
    for step in leg.get("steps", []):
        maneuver = step.get("maneuver", {})
        instruction = maneuver.get("instruction")
        if not instruction:
            step_name = step.get("name") or "road"
            maneuver_type = maneuver.get("type", "continue").replace("_", " ")
            modifier = maneuver.get("modifier", "")
            instruction = f"{maneuver_type.capitalize()} {modifier} on {step_name}".strip()
        instructions.append({
            "instruction": instruction,
            "distance_m": step.get("distance", 0),
            "distance_text": format_distance(step.get("distance", 0)),
            "duration_text": format_duration(step.get("duration", 0))
        })

    return {
        "origin": {"latitude": origin_lat, "longitude": origin_lng},
        "destination": {
            "latitude": destination_lat,
            "longitude": destination_lng,
            "name": destination_name
        },
        "distance_m": route["distance"],
        "distance_text": format_distance(route["distance"]),
        "duration_s": int(round(route["duration"])),
        "duration_text": format_duration(route["duration"]),
        "eta": eta.astimezone().isoformat(),
        "geometry": route["geometry"],
        "instructions": instructions,
        "route_type": profile,
        "current_crowd": "Normal"
    }


@router.post("/")
def create_location(
    location_data: NavigationLocationIn,
    claims = Depends(current_claims),
    db: Session = Depends(get_db)
):
    """Create a new navigation location (admin only)."""
    # Check if user is admin
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_location = NavigationLocation(**location_data.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return {
        "id": new_location.id,
        "name": new_location.name,
        "message": "Location created successfully"
    }


@router.put("/{location_id}")
def update_location(
    location_id: int,
    location_data: NavigationLocationUpdate,
    claims = Depends(current_claims),
    db: Session = Depends(get_db)
):
    """Update an existing navigation location (admin only)."""
    # Check if user is admin
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    location = db.query(NavigationLocation).filter(NavigationLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Update only provided fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    
    return {
        "id": location.id,
        "name": location.name,
        "message": "Location updated successfully"
    }


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    claims = Depends(current_claims),
    db: Session = Depends(get_db)
):
    """Delete a navigation location (admin only)."""
    # Check if user is admin
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    location = db.query(NavigationLocation).filter(NavigationLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()
    
    return {"message": "Location deleted successfully"}
