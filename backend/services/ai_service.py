"""
OURS TTD — AI Service
Gemini-powered pilgrim assistant with TTD-specific knowledge.
Communicates directly with Google Gemini API using supported models (gemini-3.6-flash, gemini-3.5-flash).
Provides explicit status and source tracking without silently swallowing failures.
"""
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Guarantee .env is loaded from project root regardless of CWD
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")
load_dotenv()

logger = logging.getLogger(__name__)

# Candidate models in order of preference
MODEL_CANDIDATES = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-flash-latest']

_genai_client = None
_genai_legacy_model = None


def _init_gemini() -> bool:
    """Initialise Gemini client or legacy model lazily."""
    global _genai_client, _genai_legacy_model
    if _genai_client is not None or _genai_legacy_model is not None:
        return True

    # Re-trigger load_dotenv in case environment was updated at runtime
    load_dotenv(ROOT / ".env")
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your-gemini-api-key-here":
        logger.warning("GEMINI_API_KEY not configured or using placeholder. Using fallback responses.")
        return False

    # Try modern google.genai SDK first
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        _genai_client = client
        logger.info("Gemini initialized successfully with google.genai Client")
        return True
    except Exception as e:
        logger.debug("google.genai Client init attempt failed: %s", e)

    # Fallback to google.generativeai SDK (legacy)
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        
        # Try different model names for legacy SDK
        legacy_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-flash']
        for model_name in legacy_models:
            try:
                m = legacy_genai.GenerativeModel(model_name)
                _genai_legacy_model = m
                logger.info("Gemini initialized successfully with google.generativeai model: %s", model_name)
                return True
            except Exception as ex:
                logger.debug("Legacy model %s init failed: %s", model_name, ex)
                continue
    except Exception as e:
        logger.error("Failed to initialize legacy google.generativeai: %s", e)

    return False


SYSTEM_PROMPT = """You are the AI Smart Pilgrim Assistant for Tirumala Tirupati (OURS TTD).
Your objective: Provide direct, short, accurate, point-wise, and easily understandable answers.

STRICT RESPONSE RULES:
1. Format every answer as short, clean bullet points (* or -) with bold key terms.
2. Keep replies concise and directly relevant to the user's specific question.
3. Do NOT include long historical introductions or essays about TTD unless explicitly requested.
4. NEVER mention API keys, GEMINI_API_KEY, .env, backend configurations, developer details, debug messages, or "basic guidance mode".
5. For Queue questions: Provide Current crowd level, Waiting condition, Recommendation, and Better time slot.
6. For Darshan/Preparation: Provide essential checklist items (Valid booking, Original ID proof, Dress code, Prohibited items, Medicines).
7. If exact live data is unavailable, give clear point-wise guidance based on standard TTD procedures.
"""


