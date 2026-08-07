"""
Seed script for TTD locations
Loads locations from ttd_locations.json and seeds the database
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import NavigationLocation

def seed_locations():
    """Seed the database with TTD locations from JSON file"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Created/verified database tables")
    
    # Load locations from JSON
    json_path = os.path.join(os.path.dirname(__file__), 'ttd_locations.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return False
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Clear existing locations
        db.query(NavigationLocation).delete()
        db.commit()
        print("Cleared existing locations")
        
        # Add new locations
        locations_data = data.get('locations', [])
        added_count = 0
        
        for loc_data in locations_data:
            location = NavigationLocation(
                id=loc_data['id'],
                name=loc_data['name'],
                category=loc_data['category'],
                description=loc_data.get('description', ''),
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude'],
                address=loc_data.get('address', ''),
                opening_hours='24/7',
                contact_number='',
                wheelchair_accessible=False
            )
            
            db.add(location)
            added_count += 1
        
        db.commit()
        print(f"Successfully seeded {added_count} locations")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding TTD locations...")
    success = seed_locations()
    
    if success:
        print("Database seeded successfully")
        sys.exit(0)
    else:
        print("Failed to seed database")
        sys.exit(1)
