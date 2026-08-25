"""
Test script for transport fallback system
"""
import requests
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_transport_search(from_loc, to_loc):
    """Test transport search with fallback"""
    params = {
        "from_location": from_loc,
        "to_location": to_loc
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/transport/search", params=params)
        data = response.json()
        
        print(f"\n{'='*60}")
        print(f"Test: {from_loc} -> {to_loc}")
        print(f"{'='*60}")
        print(f"Status: {data.get('status')}")
        print(f"Count: {data.get('count')}")
        
        if data.get('status') == 'error':
            print(f"Error Message: {data.get('message')}")
        elif data.get('routes'):
            for route in data['routes']:
                print(f"\nRoute: {route.get('route_name')}")
                print(f"  Vehicle: {route.get('vehicle_type')}")
                print(f"  From: {route.get('source_location')}")
                print(f"  To: {route.get('destination_location')}")
                print(f"  Duration: {route.get('estimated_duration')}")
                print(f"  Fare: {route.get('fare')}")
                print(f"  Is Fallback: {route.get('is_fallback', False)}")
                print(f"  Data Status: {route.get('data_status')}")
        
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing Transport Fallback System")
    print("="*60)
    
    # Test cases as specified in requirements
    test_cases = [
        ("Tirumala", "Tirupati"),
        ("Tirupati", "Tirumala"),
        ("Tirumala", "Kapila Theertham"),
        ("Kapila Theertham", "Tirumala"),
        ("Alipiri", "Tirumala"),
        ("Tirumala", "Alipiri"),
        ("Tirupati Railway Station", "Tirumala"),
        ("Tirupati", "Tiruchanoor"),
        ("Tiruchanoor", "Tirupati"),
        ("Srinivasa Mangapuram", "Tirumala"),
        ("Hyderabad", "Tirumala"),  # Invalid outside-area location
    ]
    
    for from_loc, to_loc in test_cases:
        test_transport_search(from_loc, to_loc)