def _build_db_context(message: str, db: Optional[Any] = None) -> str:
    """Retrieve relevant application database facts to attach as context for Gemini."""
    context_parts = []
    msg_lower = message.lower()

    # Queue status context — prefer live admin-entered data over AI prediction
    if any(k in msg_lower for k in ("queue", "wait", "crowd", "darshan line", "density", "line", "pilgrim")):
        try:
            from datetime import date as dt_date
            from backend.models import PilgrimFlowData
            from sqlalchemy import desc
            if db:
                today = dt_date.today().strftime("%Y-%m-%d")
                latest_flow = (
                    db.query(PilgrimFlowData)
                    .filter(PilgrimFlowData.date == today)
                    .order_by(desc(PilgrimFlowData.start_time))
                    .first()
                )
                if latest_flow:
                    context_parts.append(
                        f"[SYSTEM CONTEXT - LIVE ADMIN QUEUE DATA]: "
                        f"Current Estimated Crowd = {latest_flow.estimated_crowd:,} pilgrims, "
                        f"Queue Status = {latest_flow.queue_status}, "
                        f"Incoming = {latest_flow.incoming_pilgrims}, "
                        f"Outgoing = {latest_flow.outgoing_pilgrims}, "
                        f"Net change = {latest_flow.net_pilgrims:+d}, "
                        f"Festival day = {'YES' if latest_flow.festival else 'NO'}, "
                        f"Time Slot = {latest_flow.start_time}–{latest_flow.end_time}."
                    )
                else:
                    from backend.services.ttd_official import public_status
                    from backend.services.queue_prediction import predict_queue_status
                    status = public_status()
                    pred = predict_queue_status(status.get("wait_minutes", 120), status.get("crowd_density", "Moderate"))
                    context_parts.append(
                        f"[SYSTEM CONTEXT - QUEUE ESTIMATE]: "
                        f"Current wait ≈ {status.get('wait_minutes')} mins, "
                        f"Crowd density = {status.get('crowd_density')}. "
                        f"Trend: {pred.get('trend')} — {pred.get('recommendation')}."
                    )
        except Exception as e:
            logger.debug("Could not fetch queue context: %s", e)

    # Transport context
    if any(k in msg_lower for k in ("bus", "transport", "route", "reach", "tirupati", "tirumala", "fare", "shuttle", "alipiri", "mettu", "tour")):
        try:
            from backend.models import TransportRoute
            if db:
                routes = db.query(TransportRoute).all()
                if routes:
                    r_lines = []
                    for r in routes[:6]:
                        r_lines.append(
                            f"- {r.route_name} ({r.vehicle_type}, Operator: {r.operator}, Fare: {r.fare}, Hours: {r.operating_hours})"
                        )
                    context_parts.append(f"[SYSTEM CONTEXT - VERIFIED TTD TRANSPORT]:\n" + "\n".join(r_lines))
        except Exception as e:
            logger.debug("Could not fetch transport context: %s", e)

    # Facilities context
    if any(k in msg_lower for k in ("medical", "hospital", "doctor", "annaprasadam", "food", "eat", "restroom", "toilet", "laddu", "phone", "deposit", "parking")):
        try:
            from backend.services.facilities_data import FACILITIES
            relevant = [f"{f['name']} ({f['kind']})" for f in FACILITIES[:5]]
            context_parts.append(f"[SYSTEM CONTEXT - TTD FACILITIES]: {', '.join(relevant)}")
        except Exception as e:
            logger.debug("Could not fetch facilities context: %s", e)

    return "\n".join(context_parts)


