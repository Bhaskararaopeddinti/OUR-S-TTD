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

MODEL_CANDIDATES = [
    'gemini-3.1-flash-lite-preview',
    'gemini-flash-lite-latest',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-flash-latest',
    'gemini-3.6-flash',
    'gemini-3.7-flash',
    'gemma-4-26b-a4b-it',
    'gemma-4-31b-it'
]

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


SYSTEM_PROMPT = """You are the OURS TTD AI Pilgrim Assistant.

Your job is to help pilgrims visiting Tirumala with concise, accurate and practical information.

RULES:
1. Always understand the user's EXACT question before answering. Answer ONLY what is relevant to the question asked.
2. Format every response as 4 to 5 short, clear bullet points using * with **bold key terms**.
3. Each bullet should be 1-2 sentences max. Keep it mobile-friendly and easy to scan.
4. Answer from the PILGRIM'S perspective. Give practical, actionable advice.
5. Do NOT add unrelated TTD history, deity descriptions, or generic introductions unless the user specifically asks.
6. For queue questions: use the provided live data context. If no data is available, say "Current queue data is unavailable right now."
7. For transport/facilities: use the provided database context when available.
8. Do NOT invent or fabricate current data (crowd numbers, wait times). Only use data from the [SYSTEM CONTEXT] sections.
9. NEVER mention API keys, .env, backend configurations, developer details, or debug messages.
10. NEVER start with "Sure, here is..." or similar filler. Start directly with the first bullet point.
11. If the user asks a general question unrelated to Tirumala, answer it briefly and helpfully.
12. For recommendations, clearly distinguish between current data and general advice. Never claim predictions are guaranteed.
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
    Generate a dynamic reply using Gemini API. Every question goes through Gemini.
    No static/hardcoded answers. If Gemini fails, show a user-friendly error.
    Never leaks debug information, API keys, or technical errors.
    """
    logger.info("CHAT REQUEST RECEIVED: language=%s, msg_len=%d", language, len(message))

    # Always try Gemini — this is the ONLY answer source
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

    # If Gemini is unavailable or failed — show clean error, NOT static answers
    logger.info("Gemini unavailable, returning user-friendly error")
    return {
        "reply": (
            "* **Sorry**, I couldn't process your question right now.\n"
            "* The AI service is temporarily unavailable.\n"
            "* Please **try again** in a moment.\n"
            "* For urgent help, call **TTD Helpline: 155257** (24/7)."
        ),
        "language": language,
        "source": "error",
        "ai_available": False
    }


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
        import time
        # Modern google.genai Client
        if _genai_client is not None:
            for model_name in MODEL_CANDIDATES:
                try:
                    response = _genai_client.models.generate_content(
                        model=model_name,
                        contents=formatted_prompt
                    )
                    if response:
                        # Candidate parts extraction (prioritize non-thought final answer parts)
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
                                    logger.info("Successfully generated response using model %s (fallback parts)", model_name)
                                    return all_parts[-1].strip()

                        # Direct text attribute fallback
                        try:
                            if hasattr(response, 'text') and response.text:
                                logger.info("Successfully generated response using model %s (.text)", model_name)
                                return response.text.strip()
                        except Exception:
                            pass
                except Exception as e:
                    err_msg = str(e)
                    logger.info("Model candidate %s attempt failed: %s", model_name, err_msg[:100])
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        time.sleep(0.5)
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
            return future.result(timeout=25.0)
    except Exception as ex:
        logger.debug("Gemini model call exceeded timeout or encountered error: %s", ex)
        return None
