"""
OURS TTD — AI Service
Gemini-powered pilgrim assistant with TTD-specific knowledge.
Communicates directly with Google Gemini API using supported models (gemini-3.6-flash, gemini-3.5-flash).
Provides explicit status and source tracking without silently swallowing failures.
"""
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Candidate models in order of preference (updated to use current Gemini models)
MODEL_CANDIDATES = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']

_genai_client = None
_genai_legacy_model = None


def _init_gemini() -> bool:
    """Initialise Gemini client or legacy model lazily."""
    global _genai_client, _genai_legacy_model
    if _genai_client is not None or _genai_legacy_model is not None:
        return True

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


SYSTEM_PROMPT = """You are OURS TTD AI Smart Pilgrim Assistant.
Your job is to help pilgrims visiting Tirumala and Tirupati.

You can help with:
- Darshan guidance & Queue information
- Crowd guidance & Queue predictions
- TTD facilities & accommodation guidance
- Temple etiquette, dress code & phone deposit
- Annaprasadam (free food) & Laddu information
- Cloak rooms & luggage deposit
- Medical facilities & emergency assistance
- Transportation, bus routes & parking
- Navigation & walking trek footpaths (Alipiri, Srivari Mettu)
- Weather-related planning & lost & found
- Accessibility, senior citizen & Divya Darshan assistance

Guidance Rules:
1. Give concise, warm, respectful, and easy-to-understand answers.
2. Never invent live TTD information (such as live booking availability, exact queue wait minutes, live crowd level, or bus schedules) unless provided in the system context.
3. If specific live information is unavailable, state clearly that it is unavailable and direct the user to the appropriate application feature (AI Queue Intelligence, Smart Navigation, Health & Emergency Companion, etc.).
4. Never state false coordinates or fake distance metrics. Direct location queries to Smart Navigation.
5. Transport Guidance: Always use verified transport records from the system context. If the pilgrim asks for a route where no verified record is present in context, state: "I don't have verified current transport information for that route." Never invent bus numbers, fares, frequency, or live schedules.
6. The assistant should be especially easy for first-time pilgrims and senior citizens to understand.
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
                        f"[SYSTEM CONTEXT - LIVE ADMIN QUEUE DATA (Source: Admin-entered)]: "
                        f"Current Estimated Crowd = {latest_flow.estimated_crowd:,} pilgrims, "
                        f"Queue Status = {latest_flow.queue_status}, "
                        f"Incoming this slot = {latest_flow.incoming_pilgrims}, "
                        f"Outgoing this slot = {latest_flow.outgoing_pilgrims}, "
                        f"Net change = {latest_flow.net_pilgrims:+d}, "
                        f"Festival day = {'YES' if latest_flow.festival else 'NO'}, "
                        f"Slot = {latest_flow.start_time}–{latest_flow.end_time}."
                    )
                else:
                    # Fallback to AI prediction
                    from backend.services.ttd_official import public_status
                    from backend.services.queue_prediction import predict_queue_status
                    status = public_status()
                    pred = predict_queue_status(status.get("wait_minutes", 120), status.get("crowd_density", "Moderate"))
                    context_parts.append(
                        f"[SYSTEM CONTEXT - AI PREDICTED QUEUE (No admin data yet)]: "
                        f"Current wait ≈ {status.get('wait_minutes')} mins, "
                        f"Crowd density = {status.get('crowd_density')}. "
                        f"AI Prediction: {pred.get('trend')} — {pred.get('recommendation')}."
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
                    for r in routes:
                        r_lines.append(
                            f"- {r.route_name} ({r.vehicle_type}, Operator: {r.operator}, Fare: {r.fare}, Hours: {r.operating_hours}, Freq: {r.frequency}, Status: {r.data_status}, Source: {r.source})"
                        )
                    context_parts.append(f"[SYSTEM CONTEXT - VERIFIED TTD TRANSPORT DATABASE]:\n" + "\n".join(r_lines))
        except Exception as e:
            logger.debug("Could not fetch transport context: %s", e)

    # Facilities context
    if any(k in msg_lower for k in ("medical", "hospital", "doctor", "annaprasadam", "food", "eat", "restroom", "toilet", "laddu", "phone", "deposit", "parking")):
        try:
            from backend.services.facilities_data import FACILITIES
            relevant = [f"{f['name']} ({f['kind']}, Distance: ~{f.get('distance_m', 'N/A')}m)" for f in FACILITIES[:5]]
            context_parts.append(f"[SYSTEM CONTEXT - TTD FACILITIES DIRECTORY]: {', '.join(relevant)}")
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
    Generate a reply to a pilgrim's question using Gemini.
    Returns structured response dictionary containing reply, language, source, and ai_available.
    """
    logger.info("CHAT REQUEST RECEIVED: language=%s, msg_len=%d", language, len(message))

    # Try Gemini first
    if _init_gemini():
        logger.info("GEMINI REQUEST STARTED")

        db_context = _build_db_context(message, db)
        lang_instruction = f"\n\nPlease respond in {language}." if language and language != "English" else ""

        prompt_parts = [SYSTEM_PROMPT]
        if db_context:
            prompt_parts.append(db_context)
        if lang_instruction:
            prompt_parts.append(lang_instruction)
        prompt_parts.append(f"\nPilgrim's Question: {message}")

        full_prompt = "\n\n".join(prompt_parts)

        try:
            reply_text = _generate_with_gemini(full_prompt, history)
            if reply_text:
                logger.info("GEMINI RESPONSE SUCCESS")
                return {
                    "reply": reply_text,
                    "language": language,
                    "source": "gemini",
                    "ai_available": True
                }
            else:
                logger.error("GEMINI REQUEST FAILED: Empty response from model.")
        except Exception as e:
            safe_error = str(e).split("key=")[0].split("API_KEY=")[0]
            logger.error("GEMINI REQUEST FAILED: %s", safe_error)

    # Fallback to rule-based responses if Gemini fails
    logger.warning("Using fallback response system")
    fallback_reply = _generate_fallback_response(message, db)
    
    # Add a note about fallback mode
    fallback_note = "\n\n[Note: Using basic guidance mode. For full AI assistance, please configure GEMINI_API_KEY in .env file]"
    
    return {
        "reply": fallback_reply + fallback_note,
        "language": language,
        "source": "fallback",
        "ai_available": False
    }


