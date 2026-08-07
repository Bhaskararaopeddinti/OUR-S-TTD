"""
OURS TTD — Navigation Locations Router
REST API for Smart Navigation module with Leaflet.js and OpenStreetMap.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.database import get_db
from backend.models import NavigationLocation
from backend.schemas import NavigationLocationIn, NavigationLocationUpdate
from backend.auth import current_claims
from math import radians, sin, cos, sqrt, atan2

router = APIRouter(prefix="/api/locations", tags=["Navigation Locations"])


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
        "locations": [
            {
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
                "last_verified": loc.last_verified.isoformat() if loc.last_verified else None
            }
            for loc in locations
        ],
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
        "locations": [
            {
                "id": loc.id,
                "name": loc.name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "description": loc.description,
                "opening_hours": loc.opening_hours,
                "contact_number": loc.contact_number,
                "wheelchair_accessible": loc.wheelchair_accessible
            }
            for loc in locations
        ],
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
        "nearest": [
            {
                "id": item["location"].id,
                "name": item["location"].name,
                "category": item["location"].category,
                "latitude": item["location"].latitude,
                "longitude": item["location"].longitude,
                "address": item["location"].address,
                "description": item["location"].description,
                "opening_hours": item["location"].opening_hours,
                "contact_number": item["location"].contact_number,
                "wheelchair_accessible": item["location"].wheelchair_accessible,
                "distance_m": round(item["distance_m"], 2),
                "distance_km": round(item["distance_m"] / 1000, 2)
            }
            for item in results
        ],
        "count": len(results)
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
