"""
Command Processor Module for Yakob Desktop Assistant.
Parses natural language commands in Amharic (አማርኛ) and English.
Dispatches commands to system controller, web navigation, timer, weather, news,
Alexa-style daily tools, calculator, or conversational dialogue.
"""
import re
import random
from typing import Tuple, Dict, Any, Optional, Callable

from config import (
    APPLICATION_COMMANDS,
    WEBSITE_SHORTCUTS,
    CONVERSATION_RESPONSES,
    FACTS_AM,
    FACTS_EN,
    RIDDLES_AM,
    RIDDLES_EN,
    QUOTES_AM,
    QUOTES_EN,
    ASSISTANT_NAME,
    ASSISTANT_NAME_AM
)
from core.system_controller import SystemController
from core.llm_brain import LLMBrain


class CommandProcessor:
    def __init__(
        self,
        system_controller: Optional[SystemController] = None,
        on_timer_expire_callback: Optional[Callable[[str, str], None]] = None,
        llm_brain: Optional[LLMBrain] = None
    ):
        self.sys_ctrl = system_controller or SystemController()
        self.on_timer_expire = on_timer_expire_callback
        self.llm_brain = llm_brain or LLMBrain()

    def process_command(self, raw_text: str, language: str = "am") -> Tuple[str, str, Dict[str, Any]]:
        """
        Processes spoken or typed command and returns the assistant's response.
        
        Args:
            raw_text: The user's input utterance or text.
            language: "am", "en", or "auto".
            
        Returns:
            Tuple of (spoken_response, display_text, action_metadata)
        """
        if not raw_text or not raw_text.strip():
            return "", "", {"action": "none"}

        text = raw_text.strip()
        text_lower = text.lower()

        # Detect language if auto
        if language == "auto" or language not in ["am", "en"]:
            if any('\u1200' <= c <= '\u137F' for c in text):
                detected_lang = "am"
            else:
                detected_lang = "en"
        else:
            detected_lang = language

        # -------------------------------------------------------------
        # 1. TIMERS & ALARMS INTENT (ALEXA FEATURE)
        # -------------------------------------------------------------
        timer_am = ["ታይመር", "ሰዓት ሙላ", "አላርም"]
        timer_en = ["set a timer", "set timer", "timer for", "alarm for", "start a timer"]
        if (detected_lang == "am" and any(k in text_lower for k in timer_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in timer_en)):
            seconds = self._extract_timer_duration(text_lower, detected_lang)
            if seconds:
                spoken, display = self.sys_ctrl.set_timer(
                    seconds=seconds,
                    language=detected_lang,
                    on_expire=self.on_timer_expire
                )
                return spoken, display, {"action": "timer", "seconds": seconds}
            else:
                # Default 5 min timer if unspecified
                spoken, display = self.sys_ctrl.set_timer(
                    seconds=300,
                    language=detected_lang,
                    on_expire=self.on_timer_expire
                )
                return spoken, display, {"action": "timer", "seconds": 300}

        # -------------------------------------------------------------
        # 2. WEATHER FORECAST INTENT (ALEXA FEATURE)
        # -------------------------------------------------------------
        weather_am = ["የአየር ሁኔታ", "የአየር ፀባይ", "የዛሬ የአየር", "አየር ፀባይ", "አየር ሁኔታ"]
        weather_en = ["weather", "weather forecast", "what's the weather", "temperature today", "how hot is it", "how cold is it"]
        if (detected_lang == "am" and any(k in text_lower for k in weather_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in weather_en)):
            city = self._extract_city(text_lower) or "Addis Ababa"
            spoken, display = self.sys_ctrl.get_weather(city=city, language=detected_lang)
            return spoken, display, {"action": "weather", "city": city}

        # -------------------------------------------------------------
        # 3. NEWS & HEADLINES INTENT (ALEXA FEATURE)
        # -------------------------------------------------------------
        news_am = ["የዛሬ ዜና", "ዜና ንገረኝ", "ዜናዎችን", "አዳዲስ ዜና", "ዜና"]
        news_en = ["latest news", "news headlines", "what's the news", "tell me the news", "today's news", "read the news"]
        if (detected_lang == "am" and any(k in text_lower for k in news_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in news_en)):
            spoken, display = self.sys_ctrl.get_news(language=detected_lang)
            return spoken, display, {"action": "news"}

        # -------------------------------------------------------------
        # 4. COIN FLIP & DICE ROLL (ALEXA FEATURE)
        # -------------------------------------------------------------
        coin_am = ["ሳንቲም ጣል", "ሳንቲም", "ሰው ወይስ ቁጥር"]
        coin_en = ["flip a coin", "toss a coin", "coin flip", "flip coin", "heads or tails"]
        if (detected_lang == "am" and any(k in text_lower for k in coin_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in coin_en)):
            spoken, display = self.sys_ctrl.flip_coin(language=detected_lang)
            return spoken, display, {"action": "coin_flip"}

        dice_am = ["ዳይስ ጣል", "ዳይስ"]
        dice_en = ["roll a die", "roll a dice", "roll dice", "roll die"]
        if (detected_lang == "am" and any(k in text_lower for k in dice_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in dice_en)):
            spoken, display = self.sys_ctrl.roll_dice(language=detected_lang)
            return spoken, display, {"action": "dice_roll"}

        # -------------------------------------------------------------
        # 5. FACTS & TRIVIA (ALEXA FEATURE)
        # -------------------------------------------------------------
        facts_kw_am = ["እውነታ ንገረኝ", "አስገራሚ እውነታ", "የሚገርም ነገር", "እውነታ", "አንድ እውነታ"]
        facts_kw_en = ["tell me a fact", "give me a fact", "did you know", "random fact", "interesting fact"]
        if (detected_lang == "am" and any(k in text_lower for k in facts_kw_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in facts_kw_en)):
            fact = random.choice(FACTS_AM) if detected_lang == "am" else random.choice(FACTS_EN)
            return fact, f"💡 {fact}", {"action": "fact"}

        # -------------------------------------------------------------
        # 6. RIDDLES & PUZZLES (ALEXA FEATURE)
        # -------------------------------------------------------------
        riddles_kw_am = ["እንቆቅልሽ ንገረኝ", "እንቆቅልሽ", "አጠያይቀኝ"]
        riddles_kw_en = ["tell me a riddle", "give me a riddle", "riddle me this", "say a riddle"]
        if (detected_lang == "am" and any(k in text_lower for k in riddles_kw_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in riddles_kw_en)):
            riddle, answer = random.choice(RIDDLES_AM) if detected_lang == "am" else random.choice(RIDDLES_EN)
            full_speech = f"{riddle} ... {answer}"
            display = f"🧩 {riddle}\n👉 {answer}"
            return full_speech, display, {"action": "riddle"}

        # -------------------------------------------------------------
        # 7. QUOTES & INSPIRATION (ALEXA FEATURE)
        # -------------------------------------------------------------
        quotes_kw_am = ["ጥቅስ ንገረኝ", "የዕለቱ ጥቅስ", "ጥቅስ", "አነቃቂ ንግግር"]
        quotes_kw_en = ["tell me a quote", "quote of the day", "inspire me", "motivate me", "give me a quote"]
        if (detected_lang == "am" and any(k in text_lower for k in quotes_kw_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in quotes_kw_en)):
            quote = random.choice(QUOTES_AM) if detected_lang == "am" else random.choice(QUOTES_EN)
            return quote, f"📜 {quote}", {"action": "quote"}

        # -------------------------------------------------------------
        # 8. PLAY MUSIC / SONGS (ALEXA FEATURE)
        # -------------------------------------------------------------
        play_kw_am = ["ሙዚቃ አጫውት", "ሙዚቃ ክፈት", "ዘፈን ክፈት", "ሙዚቃ ክፈትልኝ", "ዘፈን አጫውት"]
        play_kw_en = ["play music", "play song", "play some music", "play a song"]
        if (detected_lang == "am" and any(k in text_lower for k in play_kw_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in play_kw_en)):
            # Check if specific song or artist mentioned
            song_match = re.search(r'(?:play|አጫውት|ክፈትልኝ|ክፈት)\s+(.+)', text_lower)
            query = "Ethiopian music"
            if song_match:
                extracted = song_match.group(1).replace("ሙዚቃ", "").replace("ዘፈን", "").replace("music", "").strip()
                if extracted:
                    query = extracted
            self.sys_ctrl.search_youtube(query)
            resp = f"ዩቲዩብ ላይ '{query}' እየተጫወተ ነው..." if detected_lang == "am" else f"Playing '{query}' on YouTube..."
            return resp, f"🎵 {resp}", {"action": "play_music", "query": query}

        # -------------------------------------------------------------
        # 9. SCREENSHOT INTENT
        # -------------------------------------------------------------
        screenshot_am = ["ስክሪንሾት", "ስክሪኑን ፎቶ", "ፎቶ አንሳ", "ስክሪን ሾት"]
        screenshot_en = ["take screenshot", "screenshot", "capture screen", "screen shot"]
        if (detected_lang == "am" and any(p in text_lower for p in screenshot_am)) or \
           (detected_lang == "en" and any(p in text_lower for p in screenshot_en)):
            success, msg, path = self.sys_ctrl.take_screenshot()
            if success:
                resp_am = f"ስክሪንሾት ተነስቷል፤ በስዕሎች (Pictures) ማህደር ተቀምጧል።"
                resp_en = f"Screenshot captured and saved to your Pictures folder."
                reply = resp_am if detected_lang == "am" else resp_en
                return reply, f"📸 {reply} ({path})", {"action": "screenshot", "path": path}
            else:
                resp = "ስክሪንሾት ማንሳት አልተቻለም።" if detected_lang == "am" else "Failed to capture screenshot."
                return resp, resp, {"action": "screenshot", "error": msg}

        # -------------------------------------------------------------
        # 10. TIME INTENT
        # -------------------------------------------------------------
        time_am = ["ስንት ሰዓት", "ሰዓቱ ስንት", "ሰዓት ንገረኝ", "ሰዓቱን", "ሰዓት"]
        time_en = ["what time", "what's the time", "time now", "tell me the time", "current time"]
        if (detected_lang == "am" and any(p in text_lower for p in time_am)) or \
           (detected_lang == "en" and any(p in text_lower for p in time_en)):
            reply = self.sys_ctrl.get_current_time(language=detected_lang)
            return reply, f"🕒 {reply}", {"action": "time"}

        # -------------------------------------------------------------
        # 11. DATE INTENT
        # -------------------------------------------------------------
        date_am = ["ምን ቀን ነው", "ምን ቀን", "ቀኑ ስንት ነው", "የዛሬ ቀን", "ቀኑን ንገረኝ", "የዛሬውን ቀን", "ዛሬ ምን ቀን"]
        date_en = ["what date", "what is today's date", "today's date", "what day is today", "current date"]
        if (detected_lang == "am" and any(p in text_lower for p in date_am)) or \
           (detected_lang == "en" and any(p in text_lower for p in date_en)):
            reply = self.sys_ctrl.get_current_date(language=detected_lang)
            return reply, f"📅 {reply}", {"action": "date"}

        # -------------------------------------------------------------
        # 12. BATTERY / POWER INTENT
        # -------------------------------------------------------------
        battery_am = ["ባትሪ", "ቻርጅ", "የባትሪ መጠን", "ባትሪው"]
        battery_en = ["battery", "battery level", "power status", "charge level"]
        if (detected_lang == "am" and any(p in text_lower for p in battery_am)) or \
           (detected_lang == "en" and any(p in text_lower for p in battery_en)):
            reply = self.sys_ctrl.get_battery_info(language=detected_lang)
            return reply, f"🔋 {reply}", {"action": "battery"}

        # -------------------------------------------------------------
        # 13. VOLUME / MEDIA CONTROLS
        # -------------------------------------------------------------
        # Volume Up
        if (detected_lang == "am" and any(k in text_lower for k in ["ድምፅ ጨምር", "ድምፁን ጨምር", "ድምጽ ጨምር"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["volume up", "increase volume", "louder"])):
            self.sys_ctrl.change_volume("up")
            resp = "የኮምፒውተሩ ድምፅ ጨምሯል።" if detected_lang == "am" else "Volume increased."
            return resp, f"🔊 {resp}", {"action": "volume_up"}

        # Volume Down
        if (detected_lang == "am" and any(k in text_lower for k in ["ድምፅ ቀንስ", "ድምፁን ቀንስ", "ድምጽ ቀንስ"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["volume down", "decrease volume", "lower volume", "quieter"])):
            self.sys_ctrl.change_volume("down")
            resp = "የኮምፒውተሩ ድምፅ ቀንሷል።" if detected_lang == "am" else "Volume decreased."
            return resp, f"🔉 {resp}", {"action": "volume_down"}

        # Mute / Unmute
        if (detected_lang == "am" and any(k in text_lower for k in ["ድምፅ አጥፋ", "ድምፅ ዝጋ", "ድምፁን አጥፋ", "ድምጽ አጥፋ"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["mute", "unmute", "silence volume"])):
            self.sys_ctrl.change_volume("mute")
            resp = "የኮምፒውተሩ ድምፅ ተዘግቷል / ተከፍቷል።" if detected_lang == "am" else "Volume muted/unmuted."
            return resp, f"🔇 {resp}", {"action": "volume_mute"}

        # -------------------------------------------------------------
        # 14. LOCK WORKSTATION
        # -------------------------------------------------------------
        if (detected_lang == "am" and any(k in text_lower for k in ["ኮምፒውተሩን ቆልፍ", "ስክሪኑን ቆልፍ", "ቆልፍ"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["lock pc", "lock computer", "lock screen", "lock workstation"])):
            resp = "ኮምፒውተሩን እየቆለፍኩ ነው።" if detected_lang == "am" else "Locking your computer."
            self.sys_ctrl.lock_pc()
            return resp, f"🔒 {resp}", {"action": "lock_pc"}

        # -------------------------------------------------------------
        # 15. WEB SEARCH & YOUTUBE INTENT
        # -------------------------------------------------------------
        yt_search_match = re.search(r'(?:youtube\s+(?:ላይ|search|for)|ዩቲዩብ\s+ላይ)\s+(.+)', text_lower)
        if yt_search_match:
            query = yt_search_match.group(1).replace("ፈልግ", "").replace("search", "").strip()
            if query:
                self.sys_ctrl.search_youtube(query)
                resp = f"ዩቲዩብ ላይ '{query}' እየተፈለገ ነው..." if detected_lang == "am" else f"Searching YouTube for '{query}'..."
                return resp, f"▶️ {resp}", {"action": "youtube_search", "query": query}

        # Google Web Search
        search_am_match = re.search(r'(?:ስለ|በጎግል|ጎግል ላይ|ኢንተርኔት ላይ)?\s*(.+?)\s*(?:ፈልግ|ፈልግልኝ|ፈልጊ)', text_lower)
        if detected_lang == "am" and search_am_match and "ክፈት" not in text_lower:
            query = search_am_match.group(1).replace("ስለ", "").replace("ጎግል", "").strip()
            if len(query) > 1 and not any(k in query for k in ["ቀልድ", "ሰዓት", "ቀን", "ባትሪ", "ታይመር"]):
                self.sys_ctrl.search_google(query)
                resp = f"ኢንተርኔት ላይ ስለ '{query}' እየፈለግኩ ነው..."
                return resp, f"🔍 {resp}", {"action": "google_search", "query": query}

        search_en_match = re.search(r'(?:search for|google search|search on google|look up)\s+(.+)', text_lower)
        if search_en_match:
            query = search_en_match.group(1).strip()
            self.sys_ctrl.search_google(query)
            resp = f"Searching the web for '{query}'..."
            return resp, f"🔍 {resp}", {"action": "google_search", "query": query}

        # -------------------------------------------------------------
        # 16. OPEN APPLICATION OR WEBSITE INTENT
        # -------------------------------------------------------------
        open_verbs_am = ["ክፈት", "ክፈተው", "ክፈቺ", "ክፈትልኝ", "አስጀምር", "አስነሳ"]
        open_verbs_en = ["open", "launch", "start", "run", "bring up"]
        is_open_intent = any(v in text_lower for v in open_verbs_am) or any(v in text_lower for v in open_verbs_en)

        # First check registered websites
        for site_key, site_info in WEBSITE_SHORTCUTS.items():
            for alias in site_info["aliases"]:
                if alias.lower() in text_lower:
                    success, msg = self.sys_ctrl.open_website(site_key)
                    site_title = site_key.title()
                    resp = f"{site_title}ን እየከፈትኩ ነው..." if detected_lang == "am" else f"Opening {site_title}..."
                    return resp, f"🌐 {resp}", {"action": "open_website", "target": site_key}

        # Check registered applications
        for app_key, app_info in APPLICATION_COMMANDS.items():
            for alias in app_info["aliases"]:
                if alias.lower() in text_lower:
                    success, msg = self.sys_ctrl.open_application(app_key)
                    app_title = app_key.title()
                    if success:
                        resp = f"{app_title}ን እየከፈትኩ ነው..." if detected_lang == "am" else f"Opening {app_title}..."
                        return resp, f"🚀 {resp}", {"action": "open_app", "app": app_key}
                    else:
                        resp = f"{app_title}ን መክፈት አልተቻለም።" if detected_lang == "am" else f"Could not launch {app_title}."
                        return resp, f"⚠️ {resp} ({msg})", {"action": "open_app", "error": msg}

        # Generic open app fallback
        if is_open_intent:
            target_name = text_lower
            for v in open_verbs_am + open_verbs_en:
                target_name = target_name.replace(v, "")
            target_name = target_name.strip()
            
            if target_name:
                success, msg = self.sys_ctrl.open_application(target_name)
                if success:
                    resp = f"'{target_name}' እየተከፈተ ነው..." if detected_lang == "am" else f"Opening '{target_name}'..."
                    return resp, f"🚀 {resp}", {"action": "open_custom_app", "target": target_name}

        # -------------------------------------------------------------
        # 16. SMART CLIPBOARD & TEXT TOOLS
        # -------------------------------------------------------------
        t = text_lower
        if any(w in t for w in ["ኮፒ", "ክሊፕቦርድ", "ጽሑፌን አንብብ", "clipboard", "read my copied", "read what i copied"]):
            clip = self.sys_ctrl.get_clipboard_text()
            if clip:
                preview = clip if len(clip) <= 200 else (clip[:200] + "...")
                resp = f"የኮፒ ያደረጉት ጽሑፍ ይህ ነው፡ {preview}" if detected_lang == "am" else f"Here is your copied text: {preview}"
                return resp, f"📋 {resp}", {"action": "read_clipboard", "text": clip}
            else:
                resp = "በክሊፕቦርዱ ላይ ምንም ጽሑፍ አልተገኘም።" if detected_lang == "am" else "No text found in your clipboard."
                return resp, f"📋 {resp}", {"action": "read_clipboard", "status": "empty"}

        # -------------------------------------------------------------
        # 17. MATH EVALUATION INTENT
        # -------------------------------------------------------------
        math_result = self._evaluate_spoken_math(text_lower, detected_lang)
        if math_result:
            spoken_math, display_math = math_result
            return spoken_math, display_math, {"action": "math"}

        # -------------------------------------------------------------
        # 18. CONVERSATIONAL & SOCIAL INTENTS
        # -------------------------------------------------------------
        # Good Morning
        if (detected_lang == "am" and any(k in text_lower for k in ["እንደምን አደርክ", "ደህና አደርክ", "እንደምን አደሩ", "ደህና አደሩ"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["good morning", "morning"])):
            reply = random.choice(CONVERSATION_RESPONSES["good_morning"][detected_lang])
            return reply, f"🌅 {reply}", {"action": "conversation", "topic": "good_morning"}

        # Good Night
        if (detected_lang == "am" and any(k in text_lower for k in ["ደህና እደር", "ደህና እደሩ", "መልካም አዳር", "ደህና ሁን"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["good night", "sweet dreams", "goodnight", "bye for now"])):
            reply = random.choice(CONVERSATION_RESPONSES["good_night"][detected_lang])
            return reply, f"🌙 {reply}", {"action": "conversation", "topic": "good_night"}

        # Sing a song
        if (detected_lang == "am" and any(k in text_lower for k in ["ዘፈን ዘፍን", "ዘምር", "ዘፍንልኝ", "አዝፍን"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["sing a song", "can you sing", "sing for me"])):
            reply = random.choice(CONVERSATION_RESPONSES["sing"][detected_lang])
            return reply, f"🎤 {reply}", {"action": "conversation", "topic": "sing"}

        # Creator / Who made you
        if (detected_lang == "am" and any(k in text_lower for k in ["ማን ፈጠረህ", "ማን ሰራህ", "ማን አበለጸገህ"])) or \
           (detected_lang == "en" and any(k in text_lower for k in ["who made you", "who created you", "who built you"])):
            reply = random.choice(CONVERSATION_RESPONSES["creator"][detected_lang])
            return reply, f"👨‍💻 {reply}", {"action": "conversation", "topic": "creator"}

        # Greetings
        greetings_am = ["ሰላም", "እንደምን ዋላችሁ", "ጤና ይስጥልኝ", "ሀይ", "ታዲያስ", "ሰላም ነው"]
        greetings_en = ["hello", "hi", "hey", "good afternoon", "good evening", "greetings"]
        if (detected_lang == "am" and any(g in text_lower for g in greetings_am)) or \
           (detected_lang == "en" and any(g in text_lower for g in greetings_en)):
            reply = random.choice(CONVERSATION_RESPONSES["greetings"][detected_lang])
            return reply, f"👋 {reply}", {"action": "conversation", "topic": "greeting"}

        # Identity / Who are you
        identity_am = ["ማን ነህ", "ስምህ ማን", "ምን አይነት ቦት ነህ", "ራስህን አስተዋውቅ", "ማን ነሽ"]
        identity_en = ["who are you", "what is your name", "what are you", "introduce yourself"]
        if (detected_lang == "am" and any(k in text_lower for k in identity_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in identity_en)):
            reply = random.choice(CONVERSATION_RESPONSES["identity"][detected_lang])
            return reply, f"🤖 {reply}", {"action": "conversation", "topic": "identity"}

        # Status / How are you
        status_am = ["እንዴት ነህ", "ደህና ነህ", "እንደምን አለህ", "እንዴት ነሽ"]
        status_en = ["how are you", "how are you doing", "how is it going", "are you okay"]
        if (detected_lang == "am" and any(k in text_lower for k in status_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in status_en)):
            reply = random.choice(CONVERSATION_RESPONSES["status"][detected_lang])
            return reply, f"✨ {reply}", {"action": "conversation", "topic": "status"}

        # Thanks
        thanks_am = ["አመሰግናለሁ", "እናመሰግናለን", "እግዜር ይስጥልኝ", "ክበርልኝ"]
        thanks_en = ["thank you", "thanks", "appreciate it", "thank you so much"]
        if (detected_lang == "am" and any(k in text_lower for k in thanks_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in thanks_en)):
            reply = random.choice(CONVERSATION_RESPONSES["thanks"][detected_lang])
            return reply, f"🙏 {reply}", {"action": "conversation", "topic": "thanks"}

        # Jokes
        jokes_am = ["ቀልድ ንገረኝ", "ቀልድ አጫውተኝ", "አስቀኝ", "ቀልድ"]
        jokes_en = ["tell me a joke", "tell a joke", "make me laugh", "say a joke"]
        if (detected_lang == "am" and any(k in text_lower for k in jokes_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in jokes_en)):
            reply = random.choice(CONVERSATION_RESPONSES["jokes"][detected_lang])
            return reply, f"😄 {reply}", {"action": "conversation", "topic": "joke"}

        # Help / Capabilities
        help_am = ["እርዳታ", "ምን ትችላለህ", "ምን መስራት ትችላለህ", "ትእዛዞች", "ትዕዛዞች"]
        help_en = ["help", "what can you do", "commands", "features", "how to use", "what are the commands"]
        if (detected_lang == "am" and any(k in text_lower for k in help_am)) or \
           (detected_lang == "en" and any(k in text_lower for k in help_en)):
            reply = random.choice(CONVERSATION_RESPONSES["help"][detected_lang])
            return reply, f"💡 {reply}", {"action": "conversation", "topic": "help"}

        # -------------------------------------------------------------
        # 19. TRIVIA & LLM CONVERSATIONAL GENERATION
        # -------------------------------------------------------------
        # Check LLM / Offline Trivia Engine (Gemini 2.5 Flash / Groq / Curated Trivia Knowledge)
        trivia_or_llm_answer = self.llm_brain.answer_trivia_or_chat(raw_text, language=detected_lang)
        if trivia_or_llm_answer:
            return trivia_or_llm_answer, f"💡 {trivia_or_llm_answer}", {"action": "trivia_or_llm"}

        fallback = random.choice(CONVERSATION_RESPONSES["unknown"][detected_lang])
        return fallback, f"❓ {fallback}", {"action": "unknown"}

    def _extract_timer_duration(self, text: str, language: str) -> Optional[int]:
        """Extracts timer seconds from spoken text (e.g. 5 minutes, 30 seconds)."""
        # Look for numbers with minutes or seconds
        # Amharic: "የ 5 ደቂቃ", "10 ሰከንድ", "1 ሰዓት"
        min_match_am = re.search(r'(\d+)\s*ደቂቃ', text)
        sec_match_am = re.search(r'(\d+)\s*ሰከንድ', text)
        hr_match_am = re.search(r'(\d+)\s*ሰዓት', text)

        # English: "5 minutes", "10 seconds", "1 hour"
        min_match_en = re.search(r'(\d+)\s*(?:min|minute)', text)
        sec_match_en = re.search(r'(\d+)\s*(?:sec|second)', text)
        hr_match_en = re.search(r'(\d+)\s*(?:hour|hr)', text)

        total_secs = 0
        if hr_match_am:
            total_secs += int(hr_match_am.group(1)) * 3600
        elif hr_match_en:
            total_secs += int(hr_match_en.group(1)) * 3600

        if min_match_am:
            total_secs += int(min_match_am.group(1)) * 60
        elif min_match_en:
            total_secs += int(min_match_en.group(1)) * 60

        if sec_match_am:
            total_secs += int(sec_match_am.group(1))
        elif sec_match_en:
            total_secs += int(sec_match_en.group(1))

        # Direct single number fallback if text has "timer" and a number
        if total_secs == 0:
            num_match = re.search(r'\b(\d+)\b', text)
            if num_match:
                # Default to minutes if under 60, otherwise seconds
                val = int(num_match.group(1))
                total_secs = val * 60 if val <= 60 else val

        return total_secs if total_secs > 0 else None

    def _extract_city(self, text: str) -> Optional[str]:
        """Extracts city name for weather lookups."""
        cities = {
            "addis ababa": "Addis Ababa",
            "አዲስ አበባ": "Addis Ababa",
            "hawassa": "Hawassa",
            "ሐዋሳ": "Hawassa",
            "bahir dar": "Bahir Dar",
            "ባህር ዳር": "Bahir Dar",
            "gondar": "Gondar",
            "ጎንደር": "Gondar",
            "mekelle": "Mekelle",
            "መቀሌ": "Mekelle",
            "adama": "Adama",
            "አዳማ": "Adama",
            "dire dawa": "Dire Dawa",
            "ድሬዳዋ": "Dire Dawa",
            "london": "London",
            "new york": "New York",
            "dubai": "Dubai",
            "nairobi": "Nairobi",
            "washington": "Washington"
        }
        for alias, name in cities.items():
            if alias in text:
                return name
        return None

    def _evaluate_spoken_math(self, text: str, language: str) -> Optional[Tuple[str, str]]:
        """Evaluates spoken simple arithmetic operations."""
        math_str = text
        math_str = math_str.replace("ሲደመር", "+").replace("plus", "+").replace("add", "+")
        math_str = math_str.replace("ሲቀነስ", "-").replace("minus", "-").replace("subtract", "-")
        math_str = math_str.replace("ሲባዛ በ", "*").replace("ሲባዛ", "*").replace("times", "*").replace("multiplied by", "*")
        math_str = math_str.replace("ሲካፈል ለ", "/").replace("ሲካፈል", "/").replace("divided by", "/")
        math_str = math_str.replace("ስንት ነው", "").replace("what is", "").replace("calculate", "")
        
        match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)', math_str)
        if match:
            num1 = float(match.group(1))
            op = match.group(2)
            num2 = float(match.group(3))
            
            res = 0.0
            if op == "+":
                res = num1 + num2
            elif op == "-":
                res = num1 - num2
            elif op == "*":
                res = num1 * num2
            elif op == "/":
                if num2 == 0:
                    resp = "ለዜሮ ማካፈል አይቻልም።" if language == "am" else "Cannot divide by zero."
                    return resp, f"⚠️ {resp}"
                res = num1 / num2
                
            res_str = str(int(res)) if res.is_integer() else f"{res:.2f}"
            
            if language == "am":
                spoken = f"መልሱ {res_str} ነው።"
            else:
                spoken = f"The answer is {res_str}."
                
            display = f"🧮 {num1:g} {op} {num2:g} = {res_str}"
            return spoken, display

        return None
