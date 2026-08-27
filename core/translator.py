"""
Bilingual Cross-Language Translation Engine for Yakob Assistant.
Supports:
1. Google Translate GTX
2. MyMemory Translation API
3. Internal LLM Cross-Language Chain-of-Thought
"""
import urllib.request
import urllib.parse
import json
import re
from typing import Optional


class AmharicEnglishTranslator:
    def __init__(self):
        self.common_phrases = {
            "የፈረንሳይ ዋና ከተማ": "capital of France",
            "የኢትዮጵያ ዋና ከተማ": "capital of Ethiopia",
            "ስንት ሰዓት ነው": "what time is it",
            "ዛሬ ምን ቀን ነው": "what date is today",
            "የአየር ሁኔታ": "weather forecast",
            "ሙዚቃ አጫውት": "play music",
            "ካልኩሌተር ክፈት": "open calculator",
            "ክሮምን ክፈት": "open chrome",
            "ስክሪንሾት አንሳ": "take screenshot"
        }

    def translate_amharic_to_english(self, text: str) -> str:
        """Translates Amharic input to English for LLM processing."""
        return self._do_translate(text, source_lang="am", target_lang="en")

    def translate_english_to_amharic(self, text: str) -> str:
        """Translates English LLM answer back to fluent Amharic for TTS speaking."""
        return self._do_translate(text, source_lang="en", target_lang="am")

    def _do_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip() or source_lang == target_lang:
            return text

        # 1. Check phrase cache
        if source_lang == "am" and text.strip() in self.common_phrases:
            return self.common_phrases[text.strip()]

        # 2. Try Google Translate Endpoint
        try:
            url = (
                f"https://translate.googleapis.com/translate_a/single"
                f"?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
            )
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and len(data) > 0 and data[0]:
                    translated_segments = [seg[0] for seg in data[0] if seg and len(seg) > 0 and seg[0]]
                    res = "".join(translated_segments).strip()
                    if res:
                        return res
        except Exception:
            pass

        # 3. Fallback: MyMemory Free Translation API
        try:
            langpair = f"{source_lang}|{target_lang}"
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={langpair}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and "responseData" in data and "translatedText" in data["responseData"]:
                    res = data["responseData"]["translatedText"].strip()
                    if res:
                        return res
        except Exception:
            pass

        return text
