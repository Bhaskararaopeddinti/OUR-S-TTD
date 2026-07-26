import os
from typing import Optional
from google.cloud import translate

def translate_text(text: str, target_language: str) -> str:
    """Translate text to target language using Google Cloud Translation API."""
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not api_key:
        # Fallback: return original text if no API key
        return text
    
    try:
        client = translate.TranslationServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "our-ttd-project")
        parent = f"projects/{project_id}"
        
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",
                "source_language_code": "en",
                "target_language_code": target_language,
            }
        )
        
        return response.translations[0].translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text on error

def get_language_code(language_name: str) -> str:
    """Convert language name to Google Translate language code."""
    language_map = {
        "English": "en",
        "Telugu": "te",
        "Hindi": "hi",
        "Tamil": "ta",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Marathi": "mr",
        "Bengali": "bn"
    }
    return language_map.get(language_name, "en")
