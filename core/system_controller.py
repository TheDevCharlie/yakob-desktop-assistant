"""
System Controller Module
Provides system automation for Windows:
- Application launching (Chrome, Notepad, Calc, Explorer, VS Code, etc.)
- Web actions (Google/YouTube search, opening websites)
- Timers & Alarms with audio notification callbacks
- Real-time weather queries
- News headlines lookup
- Interactive tools (Coin Flip, Dice Roll)
- Volume & Media controls via Windows API key events
- Screenshots & Battery/Power info
- Workstation Lock & Time/Date retrieval in Amharic & English
"""
import os
import sys
import json
import random
import ctypes
import datetime
import threading
import subprocess
import webbrowser
import urllib.request
from typing import Optional, Tuple, Callable
from pathlib import Path

from config import APPLICATION_COMMANDS, WEBSITE_SHORTCUTS

# Windows Virtual Key Codes for Media & Volume Control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


class SystemController:
    def __init__(self):
        self.pictures_dir = Path(os.path.expanduser("~")) / "Pictures"
        self.pictures_dir.mkdir(parents=True, exist_ok=True)
        self.active_timers = []
        self._lock = threading.Lock()

    def get_clipboard_text(self) -> Optional[str]:
        """Reads text currently stored on Windows clipboard."""
        try:
            import pyperclip
            text = pyperclip.paste()
            if text and text.strip():
                return text.strip()
        except Exception as e:
            print(f"[SystemController] Clipboard error: {e}")
        return None

    def open_application(self, app_key_or_name: str) -> Tuple[bool, str]:
        """Launches an application by key, alias, or executable command."""
        app_name_lower = app_key_or_name.strip().lower()

        # 1. Match against registered application table in config
        for key, info in APPLICATION_COMMANDS.items():
            if app_name_lower == key or app_name_lower in [alias.lower() for alias in info["aliases"]]:
                for fallback in info.get("path_fallbacks", []):
                    if os.path.exists(fallback):
                        try:
                            subprocess.Popen(f'"{fallback}"', shell=True)
                            return True, f"Launched {key.title()} from path."
                        except Exception:
                            pass
                
                cmd = info["command"]
                try:
                    if cmd.startswith("start "):
                        subprocess.Popen(cmd, shell=True)
                    else:
                        subprocess.Popen(f'start "" "{cmd}"', shell=True)
                    return True, f"Launched {key.title()}."
                except Exception as e:
                    return False, f"Failed to launch {key}: {e}"

        # 2. Try launching arbitrary command directly via Windows start
        try:
            subprocess.Popen(f'start "" "{app_key_or_name}"', shell=True)
            return True, f"Launched '{app_key_or_name}'."
        except Exception as e:
            return False, f"Could not launch '{app_key_or_name}': {e}"

    def open_website(self, site_key_or_url: str) -> Tuple[bool, str]:
        """Opens a website URL in the default browser."""
        target_lower = site_key_or_url.strip().lower()

        for key, info in WEBSITE_SHORTCUTS.items():
            if target_lower == key or target_lower in [alias.lower() for alias in info["aliases"]]:
                webbrowser.open(info["url"])
                return True, f"Opened {key.title()} ({info['url']})."

        if target_lower.startswith("http://") or target_lower.startswith("https://"):
            webbrowser.open(site_key_or_url)
            return True, f"Opened {site_key_or_url}."
        elif "." in target_lower and " " not in target_lower:
            webbrowser.open(f"https://{site_key_or_url}")
            return True, f"Opened https://{site_key_or_url}."

        search_url = f"https://www.google.com/search?q={target_lower}"
        webbrowser.open(search_url)
        return True, f"Searched Google for '{site_key_or_url}'."

    def search_youtube(self, query: str) -> Tuple[bool, str]:
        """Performs a YouTube search or plays music."""
        url = f"https://www.youtube.com/results?search_query={query.strip()}"
        webbrowser.open(url)
        return True, f"Searched YouTube for '{query}'."

    def search_google(self, query: str) -> Tuple[bool, str]:
        """Performs a Google search."""
        url = f"https://www.google.com/search?q={query.strip()}"
        webbrowser.open(url)
        return True, f"Searched Google for '{query}'."

    # -----------------------------------------------------------------
    # TIMERS & ALARMS
    # -----------------------------------------------------------------
    def set_timer(
        self,
        seconds: int,
        label: str = "Timer",
        language: str = "am",
        on_expire: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[str, str]:
        """
        Schedules a background timer.
        """
        if seconds <= 0:
            err = "የታይመር ሰዓቱ ከዜሮ በላይ መሆን አለበት።" if language == "am" else "Timer duration must be greater than zero."
            return err, f"⚠️ {err}"

        # Format duration string
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        
        time_parts_am = []
        time_parts_en = []
        if hours > 0:
            time_parts_am.append(f"{hours} ሰዓት")
            time_parts_en.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if mins > 0:
            time_parts_am.append(f"{mins} ደቂቃ")
            time_parts_en.append(f"{mins} minute{'s' if mins > 1 else ''}")
        if secs > 0 or not time_parts_am:
            time_parts_am.append(f"{secs} ሰከንድ")
            time_parts_en.append(f"{secs} second{'s' if secs > 1 else ''}")

        dur_str_am = " ከ ".join(time_parts_am)
        dur_str_en = ", ".join(time_parts_en)

        def _timer_worker():
            # Beep alert sound using Windows winsound / ctypes
            try:
                import winsound
                winsound.Beep(1000, 400)
                winsound.Beep(1200, 400)
                winsound.Beep(1500, 600)
            except Exception:
                pass

            expire_am = f"⏰ የ {dur_str_am} ታይመር አልቋል!"
            expire_en = f"⏰ Your {dur_str_en} timer is up!"
            
            if on_expire:
                on_expire(expire_am if language == "am" else expire_en, dur_str_am if language == "am" else dur_str_en)

        t = threading.Timer(float(seconds), _timer_worker)
        t.daemon = True
        t.start()
        self.active_timers.append(t)

        if language == "am":
            spoken = f"የ {dur_str_am} ታይመር ተሞልቷል። ሰዓቱ ሲደርስ አሳውቅዎታለሁ።"
            display = f"⏱️ የ {dur_str_am} ታይመር ተጀምሯል..."
        else:
            spoken = f"Timer set for {dur_str_en}. I will notify you when it's up."
            display = f"⏱️ Timer started for {dur_str_en}..."

        return spoken, display

    # -----------------------------------------------------------------
    # WEATHER INFORMATION
    # -----------------------------------------------------------------
    def get_weather(self, city: str = "Addis Ababa", language: str = "am") -> Tuple[str, str]:
        """Retrieves real-time weather information."""
        city_encoded = city.strip().replace(" ", "_")
        try:
            url = f"https://wttr.in/{city_encoded}?format=j1"
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode())
                curr = data['current_condition'][0]
                temp_c = curr.get('temp_C', 'N/A')
                desc_en = curr.get('weatherDesc', [{'value': 'Clear'}])[0]['value']
                humidity = curr.get('humidity', 'N/A')
                feels_like = curr.get('FeelsLikeC', temp_c)

                # Amharic translations for common weather conditions
                weather_map_am = {
                    "Sunny": "ፀሐያማ",
                    "Clear": "ጥርት ያለ",
                    "Partly cloudy": "በከፊል ደመናማ",
                    "Cloudy": "ደመናማ",
                    "Overcast": "የተጋረደ ደመና",
                    "Mist": "ጉም",
                    "Fog": "ብርቱ ጉም",
                    "Light rain": "ቀላል ዝናብ",
                    "Moderate rain": "መጠነኛ ዝናብ",
                    "Heavy rain": "ከባድ ዝናብ",
                    "Thunderstorm": "ነጎድጓዳማ ዝናብ",
                    "Patchy rain possible": "አነስተኛ ዝናብ ሊኖር ይችላል"
                }
                desc_am = weather_map_am.get(desc_en, desc_en)

                if language == "am":
                    city_display = "በአዲስ አበባ" if "addis" in city.lower() else f"በ{city}"
                    spoken = f"አሁን {city_display} የሙቀት መጠኑ {temp_c} ዲግሪ ሴልሺየስ ሲሆን፣ የአየር ሁኔታው {desc_am} ነው።"
                    display = f"☀️ {city.title()} የአየር ሁኔታ: {temp_c}°C ({desc_am}), እርጥበት: {humidity}%"
                else:
                    spoken = f"Currently in {city.title()}, it's {temp_c} degrees Celsius with {desc_en} conditions."
                    display = f"☀️ Weather in {city.title()}: {temp_c}°C ({desc_en}), Humidity: {humidity}%, Feels like: {feels_like}°C"

                return spoken, display
        except Exception as e:
            # Fallback to browser search
            self.search_google(f"weather in {city}")
            if language == "am":
                spoken = f"የ{city}ን የአየር ሁኔታ ኢንተርኔት ላይ እየፈለግኩ ነው።"
                display = f"☀️ የ{city} የአየር ሁኔታ በብሮውዘር ተከፍቷል።"
            else:
                spoken = f"Opening weather forecast for {city} in your browser."
                display = f"☀️ Opened weather forecast for {city} in browser."
            return spoken, display

    # -----------------------------------------------------------------
    # NEWS HEADLINES
    # -----------------------------------------------------------------
    def get_news(self, language: str = "am") -> Tuple[str, str]:
        """Opens top news or provides latest headlines."""
        if language == "am":
            webbrowser.open("https://news.google.com?hl=am")
            spoken = "የወቅቱን አዳዲስ ዜናዎች በጎግል ዜና እየከፈትኩ ነው።"
            display = "📰 የቅርብ ጊዜ ዜናዎች በብሮውዘር ተከፍተዋል።"
        else:
            webbrowser.open("https://news.google.com")
            spoken = "Opening the latest news headlines on Google News."
            display = "📰 Opened latest news headlines in your browser."
        return spoken, display

    # -----------------------------------------------------------------
    # CASUAL ALEXA UTILITIES (COIN FLIP, DICE ROLL)
    # -----------------------------------------------------------------
    def flip_coin(self, language: str = "am") -> Tuple[str, str]:
        """Simulates flipping a coin."""
        outcome = random.choice(["heads", "tails"])
        if language == "am":
            result_am = "ሰው (Heads)" if outcome == "heads" else "ቁጥር (Tails)"
            spoken = f"ሳንቲሙ ተጥሎ {result_am} ወጥቷል!"
            display = f"🪙 ሳንቲም ጣል: {result_am}"
        else:
            result_en = "Heads" if outcome == "heads" else "Tails"
            spoken = f"I flipped a coin and it landed on {result_en}!"
            display = f"🪙 Coin Flip Result: {result_en}"
        return spoken, display

    def roll_dice(self, language: str = "am") -> Tuple[str, str]:
        """Simulates rolling a 6-sided die."""
        number = random.randint(1, 6)
        if language == "am":
            spoken = f"ዳይሱ ተጥሎ {number} ወጥቷል!"
            display = f"🎲 ዳይስ ጣል: {number}"
        else:
            spoken = f"I rolled the dice and got a {number}!"
            display = f"🎲 Dice Roll Result: {number}"
        return spoken, display

    # -----------------------------------------------------------------
    # HARDWARE & WINDOWS SYSTEM CONTROLS
    # -----------------------------------------------------------------
    def take_screenshot(self) -> Tuple[bool, str, Optional[str]]:
        """Takes a desktop screenshot and saves it to the user's Pictures folder."""
        try:
            from PIL import ImageGrab
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.pictures_dir / f"Screenshot_{timestamp}.png"
            screenshot = ImageGrab.grab()
            screenshot.save(file_path, "PNG")
            return True, f"Screenshot saved to {file_path.name}", str(file_path)
        except Exception as e:
            return False, f"Screenshot failed: {e}", None

    def change_volume(self, action: str) -> Tuple[bool, str]:
        """Adjusts Windows master volume (up, down, mute)."""
        try:
            if action == "up":
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_KEYUP, 0)
                return True, "Volume increased."
            elif action == "down":
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_KEYUP, 0)
                return True, "Volume decreased."
            elif action == "mute":
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
                return True, "Volume muted / unmuted."
            return False, "Unknown volume action."
        except Exception as e:
            return False, f"Volume adjustment error: {e}"

    def lock_pc(self) -> Tuple[bool, str]:
        """Locks the Windows workstation."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "PC Locked."
        except Exception as e:
            return False, f"Lock failed: {e}"

    def get_battery_info(self, language: str = "am") -> str:
        """Retrieves system battery percentage and charging state."""
        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ('ACLineStatus', ctypes.c_byte),
                ('BatteryFlag', ctypes.c_byte),
                ('BatteryLifePercent', ctypes.c_byte),
                ('Reserved1', ctypes.c_byte),
                ('BatteryLifeTime', ctypes.c_ulong),
                ('BatteryFullLifeTime', ctypes.c_ulong)
            ]

        try:
            status = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                percent = status.BatteryLifePercent
                is_plugged = status.ACLineStatus == 1
                
                if percent == 255:
                    if language == "am":
                        return "ይህ ኮምፒውተር ባትሪ የለውም (ቀጥታ ከኤሌክትሪክ የተገናኘ ነው)።"
                    return "No battery detected (Desktop connected to AC power)."
                    
                plugged_str_am = "ከቻርጀር ጋር ተገናኝቷል" if is_plugged else "በባትሪ እየሰራ ነው"
                plugged_str_en = "Plugged in (Charging)" if is_plugged else "On battery power"
                
                if language == "am":
                    return f"የባትሪው መጠን {percent}% ሲሆን {plugged_str_am}።"
                return f"Battery level is {percent}%, {plugged_str_en}."
        except Exception:
            pass

        if language == "am":
            return "የባትሪውን መረጃ ማግኘት አልተቻለም።"
        return "Could not retrieve battery information."

    def get_current_time(self, language: str = "am") -> str:
        """Returns the current formatted time."""
        now = datetime.datetime.now()
        hour = now.strftime("%I").lstrip("0")
        minute = now.strftime("%M")
        period = now.strftime("%p")
        
        if language == "am":
            period_am = "ከጠዋቱ" if period == "AM" else "ከቀትር በኋላ"
            if int(hour) >= 6 and period == "PM":
                period_am = "ከምሽቱ"
            return f"አሁን ሰዓቱ {period_am} {hour} ሰዓት ከ {minute} ደቂቃ ነው።"
        return f"The current time is {hour}:{minute} {period}."

    def get_current_date(self, language: str = "am") -> str:
        """Returns the current date formatted."""
        now = datetime.datetime.now()
        
        days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        days_am = ["ሰኞ", "ማክሰኞ", "ረቡዕ", "ሐሙስ", "አርብ", "ቅዳሜ", "እሁድ"]
        months_am = ["ጃንዋሪ", "ፌብሩዋሪ", "ማርች", "ኤፕሪል", "ሜይ", "ጁን", "ጁላይ", "ኦገስት", "ሴፕቴምበር", "ኦክቶበር", "ኖቬምበር", "ዲሴምበር"]
        
        day_idx = now.weekday()
        month_idx = now.month - 1
        
        if language == "am":
            return f"ዛሬ {days_am[day_idx]}፣ {months_am[month_idx]} {now.day}፣ {now.year} ዓ.ም ነው።"
        return f"Today is {days_en[day_idx]}, {months_en[month_idx]} {now.day}, {now.year}."