def pilgrim_reply(
    message: str,
    language: str = "English",
    history: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Generate a concise point-wise reply to a pilgrim's question using Gemini or fallback logic.
    Never leaks debug information, API keys, or technical errors.
    """
    logger.info("CHAT REQUEST RECEIVED: language=%s, msg_len=%d", language, len(message))

    # Try Gemini first
    if _init_gemini():
        logger.info("GEMINI REQUEST STARTED")

        db_context = _build_db_context(message, db)
        lang_instruction = f"\nPlease respond in {language}." if language and language != "English" else ""

        prompt_parts = [SYSTEM_PROMPT]
        if db_context:
            prompt_parts.append(db_context)
        if lang_instruction:
            prompt_parts.append(lang_instruction)
        prompt_parts.append(f"\nPilgrim's Question: {message}")

        full_prompt = "\n\n".join(prompt_parts)

        try:
            reply_text = _generate_with_gemini(full_prompt, history)
            if reply_text and len(reply_text.strip()) > 0:
                logger.info("GEMINI RESPONSE SUCCESS")
                return {
                    "reply": reply_text.strip(),
                    "language": language,
                    "source": "gemini",
                    "ai_available": True
                }
            else:
                logger.error("GEMINI REQUEST FAILED: Empty response from model.")
        except Exception as e:
            safe_error = str(e).split("key=")[0].split("API_KEY=")[0]
            logger.error("GEMINI REQUEST FAILED: %s", safe_error)

    # Fallback to direct, rule-based point-wise responses if Gemini is unavailable
    logger.info("Using clean rule-based point-wise fallback response")
    fallback_reply = _generate_fallback_response(message, db)

    return {
        "reply": fallback_reply,
        "language": language,
        "source": "fallback",
        "ai_available": False
    }


def _generate_fallback_response(message: str, db: Optional[Any] = None) -> str:
    """Generate a clean, point-wise fallback response without exposing configuration details."""
    msg_lower = message.lower()

    # Queue-related queries
    if any(k in msg_lower for k in ("queue", "wait", "crowd", "darshan line", "density", "line", "join")):
        try:
            from datetime import date as dt_date
            from backend.models import PilgrimFlowData
            from sqlalchemy import desc
            if db:
                today = dt_date.today().strftime("%Y-%m-%d")
                latest_flow = (
                    db.query(PilgrimFlowData)
                    .filter(PilgrimFlowData.date == today)
                    .order_by(desc(PilgrimFlowData.start_time))
                    .first()
                )
                if latest_flow:
                    status = latest_flow.queue_status or "MODERATE"
                    crowd = latest_flow.estimated_crowd
                    rec = "Avoid joining now" if status in ("HIGH", "VERY HIGH", "CRITICAL") else "Good time to join"
                    better = "Early morning (2:30 AM – 6:00 AM) or after 9:00 PM" if status in ("HIGH", "VERY HIGH", "CRITICAL") else "Current slot is suitable"
                    wait_desc = "Long" if status in ("HIGH", "VERY HIGH", "CRITICAL") else "Moderate" if status == "MODERATE" else "Minimal"

                    return (
                        f"* Current crowd: **{status.title()}** ({crowd:,} devotees)\n"
                        f"* Expected waiting: **{wait_desc}**\n"
                        f"* Recommendation: **{rec}**\n"
                        f"* Better time: **{better}**\n"
                        f"* Active slot: **{latest_flow.start_time} – {latest_flow.end_time}**"
                    )
        except Exception as e:
            logger.debug("Could not fetch queue context for fallback: %s", e)

        return (
            "* Current crowd: **Moderate**\n"
            "* Expected waiting: **2 – 3 Hours**\n"
            "* Recommendation: **Consider joining during off-peak hours**\n"
            "* Better time: **Early morning (2:30 AM – 6:00 AM) or after 8:00 PM**\n"
            "* Status: **Check the Darshan Queue page for live updates**"
        )

    # What to carry / Darshan preparation
    if any(k in msg_lower for k in ("carry", "bring", "items", "documents", "id", "what to take", "checklist")):
        return (
            "* **Valid Darshan/booking details** (printed copy or mobile confirmation)\n"
            "* **Required ID proof** (Original Aadhaar card or matching government ID)\n"
            "* **Prescribed traditional dress code** (Dhoti/Kurta for men, Saree/Chudidar for women)\n"
            "* **Avoid prohibited items** (Mobile phones, electronic gadgets, leather items)\n"
            "* **Keep essential medicines** and light water bottle if required"
        )

    # Dress code / Guidelines
    if any(k in msg_lower for k in ("dress", "clothes", "wear", "attire", "rules", "guidelines")):
        return (
            "* **Men:** Dhoti and Kurta or Shirt / Pyjama with Kurta (no Western wear/jeans/shorts)\n"
            "* **Women:** Saree, Half-Saree, or Chudidar with Dupatta\n"
            "* **Children:** Traditional modest clothing\n"
            "* **Footwear:** Must be deposited at free footwear counters outside\n"
            "* **Electronics:** Deposit phones at free Phone Deposit Counters before entering"
        )

    # Food & Annaprasadam
    if any(k in msg_lower for k in ("food", "annaprasadam", "eat", "meal", "breakfast", "dinner", "lunch", "prasadam")):
        return (
            "* **MTVAC Annaprasada Complex:** Free, hygienic vegetarian meals (9:00 AM – 11:00 PM daily)\n"
            "* **Queue Refreshments:** Free milk, buttermilk, tea, and food packets in VQC compartments\n"
            "* **TTD Canteens:** Subsidized quality food at PAC-1, PAC-2, and Rambagicha\n"
            "* **Free Laddu:** Available at Laddu Distribution Complex upon Darshan completion"
        )

    # Transport / Travel / Bus
    if any(k in msg_lower for k in ("bus", "transport", "route", "reach", "tirupati", "tirumala", "fare", "shuttle", "alipiri", "mettu", "train")):
        return (
            "* **Free Dharma Ratham Buses:** Operate continuously within Tirumala covering all PACs and temples\n"
            "* **Ghat Road APSRTC Buses:** 24/7 frequent bus service from Tirupati Central Bus Stand & Railway Station to Tirumala\n"
            "* **Alipiri Footpath:** 3,550 steps (~3.5 to 4 hours walking climb)\n"
            "* **Srivari Mettu Footpath:** 2,100 steps (~2 to 2.5 hours walking climb)\n"
            "* **Toll & Ghat Road Timings:** 3:00 AM to 12:00 Midnight"
        )

    # Medical & Emergency
    if any(k in msg_lower for k in ("medical", "hospital", "doctor", "emergency", "health", "first aid", "sos", "ambulance")):
        return (
            "* **Aswini Hospital:** 24/7 fully equipped hospital near Seshadri Nagar, Tirumala\n"
            "* **First Aid Posts:** Located at VQC compartments, Rambagicha, and footpath routes\n"
            "* **TTD 24/7 Helpline:** Dial **155257**\n"
            "* **Emergency Ambulance:** Available immediately via Emergency SOS in this app"
        )

    # Accommodation
    if any(k in msg_lower for k in ("accommodation", "room", "stay", "hotel", "lodge", "cottage", "pac")):
        return (
            "* **Free Pilgrim Accommodation:** Available at PAC-1, PAC-2, PAC-3, and PAC-4 complexes\n"
            "* **Locker Facilities:** Free lockers available in all PAC complexes for luggage security\n"
            "* **Advance Bookings:** Subject to TTD quota availability\n"
            "* **Current Allocation:** Visit Central Reception Office (CRO) near Rambagicha"
        )

    # Famous places / Attractions
    if any(k in msg_lower for k in ("famous", "place", "sightseeing", "attraction", "visit", "spot", "temples")):
        return (
            "* **Sri Venkateswara Swamy Temple:** Main sanctum atop Tirumala hills\n"
            "* **Sri Bedi Anjaneyaswami Temple:** Opposite main temple entrance\n"
            "* **Silathoranam:** Ancient natural geological rock arch\n"
            "* **Akasa Ganga & Papavanasam:** Holy waterfalls and sacred bathing ghats\n"
            "* **Sri Padmavathi Ammavari Temple:** Located at Tiruchanur (Tirupati base)\n"
            "* **Kapila Theertham:** Ancient Shiva shrine at the foot of Alipiri"
        )

    # General / Welcome fallback
    return (
        "* **Darshan Queue Status:** View live crowd updates and optimal joining times\n"
        "* **Temple Guidelines:** Check dress code, ID requirements, and prohibited items\n"
        "* **Food & Transport:** Find free Annaprasadam and 24/7 bus routes\n"
        "* **Helpline:** Call **155257** for 24/7 official TTD assistance"
    )


def _generate_with_gemini(full_prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """Send prompt to Gemini model using available client with timeout safety."""
    global _genai_client, _genai_legacy_model
    import concurrent.futures

    formatted_prompt = full_prompt
    if history and isinstance(history, list):
        recent_history = history[-6:]
        history_lines = []
        for h in recent_history:
            if isinstance(h, dict):
                role = h.get('role', h.get('type', 'user')).capitalize()
                content = h.get('content', h.get('message', ''))
                if content and content != "Thinking...":
                    history_lines.append(f"{role}: {content}")
        if history_lines:
            formatted_prompt = f"RECENT CONVERSATION HISTORY:\n" + "\n".join(history_lines) + f"\n\n{full_prompt}"

    def _call_model():
        # Modern google.genai Client
        if _genai_client is not None:
            for model_name in MODEL_CANDIDATES:
                try:
                    response = _genai_client.models.generate_content(
                        model=model_name,
                        contents=formatted_prompt
                    )
                    if response and hasattr(response, 'text') and response.text:
                        return response.text.strip()
                    elif response and hasattr(response, 'candidates') and response.candidates:
                        if response.candidates[0].content and hasattr(response.candidates[0].content, 'parts'):
                            parts = response.candidates[0].content.parts
                            if parts and hasattr(parts[0], 'text'):
                                return parts[0].text.strip()
                except Exception as e:
                    logger.debug("Client generate_content with %s failed: %s", model_name, e)
                    continue

        # Fallback to legacy google.generativeai
        if _genai_legacy_model is not None:
            try:
                response = _genai_legacy_model.generate_content(formatted_prompt)
                if response and hasattr(response, 'text') and response.text:
                    return response.text.strip()
                elif response and hasattr(response, 'candidates') and response.candidates:
                    if response.candidates[0].content and hasattr(response.candidates[0].content, 'parts'):
                        parts = response.candidates[0].content.parts
                        if parts and hasattr(parts[0], 'text'):
                            return parts[0].text.strip()
            except Exception as e:
                logger.debug("Legacy model generate_content failed: %s", e)

        return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_model)
            return future.result(timeout=12.0)
    except Exception as ex:
        logger.debug("Gemini model call exceeded timeout or encountered error: %s", ex)
        return None
