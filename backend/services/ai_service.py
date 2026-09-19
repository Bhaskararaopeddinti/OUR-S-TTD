"""
OURS TTD — AI Service
Gemini-powered pilgrim assistant with TTD-specific live database context & open-domain support.
Communicates directly with Google Gemini API using Google GenAI SDK and verified active models.
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

DEFAULT_MODELS = [
    'gemini-3.5-flash-lite',        # confirmed working — fastest and cheapest
    'gemini-flash-lite-latest',     # alias for latest lite flash
    'gemini-flash-latest',          # alias for latest flash
    'gemini-3.1-flash-lite',        # newer generation lite
    'gemini-3-flash-preview',       # preview generation
    'gemini-2.5-flash',             # stable generation fallback
]

_genai_client = None
_genai_legacy_model = None


def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment variables (supports GEMINI_API_KEY or GOOGLE_API_KEY)."""
    # Re-trigger load_dotenv if running locally
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env")
    load_dotenv()
    
    key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if key == "your-gemini-api-key-here":
        return ""
    return key


def _init_gemini() -> bool:
    """Initialise Gemini client or legacy model lazily."""
    global _genai_client, _genai_legacy_model
    if _genai_client is not None or _genai_legacy_model is not None:
        return True

    api_key = get_gemini_api_key()
    key_configured = bool(api_key)
    logger.info("GEMINI_API_KEY configured: %s", key_configured)

    if not key_configured:
        logger.warning("GEMINI_API_KEY is missing or unconfigured in environment.")
        return False

    # Try modern google.genai SDK first (preferred)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        _genai_client = client
        logger.info("Gemini initialized successfully with google.genai Client")
        return True
    except Exception as e:
        safe_err = str(e).split("key=")[0].split("API_KEY=")[0]
        logger.debug("google.genai Client init attempt failed: %s", safe_err)

    # Fallback to google.generativeai SDK if modern SDK fails to initialize
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        
        legacy_models = ['gemini-1.5-flash', 'gemini-pro']
        for model_name in legacy_models:
            try:
                m = legacy_genai.GenerativeModel(model_name)
                _genai_legacy_model = m
                logger.info("Gemini initialized with legacy google.generativeai model: %s", model_name)
                return True
            except Exception as ex:
                continue
    except Exception as e:
        safe_err = str(e).split("key=")[0].split("API_KEY=")[0]
        logger.error("Failed to initialize legacy google.generativeai: %s", safe_err)

    return False


SYSTEM_PROMPT = """You are the OURS TTD AI Pilgrim Assistant.

Your primary role is to help pilgrims visiting Tirumala with concise, accurate, practical, and helpful information. You are also capable of answering general knowledge, technical, scientific, and open-domain questions accurately.

RULES:
1. Always understand the user's EXACT question before answering. Answer ONLY what is relevant to the question asked.
2. Format every response as 4 to 5 short, clear bullet points using * with **bold key terms**.
3. Each bullet should be 1-2 sentences max. Keep it mobile-friendly, crisp, and easy to scan.
4. For pilgrim/temple questions: answer from the PILGRIM'S perspective with practical, actionable advice.
5. Do NOT add unrelated TTD history, deity descriptions, or generic intros unless explicitly asked.
6. For queue questions: use the provided live data context. If the context states data is unavailable, clearly inform that live numeric crowd numbers are currently unavailable and suggest checking VQC display boards.
7. For transport/facilities: use the provided database context when available.
8. Do NOT invent or fabricate current data (crowd numbers, wait times). Only use verified data from the [SYSTEM CONTEXT] sections.
9. NEVER mention API keys, .env, backend configurations, developer details, or debug messages.
10. NEVER start with "Sure, here is..." or similar filler. Start directly with the first bullet point.
11. If the user asks a general knowledge, programming, scientific, or everyday question (e.g., "What is Python?", "Explain machine learning"), answer it directly, accurately, and concisely in 4-5 bullet points. Do NOT force it into a Tirumala/TTD context.
"""


