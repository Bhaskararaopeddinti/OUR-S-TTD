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

IMPORTANT: Format your response in this exact style:

Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• [Point 1 with key information]
• [Point 2 with key information]
• [Point 3 with key information]

Choose a quick question below or type your message!

Keep responses concise and helpful. If you don't have specific information, suggest contacting TTD helpline 155257.
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
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Sarva Darshan (Free): Current estimated wait time is about 2 hours 15 minutes
• Best time to join: Early afternoon (12:00 PM - 3:00 PM) usually has less crowd
• Special Entry Darshan: ₹300 ticket with shorter queue (subject to availability)
• Divya Darshan: Free footpath darshan via Alipiri or Srivari Mettu (requires trekking)

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("phone", "mobile")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Mobile phones are strictly prohibited inside the temple premises
• Deposit locations: Opposite VQC I & II, PAC-3, PAC-5 (Venkatadri Nilayam)
• Collection points: Near Sarva/Special Entry darshan lines
• Important: Retain your receipt token for collection
• Smart watches and electronic luggage must also be deposited

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("restroom", "toilet", "washroom")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Restrooms available: PAC I–V, VQC I & II, Kalyanakatta
• Additional locations: Jala Prasadam RO kiosks on temple ring road
• 350+ permanent toilet blocks with 24/7 sanitation cycles
• Free purified drinking water points available at all locations
• Milk points operate continuously for pilgrims

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("food", "annaprasadam")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Main Annaprasadam Complex: Matrusri Tarigonda Vengamamba Annaprasada Complex (MTVAC)
• Additional serving points: VQC compartments, PAC II, Rambagicha Bus Stand, CRO
• Free meals served to 55,000–65,000+ pilgrims daily
• Waiting compartments receive milk and refreshments every 3 hours
• Confirm nearest open counter with TTD volunteers

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("medical", "hospital", "emergency")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Main hospital: Aswini Hospital near Seshadri Nagar, Tirumala
• Emergency aid stations: Available on Alipiri and Srivari Mettu footpaths
• 24/7 emergency care, trauma response, and ambulance coordination
• TTD Emergency Helpline: 155257 (available 24/7)
• Medical centers located near temple, bus stand, and PAC complexes

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("laddu", "prasadam")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Main Laddu Complex: Located on West/East Mada Street
• Additional counters: VQC exit, MBC smart kiosks, standard laddu stalls
• Service: Available 24/7 during peak seasons
• One free laddu per darshan token included
• Additional laddus can be purchased at the counter (subject to limits)

Choose a quick question below or type your message!"""
    
    if any(x in query for x in ("wheelchair", "assistance", "elderly")):
        return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Here is your answer:

• Free wheelchair assistance available for senior citizens and differently-abled devotees
• Request locations: Medical centers, temple help desks, and PAC complexes
• Special queues available for wheelchair-assisted pilgrims
• Battery vehicle assistance available for elderly pilgrims
• Contact volunteers at help desks for immediate assistance

Choose a quick question below or type your message!"""
    
    return """Namaste! 🙏 Welcome to TTD AI Assistant.

I provide detailed point-wise answers for any question. Click on common questions below or type anything:

• Darshan & Sevas: Sarva Darshan (Free), Special Entry (₹300), Divya Darshan
• Live Queue: Real-time crowd condition, wait times, and recommended slots
• Pilgrim Amenities: Free Annaprasadam, PAC accommodation, Laddu prasadam
• Transit & Rules: 24/7 Ghat buses, trekking footpaths, and mandatory dress code

Choose a quick question below or type your message!"""
