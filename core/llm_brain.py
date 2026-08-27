"""
LLM Brain Module for Yakob Desktop Assistant.
Integrates Google Gemini 2.5 Flash for natural, warm, and highly human-like conversational intelligence in Amharic & English.
"""
import os
import re
from typing import Optional, Tuple

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class LLMBrain:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.conversation_history = []
        self._init_client()

    def set_api_key(self, api_key: str):
        """Updates the Gemini API key and reinitializes the client."""
        self.api_key = api_key.strip()
        self._init_client()

    def _init_client(self):
        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[LLMBrain] Gemini init note: {e}")
                self.client = None
        else:
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def generate_response(self, user_prompt: str, language: str = "am") -> Optional[str]:
        """
        Generates a human-like, concise conversational response using Gemini 2.5 Flash.
        """
        if not self.is_available() or not user_prompt:
            return None

        system_instruction = (
            "You are Yakob (ያዕቆብ), a friendly, helpful, and highly natural desktop voice assistant for Windows. "
            "You speak fluently in both Amharic (አማርኛ) and English. "
            "Tone guidelines: "
            "1. Speak in a warm, polite, and human conversational tone (avoid sounding robotic or like a sterile machine). "
            "2. Keep spoken responses concise and punchy (1 to 3 short sentences) because your output will be read aloud via voice TTS. "
            "3. If the user speaks Amharic, respond naturally in Amharic with proper Ge'ez punctuation. "
            "4. If the user speaks English, respond naturally in English. "
            "5. Never output markdown code blocks or bulleted lists unless explicitly asked, since this is for voice listening."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=250,
                )
            )
            if response and response.text:
                clean_text = response.text.strip()
                # Remove asterisks and markdown symbols for clean TTS reading
                clean_text = re.sub(r'[*_#`]', '', clean_text)
                return clean_text
        except Exception as e:
            print(f"[LLMBrain] Gemini generation error: {e}")

        return None
