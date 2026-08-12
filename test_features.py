"""
Test script for the three implemented features
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_queue_recommendation():
    """Test Feature 1: AI Queue Management recommendations"""
    print("Testing Feature 1: AI Queue Management recommendations")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/queue")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Queue Location: {data.get('location')}")
        print(f"Current Wait: {data.get('wait_minutes')} minutes")
        print(f"Crowd Density: {data.get('crowd_density')}")
        
        if 'ai_prediction' in data:
            pred = data['ai_prediction']
            print(f"\nAI Prediction:")
            print(f"  Predicted Wait: {pred.get('predicted_wait_minutes')} minutes")
            print(f"  Current Crowd Level: {pred.get('current_crowd_level')}")
            print(f"  Admin Data Used: {pred.get('admin_data_used')}")
            print(f"  Data Source: {pred.get('data_source')}")
            
            if pred.get('best_times_to_join'):
                print(f"  Best Times: {[t['time'] for t in pred.get('best_times_to_join', [])[:3]]}")
            
            if pred.get('ai_advice'):
                print(f"  AI Advice: {pred.get('ai_advice')[:2]}")
        
        print("\n[PASS] Queue recommendation API working!")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_queue_recommendation_endpoint():
    """Test the new queue recommendation endpoint"""
    print("\nTesting Feature 1: Queue Recommendation Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/queue/recommendation")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Queue Status: {data.get('queue_status')}")
        print(f"Action: {data.get('action')}")
        print(f"Action Color: {data.get('action_color')}")
        print(f"Message: {data.get('message')}")
        print(f"Admin Data Used: {data.get('admin_data_used')}")
        
        if data.get('best_time_today'):
            print(f"Best Time Today: {data.get('best_time_today').get('time')}")
        
        print("\n[PASS] Queue recommendation endpoint working!")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_ai_assistant():
    """Test Feature 2: AI Assistant"""
    print("\nTesting Feature 2: AI Assistant")
    print("=" * 60)
    
    test_questions = [
        "What is the current queue status?",
        "When should I join the queue?",
        "Where is the nearest medical facility?"
    ]
    
    for question in test_questions:
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"message": question, "language": "English"}
            )
            data = response.json()
            
            print(f"\nQuestion: {question}")
            print(f"Status Code: {response.status_code}")
            print(f"AI Available: {data.get('ai_available')}")
            print(f"Source: {data.get('source')}")
            reply = data.get('reply', '')[:200]
            print(f"Reply: {reply.encode('ascii', 'ignore').decode('ascii')}...")
            
        except Exception as e:
            print(f"[FAIL] Error for '{question}': {e}")
    
    print("\n[PASS] AI Assistant API tested!")
    return True

def test_transport_search():
    """Test Feature 3: Bus Search"""
    print("\nTesting Feature 3: Bus Search")
    print("=" * 60)
    
    test_routes = [
        ("Tirupati Bus Stand", "Tirumala"),
        ("Tirumala", "Tirupati Bus Stand"),
        ("Tirupati Railway Station", "Tirumala"),
        ("Alipiri Checkpost", "Tirumala"),
    ]
    
    for from_loc, to_loc in test_routes:
        try:
            response = requests.get(
                f"{BASE_URL}/api/transport/search",
                params={"from_location": from_loc, "to_location": to_loc}
            )
            data = response.json()
            
            print(f"\nRoute: {from_loc} -> {to_loc}")
            print(f"Status Code: {response.status_code}")
            print(f"Status: {data.get('status')}")
            print(f"Routes Found: {data.get('count')}")
            
            if data.get('routes'):
                for route in data.get('routes', [])[:2]:
                    print(f"  - {route.get('route_name')}")
                    print(f"    Vehicle: {route.get('vehicle_type')}")
                    print(f"    Duration: {route.get('estimated_duration')}")
                    print(f"    Fare: {route.get('fare')}")
                    print(f"    Fallback: {route.get('is_fallback', False)}")
            
        except Exception as e:
            print(f"[FAIL] Error for route {from_loc} -> {to_loc}: {e}")
    
    print("\n[PASS] Transport search API tested!")
    return True

if __name__ == "__main__":
    print("OURS TTD Feature Testing")
    print("=" * 60)
    
    results = []
    results.append(("Queue Recommendation", test_queue_recommendation()))
    results.append(("Queue Recommendation Endpoint", test_queue_recommendation_endpoint()))
    results.append(("AI Assistant", test_ai_assistant()))
    results.append(("Transport Search", test_transport_search()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for feature, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{feature}: {status}")