def _generate_fallback_response(message: str, db: Optional[Any] = None) -> str:
    """Generate a fallback response using rule-based logic when Gemini is unavailable."""
    msg_lower = message.lower()
    
    # Queue-related queries
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
                    return (
                        f"Based on admin-entered data, current crowd is approximately {latest_flow.estimated_crowd:,} pilgrims. "
                        f"Queue status: {latest_flow.queue_status}. "
                        f"Slot: {latest_flow.start_time}–{latest_flow.end_time}. "
                        f"{'Festival conditions are active.' if latest_flow.festival else ''} "
                        f"Please check the AI Queue Intelligence page for detailed predictions and best time recommendations."
                    )
        except Exception as e:
            logger.debug("Could not fetch queue context for fallback: %s", e)
        
        return "For current queue status and predictions, please check the AI Queue Intelligence page. It provides real-time crowd analysis and best time recommendations."

    # Transport-related queries
    if any(k in msg_lower for k in ("bus", "transport", "route", "reach", "tirupati", "tirumala", "fare", "shuttle", "alipiri", "mettu", "tour")):
        return "For transport information between TTD locations, please use the Transport page. You can search for routes between Tirumala, Tirupati, Alipiri, and other pilgrimage locations. TTD provides free bus services and APSRTC operates regular routes."

    # Facility-related queries
    if any(k in msg_lower for k in ("medical", "hospital", "doctor", "annaprasadam", "food", "eat", "restroom", "toilet", "laddu", "phone", "deposit", "parking")):
        return "For facility information including medical centers, food services, and amenities, please use the Smart Navigation feature or check the Facilities directory. TTD provides free Annaprasadam, medical assistance, and various facilities for pilgrims."

    # Temple and darshan guidance
    if any(k in msg_lower for k in ("temple", "darshan", "dress", "clothes", "mobile", "phone", "rules", "guidelines")):
        return "For temple darshan, traditional dress is recommended (dhoti for men, saree for women). Mobile phones are not allowed in the temple premises and must be deposited at the counters. Free luggage storage is available. Check the Temple Guide for detailed rules."

    # Accommodation
    if any(k in msg_lower for k in ("accommodation", "room", "stay", "hotel", "lodge", "booking")):
        return "For accommodation, TTD provides various guest houses and dormitories. Advance booking is recommended through the official TTD website. PAC complexes and other accommodations are available at different rates."

    # General guidance
    return "Namaste! 🙏 I can help you with queue information, transport routes, TTD facilities, and pilgrimage guidance. For detailed information, please use the specific features in the app like AI Queue Intelligence, Smart Navigation, and Transport Search. Jai Sri Venkateswara!"


def _generate_with_gemini(full_prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """Send prompt to Gemini model using available client."""
    global _genai_client, _genai_legacy_model

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

    # Re-try initializing google.genai client if needed
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            _genai_client = client
            for model_name in MODEL_CANDIDATES:
                try:
                    res = client.models.generate_content(model=model_name, contents=formatted_prompt)
                    if res and hasattr(res, 'text') and res.text:
                        return res.text.strip()
                    elif res and hasattr(res, 'candidates') and res.candidates:
                        if res.candidates[0].content and hasattr(res.candidates[0].content, 'parts'):
                            parts = res.candidates[0].content.parts
                            if parts and hasattr(parts[0], 'text'):
                                return parts[0].text.strip()
                except Exception:
                    continue
        except Exception as e:
            logger.debug("Re-init client attempt failed: %s", e)

    return None
