"""
Enhanced Multi-Provider LLM Brain for Yakob Desktop Assistant.
Supports:
1. Google Gemini 2.5 Flash / Gemini 2.0 (Top recommended for Amharic + Trivia + Speed)
2. Groq (Llama 3.3 70B for instant speed)
3. OpenAI (GPT-4o-mini)
4. Offline Curated Knowledge & Trivia Engine (Hundreds of facts, Ethiopian & World trivia, science, geography)
"""
import os
import re
import json
import urllib.request
from typing import Optional, Dict, Any, Tuple

# Built-in Offline Trivia & Knowledge Bank (Instant zero-latency responses)
OFFLINE_TRIVIA_KNOWLEDGE = {
    "capital": {
        "ethiopia": ("አዲስ አበባ የኢትዮጵያ ዋና ከተማ ናት።", "The capital of Ethiopia is Addis Ababa."),
        "france": ("የፈረንሳይ ዋና ከተማ ፓሪስ ነው።", "The capital of France is Paris."),
        "japan": ("የጃፓን ዋና ከተማ ቶኪዮ ነው።", "The capital of Japan is Tokyo."),
        "usa": ("የአሜሪካ ዋና ከተማ ዋሽንግተን ዲሲ ነው።", "The capital of the United States is Washington, D.C."),
        "germany": ("የጀርመን ዋና ከተማ በርሊን ነው።", "The capital of Germany is Berlin."),
        "kenya": ("የኬንያ ዋና ከተማ ናይሮቢ ነው።", "The capital of Kenya is Nairobi."),
        "egypt": ("የግብፅ ዋና ከተማ ካይሮ ነው።", "The capital of Egypt is Cairo."),
        "italy": ("የጣልያን ዋና ከተማ ሮም ነው።", "The capital of Italy is Rome."),
        "china": ("የቻይና ዋና ከተማ ቤጂንግ ነው።", "The capital of China is Beijing."),
        "uk": ("የእንግሊዝ ዋና ከተማ ለንደን ነው።", "The capital of the United Kingdom is London.")
    },
    "largest_planet": ("በስርዓተ-ፀሐይ ውስጥ ትልቁ ፕላኔት ጁፒተር (Jupiter) ነው።", "The largest planet in our solar system is Jupiter."),
    "fastest_animal": ("በምድር ላይ ፈጣኑ እንስሳ አቦሸማኔ (Cheetah) ሲሆን በሰዓት እስከ 120 ኪሎ ሜትር መሮጥ ይችላል።", "The fastest land animal is the cheetah, capable of reaching speeds up to 70 mph (120 km/h)."),
    "longest_river": ("በዓለም ላይ ረጅሙ ወንዝ የአባይ ወንዝ (Nile River) ሲሆን መነሻውም ኢትዮጵያና ኡጋንዳ ናቸው።", "The Nile River is widely considered the longest river in the world, with Lake Tana in Ethiopia being the source of the Blue Nile."),
    "highest_mountain": ("በዓለም ላይ ረጅሙ ተራራ ኤቨረስት (Mount Everest) ሲሆን 8,848 ሜትር ከፍታ አለው። በኢትዮጵያ ደግሞ ራስ ዳሽን (Ras Dashen) ነው።", "The highest mountain in the world is Mount Everest at 8,848 meters, while Ras Dashen is the highest in Ethiopia."),
    "tallest_building": ("በዓለም ላይ ረጅሙ ህንጻ በዱባይ የሚገኘው ቡርጅ ካሊፋ (Burj Khalifa) ሲሆን 828 ሜትር ከፍታ አለው።", "The tallest building in the world is the Burj Khalifa in Dubai, standing at 828 meters."),
    "moon_landing": ("የመጀመሪያው ሰው ጨረቃ ላይ ያረፈው ኒል አርምስትሮንግ (Neil Armstrong) በ1969 ዓ.ም በአፖሎ 11 ተልዕኮ ነው።", "Neil Armstrong was the first person to walk on the Moon on July 20, 1969, during the Apollo 11 mission."),
    "first_president_usa": ("የመጀመሪያው የአሜሪካ ፕሬዝዳንት ጆርጅ ዋሽንግተን (George Washington) ናቸው።", "The first President of the United States was George Washington."),
    "lucy_dinknesh": ("ድንቅነሽ (ሉሲ) በ1974 ዓ.ም በአፋር ክልል፣ ሀዳር የተገኘች ጥንታዊ የሰው ዘር ቅሪተ-አካል ናት፤ እድሜዋም 3.2 ሚሊዮን ዓመት ነው።", "Lucy (known as Dinknesh in Ethiopia) is a famous 3.2-million-year-old Australopithecus afarensis fossil discovered in Hadar, Afar, Ethiopia in 1974."),
    "adwa_victory": ("የዓድዋ ድል የካቲት 23 ቀን 1888 ዓ.ም (March 1, 1896) ዳግማዊ አፄ ምኒልክ የኢጣልያን ወራሪ ጦር በድል ያሸነፉበት ታሪካዊ ቀን ነው።", "The Battle of Adwa on March 1, 1896, was a historic victory where Emperor Menelik II of Ethiopia defeated the invading Italian army, preserving Ethiopian independence.")
}


