import os
from typing import Optional
import google.generativeai as genai

# Configure Gemini API
def get_gemini_model():
    """Get configured Gemini model instance."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return None

def pilgrim_reply_gemini(message: str, language: str = "English") -> str:
    """Get AI-powered response using Gemini API for pilgrim assistance."""
    model = get_gemini_model()
    
    if not model:
        print("Using fallback responses (Gemini API not configured)")
        # Fallback to rule-based responses if API key not configured
        return pilgrim_reply_fallback(message, language)
    
    try:
        # Create context-aware prompt for TTD pilgrim assistance
        context = f"""
You are a helpful AI assistant for Tirumala Tirupati Devasthanams (TTD) pilgrims. 
Provide accurate, helpful information about:
- Temple darshan timings and queue status
- Facilities (restrooms, food, medical, phone deposit, wheelchair assistance)
- Temple rules and dress code
- Navigation and nearby locations
- Emergency contacts and procedures

Current language preference: {language}

User message: {message}

Provide a concise, helpful response. If you don't have specific information, suggest contacting TTD helpline 155257.
"""
        
        response = model.generate_content(context)
        if response and response.text:
            return response.text.strip()
        else:
            print("Gemini returned empty response")
            return pilgrim_reply_fallback(message, language)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return pilgrim_reply_fallback(message, language)

def pilgrim_reply_fallback(message: str, language: str = "English") -> str:
    """Fallback rule-based responses when Gemini API is unavailable."""
    query = message.lower()
    
    if any(x in query for x in ("queue", "wait", "darshan")):
        return "Sarva Darshan is currently estimated at about 2 hours 15 minutes. The least busy window is usually early afternoon."
    if any(x in query for x in ("phone", "mobile")):
        return "Mobile phones are prohibited inside the temple. Deposit them at centres opposite VQC I and II, PAC-3, PAC-5, or near darshan lines. Confirm your collection point and retain the receipt token."
    if any(x in query for x in ("restroom", "toilet", "washroom")):
        return "Restrooms and drinking water are available across PAC I–V, VQC I and II, Kalyanakatta, and Jala Prasadam RO kiosks on the temple ring road."
    if any(x in query for x in ("food", "annaprasadam")):
        return "Annaprasadam is available at the Matrusri Tarigonda Vengamamba Annaprasada Complex, VQC compartments, PAC II, Rambagicha Bus Stand, and CRO. Please confirm the nearest open counter with a volunteer."
    if any(x in query for x in ("medical", "hospital", "emergency")):
        return "Medical facilities are available at Aswini Hospital near Seshadri Nagar. For emergencies, call TTD helpline 155257 (24/7)."
    if any(x in query for x in ("laddu", "prasadam")):
        return "Laddu counters are available at Main Laddu Complex on West/East Mada Street, VQC exit, and MBC smart kiosks. One free laddu per darshan token."
    if any(x in query for x in ("wheelchair", "assistance", "elderly")):
        return "Free wheelchair assistance is available for senior citizens and differently-abled devotees. Request at medical centers or temple help desks."
    
    return f"Namaste. I can help with queue status, temple etiquette, food, facilities, phone deposit, health support and navigation. What do you need? (Language: {language})"