def _build_db_context(message: str, db: Optional[Any] = None) -> str:
    """Retrieve relevant application database facts to attach as context for Gemini."""
    context_parts = []
    msg_lower = message.lower()

    # Queue status context — prefer CCTV AI data over manual data over AI prediction
    if any(k in msg_lower for k in ("queue", "wait", "crowd", "darshan line", "density", "line", "pilgrim", "time to join", "cctv", "people count")):
        try:
            from datetime import date as dt_date
            from backend.models import PilgrimFlowData, CCTVCrowdRecord
            from backend.services.cctv_vision import cctv_worker
            from sqlalchemy import desc

            cctv_live = cctv_worker.get_status()
            if cctv_live.get("is_running") or (cctv_live.get("incoming", 0) > 0 or cctv_live.get("outgoing", 0) > 0):
                context_parts.append(
                    f"[SYSTEM CONTEXT - DEMO CCTV AI QUEUE DATA (Live Vision Analysis)]: "
                    f"Data Source = Demo CCTV AI Data (Anonymous People Counting), "
                    f"Location = {cctv_live['location_name']}, "
                    f"Observed People in Camera = {cctv_live['observed_count']}, "
                    f"Incoming Devotees = {cctv_live['incoming']}, "
                    f"Outgoing Devotees = {cctv_live['outgoing']}, "
                    f"Net Flow = {cctv_live['net_flow']:+d}, "
                    f"Estimated Crowd = {cctv_live['estimated_crowd']:,}, "
                    f"Queue Status = {cctv_live['queue_status']}, "
                    f"Crowd Trend = {cctv_live['trend']}."
                )
            elif db:
                today = dt_date.today().strftime("%Y-%m-%d")
                latest_cctv = db.query(CCTVCrowdRecord).order_by(desc(CCTVCrowdRecord.timestamp)).first()
                if latest_cctv:
                    context_parts.append(
                        f"[SYSTEM CONTEXT - DEMO CCTV AI RECORD ({latest_cctv.timestamp.strftime('%Y-%m-%d %H:%M')} UTC)]: "
                        f"Data Source = Demo CCTV AI Data, "
                        f"Location = {latest_cctv.location_name}, "
                        f"Observed Count = {latest_cctv.observed_count}, "
                        f"Incoming Count = {latest_cctv.incoming_count}, "
                        f"Outgoing Count = {latest_cctv.outgoing_count}, "
                        f"Net Flow = {latest_cctv.net_flow:+d}, "
                        f"Queue Status = {latest_cctv.queue_status}, "
                        f"Trend = {latest_cctv.trend}."
                    )
                else:
                    latest_flow = (
                        db.query(PilgrimFlowData)
                        .filter(PilgrimFlowData.date == today)
                        .order_by(desc(PilgrimFlowData.start_time))
                        .first()
                    )
                    if latest_flow:
                        src_label = "Demo CCTV AI Data" if getattr(latest_flow, "source", "") == "demo_cctv_ai" else "Live Admin Data"
                        context_parts.append(
                            f"[SYSTEM CONTEXT - {src_label.upper()} (Today {today})]: "
                            f"Current Estimated Crowd = {latest_flow.estimated_crowd:,} pilgrims, "
                            f"Queue Status = {latest_flow.queue_status}, "
                            f"Incoming Flow = {latest_flow.incoming_pilgrims} pilgrims/slot, "
                            f"Outgoing Flow = {latest_flow.outgoing_pilgrims} pilgrims/slot, "
                            f"Net Flow change = {latest_flow.net_pilgrims:+d}, "
                            f"Festival Day = {'YES' if latest_flow.festival else 'NO'}, "
                            f"Time Slot Recorded = {latest_flow.start_time} to {latest_flow.end_time}."
                        )
                    else:
                        from backend.services.ttd_official import public_status
                        status = public_status()
                        wait_val = status.get('wait_minutes')
                        crowd_val = status.get('crowd_density', 'Moderate')
                        if wait_val is not None:
                            from backend.services.queue_prediction import predict_queue_status
                            pred = predict_queue_status(wait_val, crowd_val, db=db)

                            context_parts.append(
                                f"[SYSTEM CONTEXT - ESTIMATED QUEUE STATUS]: "
                                f"Estimated wait ≈ {wait_val} mins, "
                                f"Crowd density = {crowd_val}. "
                                f"Trend: {pred.get('trend')} — Recommendation: {pred.get('recommendation')}."
                            )
                        else:
                            context_parts.append(
                                f"[SYSTEM CONTEXT - LIVE QUEUE STATUS]: "
                                f"• Queue Status: Data unavailable.\n"
                                f"• Reason: No recent admin crowd data is recorded in the system.\n"
                                f"Advise the pilgrim to verify live wait boards at Vaikuntam Queue Complex."
                            )
        except Exception as e:
            logger.debug("Could not fetch queue context: %s", e)

    # Transport context
    if any(k in msg_lower for k in ("bus", "transport", "route", "reach", "tirupati", "tirumala", "fare", "shuttle", "alipiri", "mettu", "tour", "travel")):
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
    if any(k in msg_lower for k in ("medical", "hospital", "doctor", "annaprasadam", "food", "eat", "restroom", "toilet", "laddu", "phone", "deposit", "parking", "stay", "accommodation")):
        try:
            from backend.services.facilities_data import FACILITIES
            relevant = [f"{f['name']} ({f['kind']})" for f in FACILITIES[:6]]
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
    Generate a dynamic reply using Gemini API. Every question goes through Gemini.
    No static/hardcoded answers. If Gemini fails, return safe error diagnostic.
    Never leaks debug information, API keys, or technical errors.
    """
    logger.info("AI request received")
    logger.info("AI message received, length=%d", len(message))

    api_key = get_gemini_api_key()
    logger.info("Gemini API key configured: %s", bool(api_key))

    if not api_key:
        logger.error("Gemini API key is not configured in production environment.")
        return {
            "reply": (
                "* **Sorry**, I couldn't process your question right now.\n"
                "* The AI service is temporarily unavailable (API key unconfigured).\n"
                "* Please **try again** in a moment.\n"
                "* For urgent help, call **TTD Helpline: 155257** (24/7)."
            ),
            "language": language,
            "source": "error",
            "error": "GEMINI_API_KEY not configured",
            "ai_available": False
        }

    # Initialize Gemini client
    if _init_gemini():
        logger.info("Gemini request starting")

        db_context = _build_db_context(message, db)
        lang_instruction = f"\nPlease respond in {language}." if language and language != "English" else ""

        prompt_parts = [SYSTEM_PROMPT]
        if db_context:
            prompt_parts.append(db_context)
        if lang_instruction:
            prompt_parts.append(lang_instruction)
        prompt_parts.append(f"\nUser's Question: {message}")

        full_prompt = "\n\n".join(prompt_parts)

        try:
            reply_text = _generate_with_gemini(full_prompt, history)
            if reply_text and len(reply_text.strip()) > 0:
                logger.info("Gemini response received")
                logger.info("AI response successfully returned")
                return {
                    "reply": reply_text.strip(),
                    "language": language,
                    "source": "gemini",
                    "ai_available": True
                }
            else:
                logger.error("Gemini request failed: Empty response from model.")
        except Exception as e:
            safe_error = str(e).split("key=")[0].split("API_KEY=")[0]
            logger.error("Gemini request failed: %s (%s)", type(e).__name__, safe_error)

    # Fallback if Gemini temporarily failed or threw an exception
    logger.info("Gemini call failed or timed out, returning user-friendly error")
    return {
        "reply": (
            "* **Sorry**, I couldn't process your question right now.\n"
            "* The AI service is temporarily unavailable.\n"
            "* Please **try again** in a moment.\n"
            "* For urgent help, call **TTD Helpline: 155257** (24/7)."
        ),
        "language": language,
        "source": "error",
        "error": "AI service temporarily unavailable",
        "ai_available": False
    }


def _get_model_candidates() -> List[str]:
    """Build prioritized list of model candidates starting with any user configured model."""
    configured_model = os.getenv("GEMINI_MODEL", "").strip()
    candidates = []
    if configured_model:
        candidates.append(configured_model)
    for m in DEFAULT_MODELS:
        if m not in candidates:
            candidates.append(m)
    return candidates


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
        models_to_try = _get_model_candidates()
        
        # Modern google.genai Client
        if _genai_client is not None:
            for model_name in models_to_try:
                try:
                    logger.info("Attempting generation with model: %s", model_name)
                    response = _genai_client.models.generate_content(
                        model=model_name,
                        contents=formatted_prompt
                    )
                    if response:
                        # Candidate parts extraction
                        if getattr(response, 'candidates', None) and len(response.candidates) > 0:
                            cand = response.candidates[0]
                            if getattr(cand, 'content', None) and getattr(cand.content, 'parts', None):
                                answer_parts = [
                                    p.text for p in cand.content.parts
                                    if hasattr(p, 'text') and p.text and not getattr(p, 'thought', False)
                                ]
                                if answer_parts:
                                    logger.info("Successfully generated response using model %s", model_name)
                                    return "\n".join(answer_parts).strip()
                                
                                all_parts = [p.text for p in cand.content.parts if hasattr(p, 'text') and p.text]
                                if all_parts:
                                    logger.info("Successfully generated response using model %s (parts)", model_name)
                                    return all_parts[-1].strip()

                        # Direct text attribute fallback
                        try:
                            if hasattr(response, 'text') and response.text:
                                logger.info("Successfully generated response using model %s (.text)", model_name)
                                return response.text.strip()
                        except Exception:
                            pass
                except Exception as e:
                    safe_err = str(e).split("key=")[0].split("API_KEY=")[0]
                    logger.warning("Model %s generation attempt failed: %s (%s)", model_name, type(e).__name__, safe_err[:120])
                    continue

        # Fallback to legacy google.generativeai if modern client was unavailable
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
            return future.result(timeout=25.0)
    except Exception as ex:
        logger.error("Gemini model call timeout or thread error: %s", ex)
        return None
