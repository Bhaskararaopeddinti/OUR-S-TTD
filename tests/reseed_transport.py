"""
Re-seed transport routes with updated names
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from backend.database import SessionLocal, Base, engine
from backend.models import TransportRoute
from datetime import datetime

db = SessionLocal()
try:
    # Delete existing transport routes
    db.query(TransportRoute).delete()
    db.commit()
    
    # Add updated routes
    db.add_all([
        TransportRoute(
            source_location="Tirupati Bus Stand",
            destination_location="Tirumala",
            vehicle_type="GOVERNMENT_BUS",
            operator="APSRTC",
            route_name="Tirupati Central Bus Stand to Tirumala Ghat Road",
            estimated_duration="45 - 60 mins",
            fare="Rs.65 / person",
            operating_hours="24 Hours Active",
            frequency="Every 2-3 mins",
            status="Available",
            source="TTD Official Verified"
        ),
        TransportRoute(
            source_location="Tirumala",
            destination_location="Tirupati Bus Stand",
            vehicle_type="GOVERNMENT_BUS",
            operator="APSRTC",
            route_name="Tirumala to Tirupati Central Bus Stand (Return)",
            estimated_duration="45 - 60 mins",
            fare="Rs.65 / person",
            operating_hours="24 Hours Active",
            frequency="Every 2-3 mins",
            status="Available",
            source="TTD Official Verified"
        ),
        TransportRoute(
            source_location="Tirupati Railway Station",
            destination_location="Tirumala",
            vehicle_type="TTD_BUS",
            operator="TTD Devasthanams",
            route_name="Tirupati Railway Station to Tirumala via Alipiri",
            estimated_duration="60 - 75 mins",
            fare="FREE",
            operating_hours="4:00 AM - 10:00 PM",
            frequency="Every 15 mins",
            status="Available",
            source="100% Free TTD Service"
        ),
        TransportRoute(
            source_location="Tirumala",
            destination_location="Tirupati Railway Station",
            vehicle_type="TTD_BUS",
            operator="TTD Devasthanams",
            route_name="Tirumala to Tirupati Railway Station (Return)",
            estimated_duration="60 - 75 mins",
            fare="FREE",
            operating_hours="4:00 AM - 10:00 PM",
            frequency="Every 15 mins",
            status="Available",
            source="100% Free TTD Service"
        ),
        TransportRoute(
            source_location="Alipiri Checkpost",
            destination_location="Tirumala",
            vehicle_type="WALKING",
            operator="TTD Footpath Trek",
            route_name="Alipiri Footpath (3,550 Steps)",
            estimated_duration="3 - 4 Hours",
            fare="Free (Traditional Trek)",
            operating_hours="24 Hours Active",
            frequency="Continuous",
            status="Open",
            source="TTD Verified Footpath"
        ),
        TransportRoute(
            source_location="Tirumala",
            destination_location="Alipiri Checkpost",
            vehicle_type="WALKING",
            operator="TTD Footpath Trek",
            route_name="Tirumala to Alipiri Footpath (Descent)",
            estimated_duration="2 - 3 Hours",
            fare="Free (Traditional Trek)",
            operating_hours="24 Hours Active",
            frequency="Continuous",
            status="Open",
            source="TTD Verified Footpath"
        ),
        TransportRoute(
            source_location="CRO Tirumala",
            destination_location="VQC Queue Complex",
            vehicle_type="TTD_BUS",
            operator="TTD Devasthanams",
            route_name="TTD Free Dharma Ratham (Internal Shuttle)",
            estimated_duration="10 - 20 mins",
            fare="FREE",
            operating_hours="24 Hours Active",
            frequency="Continuous",
            status="Available",
            source="100% Free TTD Service"
        ),
        TransportRoute(
            source_location="Srivari Mettu",
            destination_location="Tirumala",
            vehicle_type="WALKING",
            operator="TTD Footpath Trek",
            route_name="Srivari Mettu Traditional Trek (2,388 Steps)",
            estimated_duration="2 - 3 Hours",
            fare="Free (Traditional Trek)",
            operating_hours="6:00 AM - 5:00 PM",
            frequency="Continuous",
            status="Open",
            source="TTD Verified Footpath"
        )
    ])
    
    db.commit()
    print("Transport routes re-seeded successfully!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
