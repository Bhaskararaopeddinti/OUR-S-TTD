"""
OURS TTD — Gemini Standalone Test Script
Verify GEMINI_API_KEY loading, Gemini API client connection, model generation, and response format.
"""
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from backend.services.ai_service import pilgrim_reply

def test_gemini_direct():
    print("==================================================")
    print("OURS TTD — Standalone Gemini Test")
    print("==================================================")

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is missing from .env!")
        sys.exit(1)

    print("GEMINI_API_KEY loaded: [OK] (Key starts with: %s...)" % api_key[:4])

    test_message = "Explain how a first-time pilgrim can plan a visit to Tirumala."
    print("\nSending test message: '%s'" % test_message)

    res = pilgrim_reply(message=test_message, language="English")

    print("\nResponse Received:")
    print("--------------------------------------------------")
    print("Source:", res.get("source"))
    print("AI Available:", res.get("ai_available"))
    print("Language:", res.get("language"))
    print("Reply Text:\n", res.get("reply"))
    print("--------------------------------------------------")

    if res.get("source") == "gemini" and res.get("ai_available") is True:
        print("\n[SUCCESS] Gemini generated a real response successfully!")
    else:
        print("\n[FAILURE] Gemini call failed or returned fallback!")

if __name__ == "__main__":
    test_gemini_direct()
