"""
OURS TTD — Travel & Transport Router
APIs for managing and querying verified transport options (buses, shuttles, walking, package tours).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import math

from ..database import get_db
from ..models import TransportRoute, TransportType, NavigationLocation, User
from ..schemas import TransportRouteIn, TransportRouteUpdate
from ..auth import current_claims

router = APIRouter(prefix="/api/transport", tags=["Travel & Transport"])

# TTD area bounding box (approximately covers Tirumala, Tirupati, and nearby pilgrimage areas)
TTD_AREA_BOUNDS = {
    "min_lat": 13.3,
    "max_lat": 13.75,
    "min_lng": 79.25,
    "max_lng": 80.0
}

# Major transport hubs in TTD area for fallback routing
MAJOR_TRANSPORT_HUBS = [
    "Tirumala",
    "Tirupati",
    "Tirupati Central Bus Stand",
    "Tirupati Railway Station",
    "Alipiri Checkpost",
    "Tirumala Bus Stand"
]


def is_location_in_ttd_area(location_name: str, db: Session) -> bool:
    """Check if a location is within the TTD/Tirumala/Tirupati pilgrimage area."""
    # First try to find the location in the database
    location = db.query(NavigationLocation).filter(
        NavigationLocation.name.ilike(f"%{location_name}%")
    ).first()
    
    if location:
        # Check if coordinates are within TTD area bounds
        if (TTD_AREA_BOUNDS["min_lat"] <= location.latitude <= TTD_AREA_BOUNDS["max_lat"] and
            TTD_AREA_BOUNDS["min_lng"] <= location.longitude <= TTD_AREA_BOUNDS["max_lng"]):
            return True
    
    # Fallback: check if location name contains TTD-area keywords
    ttd_keywords = [
        "tirumala", "tirupati", "alipiri", "srivari mettu", "kapila", "tiruchanoor",
        "srinivasa mangapuram", "thondavada", "govindaraja", "vakulamatha",
        "karvetinagaram", "nagalapuram", "narayanavanam", "appalayagunta",
        "nagari", "bugga", "surutupalli", "padmavathi", "kalyana venkateswara"
    ]
    
    location_lower = location_name.lower()
    for keyword in ttd_keywords:
        if keyword in location_lower:
            return True
    
    return False


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate Haversine distance between two coordinates in kilometers."""
    if not all([lat1, lng1, lat2, lng2]):
        return 0.0
    
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng/2) * math.sin(dlng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def estimate_duration(distance_km: float) -> str:
    """Estimate travel duration based on distance."""
    if distance_km == 0:
        return "N/A"
    elif distance_km < 5:
        return "10 - 20 mins"
    elif distance_km < 15:
        return "20 - 40 mins"
    elif distance_km < 30:
        return "40 - 60 mins"
    else:
        return "60 - 90 mins"


def find_nearest_transport_hub(location_name: str, db: Session) -> Optional[str]:
    """Find the nearest major transport hub to a given location."""
    location = db.query(NavigationLocation).filter(
        NavigationLocation.name.ilike(f"%{location_name}%")
    ).first()
    
    if not location:
        return None
    
    nearest_hub = None
    min_distance = float('inf')
    
    for hub_name in MAJOR_TRANSPORT_HUBS:
        hub = db.query(NavigationLocation).filter(
            NavigationLocation.name.ilike(f"%{hub_name}%")
        ).first()
        
        if hub:
            distance = calculate_distance(
                location.latitude, location.longitude,
                hub.latitude, hub.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_hub = hub.name
    
    return nearest_hub


def generate_fallback_transport(from_location: str, to_location: str, db: Session) -> dict:
    """Generate a fallback transport recommendation when no direct route exists."""
    # Get location coordinates for distance calculation
    from_loc = db.query(NavigationLocation).filter(
        NavigationLocation.name.ilike(f"%{from_location}%")
    ).first()
    
    to_loc = db.query(NavigationLocation).filter(
        NavigationLocation.name.ilike(f"%{to_location}%")
    ).first()
    
    # Calculate distance if coordinates available
    distance_km = 0.0
    if from_loc and to_loc:
        distance_km = calculate_distance(
            from_loc.latitude, from_loc.longitude,
            to_loc.latitude, to_loc.longitude
        )
    
    # Find nearest hub for route suggestion
    nearest_hub = find_nearest_transport_hub(from_location, db)
    
    # Determine appropriate vehicle type based on distance
    if distance_km > 0:
        if distance_km < 3:
            vehicle_type = "Walking / Auto"
            operator = "Local Transport"
        elif distance_km < 20:
            vehicle_type = "Local / Government Bus"
            operator = "APSRTC / TTD"
        else:
            vehicle_type = "Bus / Taxi"
            operator = "APSRTC / Licensed Operators"
    else:
        vehicle_type = "Local / Government Bus"
        operator = "APSRTC / TTD"
    
    # Generate route description
    if nearest_hub and nearest_hub.lower() != to_location.lower():
        route_description = f"Connect via {nearest_hub} to reach destination. Verify local transport availability."
    else:
        route_description = "Direct connection available. Verify current transport service at the location."
    
    return {
        "id": 0,  # Fallback routes have ID 0
        "transport_type_id": None,
        "source_location": from_location,
        "destination_location": to_location,
        "vehicle_type": vehicle_type,
        "operator": operator,
        "route_name": "Recommended Transport Connection",
        "route_description": route_description,
        "estimated_duration": estimate_duration(distance_km),
        "fare": "Verify locally",
        "operating_hours": "Verify locally",
        "frequency": "Verify locally",
        "booking_required": False,
        "data_status": "FALLBACK",
        "status": "Available",
        "live_status": "Reference recommendation – verify current service",
        "source": "System Generated Recommendation",
        "source_url": "https://ttdevasthanams.ap.gov.in",
        "last_verified": datetime.utcnow().strftime("%d/%m/%Y"),
        "is_fallback": True,
        "coords": {
            "source": {"lat": from_loc.latitude, "lng": from_loc.longitude} if from_loc else None,
            "destination": {"lat": to_loc.latitude, "lng": to_loc.longitude} if to_loc else None
        }
    }


@router.get("/types")
def get_transport_types(db: Session = Depends(get_db)):
    """Retrieve verified transport categories."""
    types = db.query(TransportType).all()
    if not types:
        # Fallback default types
        types = [
            {"id": 1, "name": "APSRTC Bus", "description": "Regular & Express buses", "operator": "APSRTC", "is_free": False},
            {"id": 2, "name": "TTD Free Bus", "description": "Free pilgrim shuttle buses", "operator": "TTD Devasthanams", "is_free": True},
            {"id": 3, "name": "Dharma Radham", "description": "Free internal Tirumala shuttles", "operator": "TTD Devasthanams", "is_free": True},
            {"id": 4, "name": "Package Tour", "description": "Local & Surrounding temple tours", "operator": "TTD / APSRTC", "is_free": False},
            {"id": 5, "name": "Taxi / Cab", "description": "Licensed cabs & private vehicles", "operator": "Licensed Operators", "is_free": False},
            {"id": 6, "name": "Walking", "description": "Alipiri & Srivari Mettu footpaths", "operator": "TTD Footpath Trek", "is_free": True},
        ]
    return {"status": "success", "count": len(types), "types": types}


@router.get("/routes")
def get_all_routes(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieve all verified transport routes."""
    routes = db.query(TransportRoute).offset(skip).limit(limit).all()
    return {"status": "success", "count": len(routes), "routes": routes}


@router.get("/search")
def search_routes(
    from_location: Optional[str] = Query(None),
    to_location: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    data_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Search transport routes by origin, destination, or vehicle type with fallback support."""
    # Validate locations if provided
    if from_location and not is_location_in_ttd_area(from_location, db):
        return {
            "status": "error",
            "message": "This transport service currently covers Tirumala, Tirupati and nearby pilgrimage locations.",
            "count": 0,
            "routes": []
        }
    
    if to_location and not is_location_in_ttd_area(to_location, db):
        return {
            "status": "error",
            "message": "This transport service currently covers Tirumala, Tirupati and nearby pilgrimage locations.",
            "count": 0,
            "routes": []
        }
    
    query = db.query(TransportRoute)

    if from_location:
        query = query.filter(TransportRoute.source_location.ilike(f"%{from_location}%"))
    if to_location:
        query = query.filter(TransportRoute.destination_location.ilike(f"%{to_location}%"))
    if vehicle_type:
        query = query.filter(TransportRoute.vehicle_type.ilike(f"%{vehicle_type}%"))
    if data_status:
        query = query.filter(TransportRoute.data_status.ilike(f"%{data_status}%"))

    routes = query.all()

    # Match location coordinates for map navigation if available
    locations_map = {loc.name.lower(): loc for loc in db.query(NavigationLocation).all()}

    enriched_routes = []
    for r in routes:
        src_loc = locations_map.get(r.source_location.lower()) if r.source_location else None
        dst_loc = locations_map.get(r.destination_location.lower()) if r.destination_location else None

        r_dict = {
            "id": r.id,
            "transport_type_id": r.transport_type_id,
            "source_location": r.source_location,
            "destination_location": r.destination_location,
            "vehicle_type": r.vehicle_type,
            "operator": r.operator,
            "route_name": r.route_name,
            "route_description": r.route_description or "",
            "estimated_duration": r.estimated_duration,
            "fare": r.fare,
            "operating_hours": r.operating_hours,
            "frequency": r.frequency,
            "booking_required": r.booking_required,
            "data_status": r.data_status or "VERIFIED",
            "status": r.status,
            "live_status": r.live_status or "Live bus tracking unavailable",
            "source": r.source or "Official TTD / APSRTC",
            "source_url": r.source_url or "https://ttdevasthanams.ap.gov.in",
            "last_verified": r.last_verified.strftime("%d/%m/%Y") if r.last_verified else datetime.utcnow().strftime("%d/%m/%Y"),
            "is_fallback": False,
            "coords": {
                "source": {"lat": src_loc.latitude, "lng": src_loc.longitude} if src_loc else None,
                "destination": {"lat": dst_loc.latitude, "lng": dst_loc.longitude} if dst_loc else None
            }
        }
        enriched_routes.append(r_dict)

    # FALLBACK: If no routes found and both locations are valid TTD locations, generate fallback
    if not enriched_routes and from_location and to_location:
        if is_location_in_ttd_area(from_location, db) and is_location_in_ttd_area(to_location, db):
            fallback_route = generate_fallback_transport(from_location, to_location, db)
            enriched_routes.append(fallback_route)

    return {
        "status": "success",
        "count": len(enriched_routes),
        "filters": {
            "from_location": from_location,
            "to_location": to_location,
            "vehicle_type": vehicle_type
        },
        "routes": enriched_routes
    }


@router.get("/recommend")
def recommend_transport(
    from_location: Optional[str] = Query("Tirupati Railway Station"),
    to_location: Optional[str] = Query("Tirumala"),
    is_free_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Transport recommendation engine based on user origin, destination, and budget."""
    query = db.query(TransportRoute)
    if from_location:
        query = query.filter(TransportRoute.source_location.ilike(f"%{from_location}%"))
    if to_location:
        query = query.filter(TransportRoute.destination_location.ilike(f"%{to_location}%"))

    routes = query.all()

    if is_free_only:
        routes = [r for r in routes if "free" in r.fare.lower()]

    recommendation = None
    if routes:
        # Prioritize free buses or regular APSRTC service
        free_opt = next((r for r in routes if "free" in r.fare.lower()), None)
        recommendation = free_opt or routes[0]

    return {
        "status": "success",
        "recommended": recommendation,
        "all_options_count": len(routes),
        "all_options": routes
    }


@router.get("/routes/{route_id}")
def get_route_by_id(route_id: int, db: Session = Depends(get_db)):
    """Retrieve single transport route details."""
    route = db.query(TransportRoute).filter(TransportRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Transport route not found")
    return {"status": "success", "route": route}


@router.post("/admin/routes", status_code=201)
def create_route(
    data: TransportRouteIn,
    db: Session = Depends(get_db),
    claims: dict = Depends(current_claims)
):
    """Create a new transport route (Admin / SuperAdmin only)."""
    if claims.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Forbidden: Admin credentials required.")

    new_route = TransportRoute(
        source_location=data.source_location,
        destination_location=data.destination_location,
        vehicle_type=data.vehicle_type,
        operator=data.operator,
        route_name=data.route_name,
        route_description=data.route_description or "",
        estimated_duration=data.estimated_duration,
        fare=data.fare,
        operating_hours=data.operating_hours,
        frequency=data.frequency,
        status=data.status,
        data_status=data.data_status or "VERIFIED",
        source=data.source or "Admin Verified",
        source_url=data.source_url or "https://ttdevasthanams.ap.gov.in",
        last_verified=datetime.utcnow()
    )
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return {"status": "success", "message": "Transport route created successfully", "route": new_route}


@router.put("/admin/routes/{route_id}")
def update_route(
    route_id: int,
    data: TransportRouteUpdate,
    db: Session = Depends(get_db),
    claims: dict = Depends(current_claims)
):
    """Update a transport route (Admin only)."""
    if claims.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Forbidden: Admin credentials required.")

    route = db.query(TransportRoute).filter(TransportRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Transport route not found")

    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(route, key, value)

    route.last_verified = datetime.utcnow()

    db.commit()
    db.refresh(route)
    return {"status": "success", "message": "Route updated successfully", "route": route}


@router.delete("/admin/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(current_claims)
):
    """Delete a transport route (Admin only)."""
    if claims.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Forbidden: Admin credentials required.")

    route = db.query(TransportRoute).filter(TransportRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Transport route not found")

    db.delete(route)
    db.commit()
    return {"status": "success", "message": "Transport route deleted successfully"}
