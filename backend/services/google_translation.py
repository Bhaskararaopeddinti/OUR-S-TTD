"""
google_translation.py – Translation service using urllib (no Cloud SDK needed).
Uses MyMemory free API as fallback; Gemini for full multilingual support.
"""
import os
import json
import urllib.request
import urllib.parse
import logging

logger = logging.getLogger(__name__)

LANG_CODES = {
    "English": "en", "Telugu": "te", "Hindi": "hi",
    "Tamil": "ta", "Kannada": "kn", "Malayalam": "ml",
    "Marathi": "mr", "Bengali": "bn",
}


def get_language_code(language_name: str) -> str:
    """Convert language name to BCP-47 code."""
    return LANG_CODES.get(language_name, "en")


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text to target language.
    Uses MyMemory free API (no key needed for small usage).
    Falls back to original text on any error.
    """
    if not text or target_language == "en":
        return text

    try:
        encoded = urllib.parse.quote(text[:500])  # MyMemory limit
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|{target_language}"
        req = urllib.request.Request(url, headers={"User-Agent": "OURS-TTD/2.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and translated.lower() != "invalid language pair":
                return translated
    except Exception as e:
        logger.warning("Translation failed: %s", e)

    return text  # Return original on failure
