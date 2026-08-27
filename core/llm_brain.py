"""
Multi-Provider LLM Brain & Live Internet Grounding Engine for Yakob Assistant.
Supports:
1. Google Gemini 2.5 Flash with Live Google Search Grounding & Multi-Turn Memory
2. Groq (Llama 3.3 70B Versatile)
3. OpenAI (GPT-4o-mini)
4. Live Autonomous Web Search Scraper (DuckDuckGo + Wikipedia) for real-time live facts
5. Curated Offline Trivia & Ethiopian History Database
6. Cross-Lingual Amharic <-> English Reasoning Pipeline
"""
import os
import re
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List

from config import OFFLINE_TRIVIA_KNOWLEDGE
from core.web_search import web_search
from core.translator import AmharicEnglishTranslator

try:
    from google import genai
    from google.genai import types
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False


class LLMBrain:
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.gemini_client = None
        self.chat_history: List[Dict[str, str]] = []
        self.translator = AmharicEnglishTranslator()
        
        self._init_client()

    def _init_client(self):
        if self.provider == "gemini" and GEMINI_SDK_AVAILABLE and self.api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[LLMBrain] Gemini init warning: {e}")
                self.gemini_client = None

    def set_config(self, provider: str, api_key: Optional[str] = None):
        self.provider = provider.lower()
        if api_key:
            self.api_key = api_key.strip()
        self._init_client()

    def clear_history(self):
        self.chat_history.clear()

    def answer_trivia_or_chat(self, prompt: str, language: str = "en") -> Optional[str]:
        """Alias for generate_response for chatbot and trivia handling."""
        return self.generate_response(prompt, language)

    def generate_response(self, prompt: str, language: str = "en") -> Optional[str]:
        """
        Generates conversational intelligence response.
        If the answer is unknown or requires real-time facts, searches the live internet.
        """
        if not prompt or not prompt.strip():
            return None

        # 1. Check LLM APIs (Gemini 2.5 Flash / Groq / OpenAI)
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

        # 3. Live Autonomous Web Search (For answers Yakob doesn't know offline)
        live_web_fact = self._search_live_internet(prompt, language)
        if live_web_fact:
            return live_web_fact

        return None

    def _search_live_internet(self, prompt: str, language: str) -> Optional[str]:
        """Searches live web (Wikipedia + DuckDuckGo) and translates if needed."""
        try:
            # If in Amharic, translate query to English for optimal web searching
            search_query = prompt
            if language == "am" or any('\u1200' <= c <= '\u137F' for c in prompt):
                search_query = self.translator.translate_amharic_to_english(prompt)

            raw_web_info = web_search.search_live_web(search_query)
            if raw_web_info and len(raw_web_info.strip()) > 15:
                # Clean up web text into 1-2 concise spoken sentences
                clean_web = re.sub(r'[*_#`~]', '', raw_web_info).strip()
                clean_web = re.sub(r'\s+', ' ', clean_web)
                sentences = re.split(r'(?<=[.!?])\s+', clean_web)
                concise_summary = " ".join(sentences[:2]) if len(sentences) > 1 else clean_web
                
                # If user asked in Amharic, translate answer back to Amharic
                if language == "am" or any('\u1200' <= c <= '\u137F' for c in prompt):
                    return self.translator.translate_english_to_amharic(concise_summary)
                return concise_summary
        except Exception as e:
            print(f"[LLMBrain] Live web search note: {e}")
        return None

    def _call_gemini(self, prompt: str, language: str) -> Optional[str]:
        """Calls Google Gemini 2.5 Flash with search grounding & multi-turn memory."""
        try:
            system_instruction = (
                "You are Yakob (ያዕቆብ), a brilliant, friendly, and ultra-knowledgeable desktop AI chatbot and voice assistant. "
                "Conversational Guidelines: "
                "1. Act like a real, intelligent AI chatbot with great conversational flow, deep general knowledge, coding ability, and trivia mastery. "
                "2. When the user asks a question in English: answer concisely and directly in 1 to 3 natural spoken sentences without markdown formatting (no asterisks or bullet points). "
                "3. When the user asks in Amharic (አማርኛ): reason in English for maximum depth, and reply in fluent, authentic Amharic using proper Ge'ez script. "
                "4. If asked about current events, facts, or live info, provide accurate, up-to-date answers."
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

            # Enable live Google Search Grounding tool with Gemini 2.5 Flash
            search_tool = types.Tool(google_search=types.GoogleSearch())

            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[search_tool],
                    temperature=0.6,
                    max_output_tokens=250
                )
            )
            if response and response.text:
                cleaned = re.sub(r'[*_#`~]', '', response.text.strip())
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "model", "content": cleaned})
                if len(self.chat_history) > 12:
                    self.chat_history = self.chat_history[-12:]
                return cleaned
        except Exception as e:
            # Fallback without search tool if tool is rejected
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.6,
                        max_output_tokens=220
                    )
                )
                if response and response.text:
                    cleaned = re.sub(r'[*_#`~]', '', response.text.strip())
                    return cleaned
            except Exception as ex:
                print(f"[LLMBrain] Gemini fallback error: {ex}")
        return None

    def _call_groq(self, prompt: str, language: str) -> Optional[str]:
        """Calls Groq API (Llama 3.3 70B) with live web search augmentation."""
        try:
            # Check if web augmentation helps
            web_context = ""
            if any(w in prompt.lower() for w in ["who is", "what is", "latest", "news", "score", "when was", "where is"]):
                live_info = web_search.search_live_web(prompt)
                if live_info:
                    web_context = f"\nLive Internet Information: {live_info}\n"

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": "You are Yakob, an ultra-smart desktop AI chatbot. Answer directly in 1-2 spoken sentences without markdown asterisks."}
            ]
            for item in self.chat_history[-6:]:
                role = "assistant" if item["role"] in ["model", "assistant"] else "user"
                messages.append({"role": role, "content": item["content"]})
                
            user_msg = prompt + (f" ({web_context})" if web_context else "")
            messages.append({"role": "user", "content": user_msg})

            body = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 220,
                "temperature": 0.6
            }
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                ans = data['choices'][0]['message']['content'].strip()
                ans = re.sub(r'[*_#`~]', '', ans)
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
                    {"role": "system", "content": "You are Yakob, an intelligent AI chatbot. Answer in 1-2 conversational sentences without markdown."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 220,
                "temperature": 0.6
            }
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                ans = data['choices'][0]['message']['content'].strip()
                return re.sub(r'[*_#`~]', '', ans)
        except Exception as e:
            print(f"[LLMBrain] OpenAI error: {e}")
        return None

    def _match_offline_trivia(self, text: str, language: str) -> Optional[str]:
        """Matches common trivia patterns against the offline curated database."""
        text_lower = text.lower()

        # 1. Capital Cities
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

        # 7. First Man on the Moon
        if "ጨረቃ" in text_lower or "moon" in text_lower or "armstrong" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["first_man_on_moon"]
            return ans_am if language == "am" else ans_en

        # 8. Battle of Adwa
        if "አድዋ" in text_lower or "adwa" in text_lower or "menelik" in text_lower or "ምኒልክ" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["adwa_victory"]
            return ans_am if language == "am" else ans_en

        # 9. Lucy / Dinknesh
        if "ድንቅነሽ" in text_lower or "lucy" in text_lower or "dinknesh" in text_lower or "dinkinesh" in text_lower:
            ans_am, ans_en = OFFLINE_TRIVIA_KNOWLEDGE["lucy_dinknesh"]
            return ans_am if language == "am" else ans_en

        return None
