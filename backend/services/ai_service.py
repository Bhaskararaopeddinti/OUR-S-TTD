"""
OURS TTD — AI Service
Gemini-powered pilgrim assistant with TTD-specific knowledge.
Falls back to keyword matching when no API key is configured.
Integrates with all app features: Queue Intelligence, Navigation, Health, Notifications.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Gemini configuration ──
_model = None

def _get_model():
    """Lazy-init the Gemini model; returns None if no API key."""
    global _model
    if _model is not None:
        return _model
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.info("GEMINI_API_KEY not set — using keyword fallback for chat.")
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        _model = client
        logger.info("Gemini AI client initialised successfully.")
        return _model
    except Exception as e:
        logger.warning("Failed to initialise Gemini: %s — falling back to keywords.", e)
        return None


SYSTEM_PROMPT = """You are OURS TTD Smart Pilgrim Assistant — a compassionate, knowledgeable guide for devotees visiting Lord Venkateswara Temple in Tirumala, India.

CORE KNOWLEDGE:
- The temple is officially managed by Tirumala Tirupati Devasthanams (TTD).
- Darshan types: Sarva Darshan (free, long queue), Special Entry Darshan (SED, ₹300 ticket), VIP Break Darshan, Divya Darshan (for senior citizens/differently abled).
- Temple opening hours: Generally 2:30 AM to 1:00 AM next day (nearly 24 hours). Brief closing for rituals.
- Queue Complex: Vaikuntam Queue Complex I & II (VQC I, VQC II) — the main waiting areas.
- Pilgrim Accommodation Complexes: PAC-1 through PAC-5. Booking via TTD website.
- Dress code: Traditional and modest attire required. Men — dhoti/panche or formal trousers with shirt. Women — saree, churidar, or salwar kameez. Shorts, skirts above knee, sleeveless tops are not permitted.
- Mobile phones: PROHIBITED inside the temple. Deposit at designated centres near VQC I, VQC II, PAC-3, PAC-5 (Venkatadri Nilayam), and near darshan lines. Retain your receipt token.
- Laddus: One free laddu per darshan token. Additional laddus can be purchased at counters. Main Laddu Complex on West/East Mada Street.
- Annaprasadam (free food): Matrusri Tarigonda Vengamamba Annaprasada Complex (MTVAC) serves ~65,000+ meals daily. Also at VQC compartments, PAC II, Rambagicha Bus Stand.
- Medical: Aswini Hospital near Seshadri Nagar. TTD Helpline: 155257. Emergency aid stations on Alipiri and Srivari Mettu footpaths.
- Transport: Buses from Tirupati to Tirumala. Two walking paths: Alipiri (3,550 steps, ~3-4 hours), Srivari Mettu (2,100 steps, ~2 hours).
- Facilities: Restrooms at PAC I-V, VQC I & II, Kalyanakatta. Drinking water points throughout.
- Hair offering (tonsure): Kalyanakatta complex, free of charge.
- Cloak rooms and luggage deposit available near bus stand and VQC.
- Hundi (donation box) inside the sanctum.
- Brahmotsavam: Annual 9-day festival in September/October.

APP FEATURES INTEGRATION:
- AI Queue Intelligence: I can provide predictive queue analysis, crowd trends, best times to join, and AI advice based on time, day, and festivals.
- Smart Navigation: I can help find nearest facilities (restrooms, food, medical, laddu counters, etc.) with crowd-aware routing and walking time estimates.
- Health & Emergency Companion: I can help with health reminders, nearest medical centers, emergency contacts, and SOS assistance.
- Smart Notifications: I can inform about queue changes, festivals, weather alerts, and temple announcements.

LOCATION QUERIES:
When users ask about locations (e.g., "where is the nearest restroom", "how to get to laddu counter", "find medical center"), guide them to use the Smart Navigation feature in the app which provides:
- Interactive map with all facility locations
- Real-time distance and walking time estimates
- Crowd-aware routing recommendations
- Direct navigation to any facility