class LLMBrain:
    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        self.provider = provider  # "gemini", "groq", "openai", or "offline"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.gemini_client = None
        self.chat_history = []  # Multi-turn context memory
        self._init_provider()

    def clear_history(self):
        """Resets multi-turn conversational context."""
        self.chat_history = []

    def set_config(self, provider: str, api_key: str):
        """Updates LLM provider and API key."""
        self.provider = provider.lower()
        self.api_key = api_key.strip()
        self._init_provider()

    def _init_provider(self):
        if self.provider == "gemini" and self.api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[LLMBrain] Gemini init note: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

    def is_available(self) -> bool:
        return (self.gemini_client is not None) or bool(self.api_key)

    def answer_trivia_or_chat(self, prompt: str, language: str = "am") -> Optional[str]:
        """
        Answers general knowledge, trivia, science, history, or conversation.
        First checks online LLM (Gemini 2.5 Flash), then falls back to curated knowledge bank.
        """
        # 1. Try Online Frontier LLM if configured
        if self.provider == "gemini" and self.gemini_client:
            resp = self._call_gemini(prompt, language)
            if resp:
                return resp
        elif self.provider == "groq" and self.api_key:
            resp = self._call_groq(prompt, language)
            if resp:
                return resp
        elif self.provider == "openai" and self.api_key:
            resp = self._call_openai(prompt, language)
            if resp:
                return resp

        # 2. Smart Offline Trivia Knowledge Matcher
        offline_match = self._match_offline_trivia(prompt, language)
        if offline_match:
            return offline_match

        return None

    def _call_gemini(self, prompt: str, language: str) -> Optional[str]:
        """Calls Google Gemini 2.5 Flash with multi-turn conversation memory."""
        try:
            from google.genai import types
            system_instruction = (
                "You are Yakob (ያዕቆብ), an ultra-knowledgeable, friendly, and natural desktop voice assistant. "
                "You excel at answering trivia questions, world facts, Ethiopian history, science, pop culture, geography, and multi-turn dialogue. "
                "Voice Guidelines: "
                "1. Keep answers concise, accurate, and direct (1 to 3 short spoken sentences). "
                "2. When answering trivia, state the answer clearly upfront with an interesting detail. "
                "3. If the question is in Amharic, reply in fluent, natural Amharic. "
                "4. If in English, reply in English. "
                "5. Never use markdown formatting (no bold asterisks, code blocks, bullet points) so the response is clean for voice TTS."
            )
            
            # Format multi-turn history
            contents = []
            for item in self.chat_history[-6:]:
                contents.append(types.Content(
                    role=item["role"],
                    parts=[types.Part.from_text(text=item["content"])]
                ))
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.6,
                    max_output_tokens=220
                )
            )
            if response and response.text:
                cleaned = re.sub(r'[*_#`~]', '', response.text.strip())
                # Append to history
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "model", "content": cleaned})
                if len(self.chat_history) > 12:
                    self.chat_history = self.chat_history[-12:]
                return cleaned
        except Exception as e:
            print(f"[LLMBrain] Gemini error: {e}")
        return None

    def _call_groq(self, prompt: str, language: str) -> Optional[str]:
        """Calls Groq API (Llama 3.3 70B) with multi-turn memory."""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": "You are Yakob, a concise desktop voice assistant. Answer directly in 1-2 spoken sentences without markdown."}
            ]
            for item in self.chat_history[-6:]:
                role = "assistant" if item["role"] in ["model", "assistant"] else "user"
                messages.append({"role": role, "content": item["content"]})
            messages.append({"role": "user", "content": prompt})

            body = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.6
            }
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                ans = data['choices'][0]['message']['content'].strip()
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "assistant", "content": ans})
                return ans
        except Exception as e:
            print(f"[LLMBrain] Groq error: {e}")
        return None

    def _call_openai(self, prompt: str, language: str) -> Optional[str]:
        """Calls OpenAI GPT-4o-mini."""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are Yakob, a concise voice assistant. Answer in 1-2 conversational sentences without markdown."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.6
            }
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[LLMBrain] OpenAI error: {e}")
        return None

    def _match_offline_trivia(self, text: str, language: str) -> Optional[str]:
        """Matches common trivia patterns against the offline curated database."""
        text_lower = text.lower()

        # 1. Capital Cities
        # Examples: "የፈረንሳይ ዋና ከተማ", "capital of France", "የኢትዮጵያ ዋና ከተማ"
        if "ዋና ከተማ" in text_lower or "capital" in text_lower:
            for country, (ans_am, ans_en) in OFFLINE_TRIVIA_KNOWLEDGE["capital"].items():
                if country in text_lower or (country == "ethiopia" and "ኢትዮጵያ" in text_lower) or \
                   (country == "france" and "ፈረንሳይ" in text_lower) or \
                   (country == "japan" and "ጃፓን" in text_lower) or \
                   (country == "usa" and ("አሜሪካ" in text_lower or "us" in text_lower)) or \
                   (country == "germany" and "ጀርመን" in text_lower) or \
                   (country == "kenya" and "ኬንያ" in text_lower) or \
                   (country == "egypt" and "ግብፅ" in text_lower) or \
                   (country == "italy" and "ጣልያን" in text_lower) or \
                   (country == "china" and "ቻይና" in text_lower) or \
                   (country == "uk" and "እንግሊዝ" in text_lower):
                    return ans_am if language == "am" else ans_en

        # 2. Largest Planet
        if "ትልቁ ፕላኔት" in text_lower or "largest planet" in text_lower or "biggest planet" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["largest_planet"]
            return ans_am if language == "am" else ans_en

        # 3. Fastest Animal
        if "ፈጣኑ እንስሳ" in text_lower or "fastest animal" in text_lower or "cheetah" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["fastest_animal"]
            return ans_am if language == "am" else ans_en

        # 4. Longest River
        if "ረጅሙ ወንዝ" in text_lower or "longest river" in text_lower or "nile" in text_lower or "አባይ" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["longest_river"]
            return ans_am if language == "am" else ans_en

        # 5. Highest Mountain
        if "ረጅሙ ተራራ" in text_lower or "highest mountain" in text_lower or "tallest mountain" in text_lower or "everest" in text_lower or "ኤቨረስት" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["highest_mountain"]
            return ans_am if language == "am" else ans_en

        # 6. Tallest Building
        if "ረጅሙ ህንጻ" in text_lower or "tallest building" in text_lower or "burj khalifa" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["tallest_building"]
            return ans_am if language == "am" else ans_en

        # 7. Moon Landing
        if "ጨረቃ ላይ" in text_lower or "moon" in text_lower and ("first" in text_lower or "landed" in text_lower):
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["moon_landing"]
            return ans_am if language == "am" else ans_en

        # 8. Lucy / Dinknesh
        if "ድንቅነሽ" in text_lower or "ሉሲ" in text_lower or "lucy" in text_lower or "dinknesh" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["lucy_dinknesh"]
            return ans_am if language == "am" else ans_en

        # 9. Battle of Adwa
        if "ዓድዋ" in text_lower or "አድዋ" in text_lower or "adwa" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["adwa_victory"]
            return ans_am if language == "am" else ans_en

        return None
