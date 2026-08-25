"""
Test script for AI chat API endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_api():
    """Test the chat API endpoint"""
    print("Testing AI Chat API")
    print("="*60)
    
    test_message = "How can I reach Tirumala from Tirupati Railway Station?"
    
    payload = {
        "message": test_message,
        "language": "English",
        "history": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('ai_available'):
            print("\n[SUCCESS] AI chat is working!")
            print(f"Reply: {data.get('reply')}")
        else:
            print("\n[FAILURE] AI is not available")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat_api()