For specific location queries, mention key locations:
- Sri Venkateswara Temple: Main temple complex
- VQC I & II: Queue complexes
- MTVAC: Annaprasadam complex
- Aswini Hospital: Medical center near Seshadri Nagar
- Laddu Counters: West/East Mada Street
- Phone Deposit: VQC I, VQC II, PAC-3, PAC-5
- Restrooms: PAC I-V, VQC I & II, Kalyanakatta

BEHAVIOR:
1. Be warm, respectful, and spiritually supportive. Start responses with appropriate greetings if the user seems to be greeting you.
2. Always give factual, verified information from the knowledge above.
3. When unsure, say "Please verify with TTD officials or visit tirumala.org for the most current information."
4. Never fabricate queue times, booking slots, or operational data.
5. For booking inquiries, mention that official booking is available through the TTD website (ttdevasthanams.ap.gov.in).
6. Keep responses concise but complete — ideal for mobile reading.
7. If the user asks in a specific language, respond in that same language.
8. For emergencies, always advise calling TTD Helpline 155257 or visiting the nearest help desk.
9. For location queries, direct users to the Smart Navigation feature for detailed maps and directions.
10. For queue queries, mention the AI Queue Intelligence feature for predictive analysis.
11. For health queries, mention the Health & Emergency Companion feature.
12. Respond in the language requested by the user.
"""


def pilgrim_reply(message: str, language: str = "English") -> str:
    """Generate a reply to a pilgrim's question. Uses Gemini if available, else keywords."""
    client = _get_model()
    if client:
        return _gemini_reply(client, message, language)
    return _keyword_reply(message)


def _gemini_reply(client, message: str, language: str) -> str:
    """Call Gemini API for an intelligent response."""
    try:
        lang_instruction = f"\n\nRespond in {language}." if language and language != "English" else ""
        prompt = SYSTEM_PROMPT + lang_instruction + f"\n\nPilgrim's question: {message}"

        if hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = getattr(response, 'text', None) or getattr(response, 'output_text', None) or ""
        elif hasattr(client, 'text_generation') and hasattr(client.text_generation, 'generate'):
            response = client.text_generation.generate(model="gemini-2.0-flash", input=prompt)
            text = getattr(response, 'text', None) or getattr(response, 'output_text', None) or ""
        else:
            raise AttributeError("Unsupported Gemini client interface")

        text = text.strip() if isinstance(text, str) else ""
        if text:
            return text
        return _keyword_reply(message)
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return _keyword_reply(message)


