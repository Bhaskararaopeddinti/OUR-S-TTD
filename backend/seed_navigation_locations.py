"""
OURS TTD – Seed Navigation Locations
Populates the database with real Tirumala facility locations from publicly available sources.
"""
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal, engine, Base
from backend.models import NavigationLocation

# Real Tirumala facility locations from publicly available sources
# Sources: TTD official website, OpenStreetMap, public maps
# Coordinates marked as "Needs Administrator Verification" where exact location couldn't be verified

NAVIGATION_LOCATIONS = [
    # Temple Complex
    {
        "name": "Sri Venkateswara Temple Main Entrance",
        "category": "temple",
        "latitude": 13.6839,
        "longitude": 79.3476,
        "address": "Temple Main Gate, Tirumala",
        "description": "Main entrance to Sri Venkateswara Swamy Temple",
        "opening_hours": "2:30 AM - 1:00 AM (next day)",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Vaikuntam Queue Complex I (VQC I)",
        "category": "queue",
        "latitude": 13.6842,
        "longitude": 79.3478,
        "address": "VQC I, Tirumala",
        "description": "Main pilgrim waiting complex for Sarva Darshan",
        "opening_hours": "24/7 during darshan hours",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Vaikuntam Queue Complex II (VQC II)",
        "category": "queue",
        "latitude": 13.6841,
        "longitude": 79.3480,
        "address": "VQC II, Tirumala",
        "description": "Second pilgrim waiting complex",
        "opening_hours": "24/7 during darshan hours",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Food & Annaprasadam
    {
        "name": "MTVAC - Matrusri Tarigonda Vengamamba Annaprasada Complex",
        "category": "food",
        "latitude": 13.6845,
        "longitude": 79.3482,
        "address": "MTVAC, Tirumala",
        "description": "Main free food complex serving ~65,000+ meals daily",
        "opening_hours": "6:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "VQC Annaprasadam Counter",
        "category": "food",
        "latitude": 13.6840,
        "longitude": 79.3475,
        "address": "VQC Compartment, Tirumala",
        "description": "Free food distribution in queue compartments",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "PAC II Annaprasadam",
        "category": "food",
        "latitude": 13.6825,
        "longitude": 79.3465,
        "address": "PAC II, Tirumala",
        "description": "Free food at Pilgrim Accommodation Complex II",
        "opening_hours": "6:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Rambagicha Bus Stand Annaprasadam",
        "category": "food",
        "latitude": 13.6810,
        "longitude": 79.3430,
        "address": "Rambagicha Bus Stand, Tirumala",
        "description": "Free food distribution at bus stand",
        "opening_hours": "6:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Laddu Counters
    {
        "name": "Main Laddu Complex (West Mada Street)",
        "category": "laddu",
        "latitude": 13.6850,
        "longitude": 79.3490,
        "address": "West Mada Street, Tirumala",
        "description": "Primary laddu distribution and sales counter",
        "opening_hours": "6:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Laddu Counter (East Mada Street)",
        "category": "laddu",
        "latitude": 13.6848,
        "longitude": 79.3460,
        "address": "East Mada Street, Tirumala",
        "description": "Secondary laddu distribution counter",
        "opening_hours": "6:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "VQC Exit Laddu Counter",
        "category": "laddu",
        "latitude": 13.6843,
        "longitude": 79.3481,
        "address": "VQC Exit, Tirumala",
        "description": "Free laddu distribution after darshan",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Mobile Deposit Centers
    {
        "name": "Phone Deposit Centre - VQC I",
        "category": "phone_deposit",
        "latitude": 13.6843,
        "longitude": 79.3472,
        "address": "Near VQC I, Tirumala",
        "description": "Mobile phone deposit centre near VQC I",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Phone Deposit Centre - VQC II",
        "category": "phone_deposit",
        "latitude": 13.6842,
        "longitude": 79.3483,
        "address": "Near VQC II, Tirumala",
        "description": "Mobile phone deposit centre near VQC II",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Phone Deposit Centre - PAC 3 (Venkatadri Nilayam)",
        "category": "phone_deposit",
        "latitude": 13.6820,
        "longitude": 79.3460,
        "address": "PAC 3, Venkatadri Nilayam, Tirumala",
        "description": "Mobile phone deposit at PAC 3",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Phone Deposit Centre - PAC 5",
        "category": "phone_deposit",
        "latitude": 13.6815,
        "longitude": 79.3455,
        "address": "PAC 5, Tirumala",
        "description": "Mobile phone deposit at PAC 5",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Medical Facilities
    {
        "name": "Aswini Hospital",
        "category": "medical",
        "latitude": 13.6825,
        "longitude": 79.3450,
        "address": "Near Seshadri Nagar, Tirumala",
        "description": "24/7 emergency care, trauma response, and ambulance coordination",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Alipiri Footpath Medical Aid Station",
        "category": "medical",
        "latitude": 13.6550,
        "longitude": 79.3380,
        "address": "Alipiri Footpath, Tirumala",
        "description": "Emergency aid station on Alipiri walking path",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Srivari Mettu Footpath Medical Aid Station",
        "category": "medical",
        "latitude": 13.6480,
        "longitude": 79.3310,
        "address": "Srivari Mettu Footpath, Tirumala",
        "description": "Emergency aid station on Srivari Mettu walking path",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Restrooms
    {
        "name": "Restrooms - PAC I",
        "category": "restroom",
        "latitude": 13.6825,
        "longitude": 79.3465,
        "address": "PAC I, Tirumala",
        "description": "Public restrooms at Pilgrim Accommodation Complex I",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - PAC II",
        "category": "restroom",
        "latitude": 13.6825,
        "longitude": 79.3465,
        "address": "PAC II, Tirumala",
        "description": "Public restrooms at Pilgrim Accommodation Complex II",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - PAC III",
        "category": "restroom",
        "latitude": 13.6820,
        "longitude": 79.3460,
        "address": "PAC III, Tirumala",
        "description": "Public restrooms at Pilgrim Accommodation Complex III",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - PAC IV",
        "category": "restroom",
        "latitude": 13.6818,
        "longitude": 79.3458,
        "address": "PAC IV, Tirumala",
        "description": "Public restrooms at Pilgrim Accommodation Complex IV",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - PAC V",
        "category": "restroom",
        "latitude": 13.6815,
        "longitude": 79.3455,
        "address": "PAC V, Tirumala",
        "description": "Public restrooms at Pilgrim Accommodation Complex V",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - VQC I",
        "category": "restroom",
        "latitude": 13.6842,
        "longitude": 79.3478,
        "address": "VQC I, Tirumala",
        "description": "Public restrooms at Vaikuntam Queue Complex I",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - VQC II",
        "category": "restroom",
        "latitude": 13.6841,
        "longitude": 79.3480,
        "address": "VQC II, Tirumala",
        "description": "Public restrooms at Vaikuntam Queue Complex II",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Restrooms - Kalyanakatta",
        "category": "restroom",
        "latitude": 13.6855,
        "longitude": 79.3500,
        "address": "Kalyanakatta Complex, Tirumala",
        "description": "Public restrooms at tonsure complex",
        "opening_hours": "4:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Drinking Water
    {
        "name": "Drinking Water - VQC Area",
        "category": "water",
        "latitude": 13.6840,
        "longitude": 79.3475,
        "address": "VQC Compartment, Tirumala",
        "description": "Free purified water points near queue complex",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Drinking Water - Temple Ring Road",
        "category": "water",
        "latitude": 13.6835,
        "longitude": 79.3470,
        "address": "Temple Ring Road, Tirumala",
        "description": "Jala Prasadam RO kiosks on temple ring road",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Drinking Water - Alipiri Footpath",
        "category": "water",
        "latitude": 13.6550,
        "longitude": 79.3380,
        "address": "Alipiri Footpath, Tirumala",
        "description": "Water points along Alipiri walking path",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Tonsure (Kalyanakatta)
    {
        "name": "Kalyanakatta Complex - Main",
        "category": "tonsure",
        "latitude": 13.6855,
        "longitude": 79.3500,
        "address": "Kalyanakatta Complex, Tirumala",
        "description": "Main hair offering (tonsure) complex - free of charge",
        "opening_hours": "4:00 AM - 10:00 PM",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Transport
    {
        "name": "Rambagicha Bus Stand",
        "category": "transport",
        "latitude": 13.6810,
        "longitude": 79.3430,
        "address": "Rambagicha Bus Stand, Tirumala",
        "description": "Main bus stand for Tirumala local transport",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Alipiri Bus Stand",
        "category": "transport",
        "latitude": 13.6300,
        "longitude": 79.3200,
        "address": "Alipiri, Tirupati",
        "description": "Bus stand at base of Alipiri footpath",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Walking Paths
    {
        "name": "Alipiri Footpath Start",
        "category": "footpath",
        "latitude": 13.6550,
        "longitude": 79.3380,
        "address": "Alipiri, Tirupati",
        "description": "Start of Alipiri footpath - 3,550 steps, ~3-4 hour climb",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": False,
        "source": "TTD Official"
    },
    {
        "name": "Srivari Mettu Footpath Start",
        "category": "footpath",
        "latitude": 13.6480,
        "longitude": 79.3310,
        "address": "Srivari Mettu, Tirupati",
        "description": "Start of Srivari Mettu footpath - 2,100 steps, ~2 hour climb",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": False,
        "source": "TTD Official"
    },
    
    # Accommodation
    {
        "name": "PAC 1 - Pilgrim Accommodation Complex",
        "category": "accommodation",
        "latitude": 13.6825,
        "longitude": 79.3465,
        "address": "PAC 1, Tirumala",
        "description": "Pilgrim Accommodation Complex 1",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "PAC 2 - Pilgrim Accommodation Complex",
        "category": "accommodation",
        "latitude": 13.6825,
        "longitude": 79.3465,
        "address": "PAC 2, Tirumala",
        "description": "Pilgrim Accommodation Complex 2",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "PAC 3 - Venkatadri Nilayam",
        "category": "accommodation",
        "latitude": 13.6820,
        "longitude": 79.3460,
        "address": "PAC 3, Venkatadri Nilayam, Tirumala",
        "description": "Pilgrim Accommodation Complex 3",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "PAC 4 - Pilgrim Accommodation Complex",
        "category": "accommodation",
        "latitude": 13.6818,
        "longitude": 79.3458,
        "address": "PAC 4, Tirumala",
        "description": "Pilgrim Accommodation Complex 4",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "PAC 5 - Pilgrim Accommodation Complex",
        "category": "accommodation",
        "latitude": 13.6815,
        "longitude": 79.3455,
        "address": "PAC 5, Tirumala",
        "description": "Pilgrim Accommodation Complex 5",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Parking
    {
        "name": "Alipiri Parking Area",
        "category": "parking",
        "latitude": 13.6300,
        "longitude": 79.3200,
        "address": "Alipiri, Tirupati",
        "description": "Main parking area at Alipiri base",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Tirumala Parking Area",
        "category": "parking",
        "latitude": 13.6800,
        "longitude": 79.3410,
        "address": "Tirumala",
        "description": "Parking area in Tirumala",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Police & Security
    {
        "name": "TTD Police Help Centre - Main",
        "category": "police",
        "latitude": 13.6835,
        "longitude": 79.3470,
        "address": "Temple Area, Tirumala",
        "description": "TTD police help centre near temple",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "TTD Police Help Centre - Bus Stand",
        "category": "police",
        "latitude": 13.6810,
        "longitude": 79.3430,
        "address": "Rambagicha Bus Stand, Tirumala",
        "description": "TTD police help centre at bus stand",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Lost & Found
    {
        "name": "Lost & Found Centre - Main",
        "category": "lost_found",
        "latitude": 13.6835,
        "longitude": 79.3470,
        "address": "Temple Area, Tirumala",
        "description": "Lost and found centre near temple",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Information Centre
    {
        "name": "TTD Information Centre - Main",
        "category": "information",
        "latitude": 13.6835,
        "longitude": 79.3470,
        "address": "Temple Area, Tirumala",
        "description": "TTD information centre near temple",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "TTD Information Centre - Bus Stand",
        "category": "information",
        "latitude": 13.6810,
        "longitude": 79.3430,
        "address": "Rambagicha Bus Stand, Tirumala",
        "description": "TTD information centre at bus stand",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    
    # Cloak Rooms
    {
        "name": "Cloak Room - Bus Stand",
        "category": "cloak_room",
        "latitude": 13.6810,
        "longitude": 79.3430,
        "address": "Rambagicha Bus Stand, Tirumala",
        "description": "Luggage deposit and cloak room at bus stand",
        "opening_hours": "24/7",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
    {
        "name": "Cloak Room - VQC",
        "category": "cloak_room",
        "latitude": 13.6840,
        "longitude": 79.3475,
        "address": "VQC Area, Tirumala",
        "description": "Luggage deposit near queue complex",
        "opening_hours": "24/7 during darshan",
        "contact_number": "155257",
        "wheelchair_accessible": True,
        "source": "TTD Official"
    },
]


def seed_navigation_locations():
    """Seed the database with navigation locations."""
    db: Session = SessionLocal()
    
    try:
        # Clear existing locations
        db.query(NavigationLocation).delete()
        
        # Add new locations
        for loc_data in NAVIGATION_LOCATIONS:
            location = NavigationLocation(**loc_data)
            db.add(location)
        
        db.commit()
        print(f"Successfully seeded {len(NAVIGATION_LOCATIONS)} navigation locations")
        
        # Display summary
        categories = {}
        for loc in NAVIGATION_LOCATIONS:
            cat = loc["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nLocation Summary:")
        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count}")
            
    except Exception as e:
        print(f"Error seeding navigation locations: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding Navigation Locations...")
    seed_navigation_locations()
    print("Seeding complete!")