def _keyword_reply(message: str) -> str:
    """Fallback keyword-based reply when Gemini is unavailable."""
    query = message.lower()

    # Location queries - direct to Smart Navigation
    if any(x in query for x in ("where is", "location", "find", "nearest", "how to get to", "direction", "navigate")):
        if any(x in query for x in ("restroom", "toilet", "washroom", "bathroom")):
            return ("For the nearest restrooms, please use the Smart Navigation feature in the app. "
                    "Restrooms are available at PAC I-V, VQC I & II, and Kalyanakatta. "
                    "The navigation map will show you the closest one with walking directions.")
        if any(x in query for x in ("food", "annaprasadam", "meal", "eat")):
            return ("Use the Smart Navigation feature to find the nearest Annaprasadam center. "
                    "MTVAC, VQC compartments, PAC II, and Rambagicha Bus Stand serve free meals. "
                    "The map will show distance and walking time.")
        if any(x in query for x in ("medical", "hospital", "doctor")):
            return ("For medical assistance, use Smart Navigation to find the nearest medical center. "
                    "Aswini Hospital near Seshadri Nagar provides 24/7 care. "
                    "Emergency aid stations are on Alipiri and Srivari Mettu footpaths. "
                    "TTD Helpline: 155257.")
        if any(x in query for x in ("laddu", "prasad", "prasadam")):
            return ("Use Smart Navigation to find the nearest laddu counter. "
                    "Main Laddu Complex is on West/East Mada Street. "
                    "The map will guide you there with crowd-aware routing.")
        if any(x in query for x in ("phone", "mobile", "deposit")):
            return ("Mobile phones are prohibited inside the temple. "
                    "Use Smart Navigation to find the nearest deposit centre at VQC I & II, PAC-3, or PAC-5. "
                    "Always retain your receipt token for collection.")
        if any(x in query for x in ("parking", "car", "vehicle")):
            return ("Use Smart Navigation to find parking areas. "
                    "Parking is available at Alipiri and Tirumala. "
                    "The map will show you the nearest parking location.")
        return ("For location queries, please use the Smart Navigation feature in the app. "
                "It provides an interactive map with all facility locations, real-time distance, "
                "walking time estimates, and crowd-aware routing to any facility.")

    # Queue queries - mention AI Queue Intelligence
    if any(x in query for x in ("queue", "wait", "darshan", "line")):
        return ("Check the AI Queue Intelligence feature in the app for predictive queue analysis. "
                "It provides crowd trends, best times to join, and AI advice based on time, day, and festivals. "
                "Historically, early mornings (2:30 AM–5 AM) and post-lunch (1 PM–3 PM) tend to be less crowded.")

    # Health queries - mention Health & Emergency Companion
    if any(x in query for x in ("health", "emergency", "sos", "medical help")):
        return ("Use the Health & Emergency Companion feature for health support. "
                "It provides health reminders, nearest medical centers, emergency contacts, and SOS assistance. "
                "For immediate help, call TTD Helpline: 155257.")

    # Other queries
    if any(x in query for x in ("dress", "attire", "wear", "cloth")):
        return ("Traditional, modest attire is required. Men: dhoti or formal trousers with shirt. "
                "Women: saree, churidar, or salwar kameez. Shorts, sleeveless tops, and short skirts are not permitted.")

    if any(x in query for x in ("book", "ticket", "slot", "seva", "accommodation", "room", "stay")):
        return ("Official bookings for darshan, accommodation, and sevas are available on the TTD website: "
                "ttdevasthanams.ap.gov.in. This app will integrate booking when TTD provides API access.")

    if any(x in query for x in ("hair", "tonsure", "kalyanakatta", "mundan")):
        return ("Hair offering (tonsure) is done at the Kalyanakatta complex, free of charge. "
                "Use Smart Navigation to find its location.")

    if any(x in query for x in ("walk", "footpath", "alipiri", "srivari mettu", "steps")):
        return ("Two walking paths: Alipiri footpath (3,550 steps, ~3-4 hours) and "
                "Srivari Mettu (2,100 steps, ~2 hours). Both have rest stops, water points, and emergency aid. "
                "Use Smart Navigation for detailed route information.")

    if any(x in query for x in ("hundi", "donat", "offer")):
        return ("The Hundi (donation box) is inside the sanctum. You can also make donations online "
                "through the TTD website. All donations receive official receipts.")

    if any(x in query for x in ("festival", "brahmotsavam", "utsav")):
        return ("Brahmotsavam is the annual 9-day festival in September/October, featuring grand processions "
                "and special rituals. Other major festivals include Vaikunta Ekadasi and Rathasapthami. "
                "Check Smart Notifications for festival alerts.")

    if any(x in query for x in ("wheelchair", "senior", "elderly", "disabled", "divya")):
        return ("Free wheelchair assistance is available at medical centres and help desks. "
                "Senior citizens (65+) and differently abled devotees qualify for Divya Darshan "
                "with shorter wait times. Use Smart Navigation to find help desks.")

    if any(x in query for x in ("hello", "hi", "namaste", "namaskar")):
        return ("Namaste! 🙏 Welcome to OURS TTD. I can help with queue status, temple facilities, "
                "navigation, health support, and more. Use the Smart Navigation feature for location queries "
                "and AI Queue Intelligence for queue predictions. How can I assist you?")

    return ("Namaste! I can help with queue status (check AI Queue Intelligence), "
            "location queries (use Smart Navigation), health support (Health & Emergency Companion), "
            "temple etiquette, food, facilities, phone deposit, dress code, and booking info. "
            "What would you like to know?")
