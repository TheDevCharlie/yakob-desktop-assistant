"""
Graphical User Interface for Yakob Desktop Assistant.
Built with CustomTkinter for a modern, responsive, dark-themed experience.
"""
import time
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import customtkinter as ctk

from config import (
    ASSISTANT_NAME,
    ASSISTANT_NAME_AM,
    ASSISTANT_VERSION,
    VOICE_CONFIG,
    DEFAULT_LANGUAGE
)
from core.audio_recorder import AudioRecorder
from core.speech_recognizer import SpeechRecognizer
from core.tts_engine import TTSEngine
from core.command_processor import CommandProcessor
from core.system_controller import SystemController

# Set CustomTkinter theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize Core Services
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.tts_engine = TTSEngine()
        self.sys_controller = SystemController()
        self.command_processor = CommandProcessor(
            system_controller=self.sys_controller,
            on_timer_expire_callback=self._on_timer_expired
        )

        # State Variables - Default to MALE voices
        self.current_language = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.current_voice = tk.StringVar(value=VOICE_CONFIG["am"]["male"])
        self.speech_rate = tk.StringVar(value="+0%")
        self.is_continuous = tk.BooleanVar(value=False)
        self.status_state = "idle"
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_listening = False
        self._msg_queue = queue.Queue()

        # Window Setup
        self.title(f"{ASSISTANT_NAME} ({ASSISTANT_NAME_AM}) - Multilingual Desktop Assistant")
        self.geometry("920x740")
        self.minsize(800, 620)

        # Build UI
        self._create_layout()
        self._process_queue()

        # Initial Welcome Greeting in Male Voice
        self.after(500, self._initial_greeting)

    def _create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # LEFT SIDEBAR - CONTROLS & MALE VOICE SETTINGS
        # -------------------------------------------------------------
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(12, weight=1)

        # App Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=f"🎙️ {ASSISTANT_NAME} ({ASSISTANT_NAME_AM})",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=15, pady=(20, 2), sticky="w")

        self.sub_label = ctk.CTkLabel(
            self.sidebar,
            text="Desktop Voice Assistant (Male Voice)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="gray70"
        )
        self.sub_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        # Language Selection Section
        self.lang_header = ctk.CTkLabel(
            self.sidebar,
            text="ቋንቋ / Language:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.lang_header.grid(row=2, column=0, padx=15, pady=(5, 5), sticky="w")

        self.lang_seg = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["አማርኛ (Amharic)", "English", "Auto (ሁለቱም)"],
            command=self._on_language_changed
        )
        self.lang_seg.set("አማርኛ (Amharic)")
        self.lang_seg.grid(row=3, column=0, padx=15, pady=(0, 12), sticky="ew")

        # Voice Selector (Default to Male voices)
        self.voice_header = ctk.CTkLabel(
            self.sidebar,
            text="የድምፅ ምርጫ / Voice:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.voice_header.grid(row=4, column=0, padx=15, pady=(5, 5), sticky="w")

        self.voice_option = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "Ameha (Amharic Male)",
                "Guy (English Male)",
                "Mekdes (Amharic Female)",
                "Jenny (English Female)"
            ],
            command=self._on_voice_changed
        )
        self.voice_option.set("Ameha (Amharic Male)")
        self.voice_option.grid(row=5, column=0, padx=15, pady=(0, 12), sticky="ew")

        # Voice Speed Slider
        self.speed_header = ctk.CTkLabel(
            self.sidebar,
            text="የንግግር ፍጥነት / Speed:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.speed_header.grid(row=6, column=0, padx=15, pady=(5, 5), sticky="w")

        self.speed_slider = ctk.CTkSlider(
            self.sidebar,
            from_=-30,
            to=30,
            number_of_steps=12,
            command=self._on_speed_changed
        )
        self.speed_slider.set(0)
        self.speed_slider.grid(row=7, column=0, padx=15, pady=(0, 12), sticky="ew")

        # Mode Options
        self.continuous_switch = ctk.CTkSwitch(
            self.sidebar,
            text="ተከታታይ ማዳመጥ\n(Continuous Listen)",
            variable=self.is_continuous,
            command=self._on_continuous_toggle
        )
        self.continuous_switch.grid(row=8, column=0, padx=15, pady=(5, 12), sticky="w")

        # Quick Test Audio Buttons
        self.test_am_btn = ctk.CTkButton(
            self.sidebar,
            text="🔊 የአማርኛ ወንድ ድምፅ ሞክር",
            fg_color="#2b5b84",
            hover_color="#1c3e5a",
            command=lambda: self._test_voice("am")
        )
        self.test_am_btn.grid(row=9, column=0, padx=15, pady=(4, 4), sticky="ew")

        self.test_en_btn = ctk.CTkButton(
            self.sidebar,
            text="🔊 Test English Male Voice",
            fg_color="#2b5b84",
            hover_color="#1c3e5a",
            command=lambda: self._test_voice("en")
        )
        self.test_en_btn.grid(row=10, column=0, padx=15, pady=(4, 8), sticky="ew")

        # Stop Speaking & Clear Log Buttons
        self.stop_tts_btn = ctk.CTkButton(
            self.sidebar,
            text="⏹️ ንግግር አቁም (Stop Speech)",
            fg_color="#913d3d",
            hover_color="#6e2e2e",
            command=self._stop_tts
        )
        self.stop_tts_btn.grid(row=11, column=0, padx=15, pady=(4, 4), sticky="ew")

        self.clear_btn = ctk.CTkButton(
            self.sidebar,
            text="🗑️ ታሪክ አጽዳ (Clear Log)",
            fg_color="#3a3a3a",
            hover_color="#2a2a2a",
            command=self._clear_chat
        )
        self.clear_btn.grid(row=12, column=0, padx=15, pady=(4, 15), sticky="ew")

        # -------------------------------------------------------------
        # RIGHT MAIN PANEL - CONVERSATION & CONTROLS
        # -------------------------------------------------------------
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header Status Banner
        self.header_card = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.header_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.header_card.grid_columnconfigure(1, weight=1)

        # Pulsing Mic Button in Header
        self.mic_btn = ctk.CTkButton(
            self.header_card,
            text="🎙️ ለመናገር ይጫኑ\n(Click to Talk)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            width=180,
            height=58,
            corner_radius=28,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._toggle_listening
        )
        self.mic_btn.grid(row=0, column=0, padx=15, pady=12)

        # Status Indicator & Label
        self.status_container = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.status_container.grid(row=0, column=1, sticky="w", padx=10)

        self.status_dot = ctk.CTkLabel(
            self.status_container,
            text="🟢",
            font=ctk.CTkFont(size=14)
        )
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_label = ctk.CTkLabel(
            self.status_container,
            text="ያዕቆብ ዝግጁ ነው - ትእዛዝዎን ለመናገር ማይክራፎኑን ይጫኑ",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        )
        self.status_label.pack(side="left")

        # Audio Energy Level Bar
        self.energy_bar = ctk.CTkProgressBar(self.header_card, height=6)
        self.energy_bar.set(0)
        self.energy_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))

        # Chat / Transcript Log Area
        self.chat_box = ctk.CTkTextbox(
            self.main_frame,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wrap="word"
        )
        self.chat_box.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.chat_box.configure(state="disabled")

        # Quick Alexa-style Voice Command Suggestions (Chip Bar)
        self.chips_frame = ctk.CTkScrollableFrame(self.main_frame, height=45, orientation="horizontal", fg_color="transparent")
        self.chips_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        alexa_commands = [
            ("⏱️ የ 5 ደቂቃ ታይመር", "የ 5 ደቂቃ ታይመር ሙላ"),
            ("☀️ የአየር ሁኔታ", "የአየር ሁኔታ ምን ይመስላል?"),
            ("🪙 ሳንቲም ጣል", "ሳንቲም ጣል"),
            ("🎲 ዳይስ ጣል", "ዳይስ ጣል"),
            ("📰 ዜና ንገረኝ", "የዛሬ ዜና ንገረኝ"),
            ("🧩 እንቆቅልሽ ንገረኝ", "እንቆቅልሽ ንገረኝ"),
            ("💡 አስገራሚ እውነታ", "አስገራሚ እውነታ ንገረኝ"),
            ("📜 የዕለቱ ጥቅስ", "ጥቅስ ንገረኝ"),
            ("🎵 ሙዚቃ አጫውት", "ሙዚቃ አጫውት"),
            ("🚀 ካልኩሌተር ክፈት", "ካልኩሌተር ክፈት"),
            ("📸 ስክሪንሾት አንሳ", "ስክሪንሾት አንሳ"),
            ("🕒 ስንት ሰዓት ነው?", "ስንት ሰዓት ነው"),
            ("⏱️ Set 5 Min Timer", "set a timer for 5 minutes"),
            ("☀️ What's the Weather?", "what's the weather like"),
            ("🪙 Flip a Coin", "flip a coin"),
            ("🎲 Roll a Die", "roll a die"),
            ("🧩 Tell Me a Riddle", "tell me a riddle"),
        ]

        for label, cmd_text in alexa_commands:
            chip_btn = ctk.CTkButton(
                self.chips_frame,
                text=label,
                height=32,
                corner_radius=16,
                fg_color="#2b3b4c",
                hover_color="#3b4f66",
                command=lambda c=cmd_text: self._execute_text_command(c)
            )
            chip_btn.pack(side="left", padx=4)

        # Bottom Text Command Entry Bar
        self.input_frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color="transparent")
        self.input_frame.grid(row=3, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.text_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="ትእዛዝ እዚህ ይተይቡ (ለምሳሌ 'የ 5 ደቂቃ ታይመር' ወይም 'የአየር ሁኔታ')...",
            height=44,
            font=ctk.CTkFont(family="Segoe UI", size=14)
        )
        self.text_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.text_entry.bind("<Return>", lambda event: self._on_send_text())

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="ላክ (Send) 🚀",
            width=110,
            height=44,
            corner_radius=8,
            command=self._on_send_text
        )
        self.send_btn.grid(row=0, column=1)

    # -----------------------------------------------------------------
    # UI STATE & STATUS MANAGEMENT
    # -----------------------------------------------------------------
    def set_status(self, state: str, message: str = ""):
        self.status_state = state
        if state == "idle":
            self.status_dot.configure(text="🟢")
            self.mic_btn.configure(
                text="🎙️ ለመናገር ይጫኑ\n(Click to Talk)",
                fg_color="#1f6aa5",
                hover_color="#144870"
            )
            self.status_label.configure(text=message or f"{ASSISTANT_NAME_AM} ዝግጁ ነው - ትእዛዝዎን ለመናገር ማይክራፎኑን ይጫኑ")
            self.energy_bar.set(0)
        elif state == "listening":
            self.status_dot.configure(text="🔴")
            self.mic_btn.configure(
                text="⏹️ ማዳመጥ አቁም\n(Stop Listening)",
                fg_color="#c0392b",
                hover_color="#962d22"
            )
            self.status_label.configure(text=message or "እያደመጥኩ ነው... (Listening...)")
        elif state == "processing":
            self.status_dot.configure(text="🟡")
            self.status_label.configure(text=message or "ትእዛዝዎን እየተረዳሁ ነው... (Processing...)")
        elif state == "speaking":
            self.status_dot.configure(text="🔵")
            self.status_label.configure(text=message or "እየመለስኩ ነው... (Speaking...)")

    def _append_chat(self, sender: str, text: str, tag: str = "normal"):
        self.chat_box.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        if sender == "user":
            header = f"\n🧑 እርስዎ (You) [{timestamp}]:\n"
            content = f"  {text}\n"
        elif sender == "bot":
            header = f"\n🤖 {ASSISTANT_NAME} [{timestamp}]:\n"
            content = f"  {text}\n"
        else:
            header = f"\nℹ️ [{timestamp}] "
            content = f"{text}\n"

        self.chat_box.insert("end", header)
        self.chat_box.insert("end", content)
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _process_queue(self):
        try:
            while True:
                task = self._msg_queue.get_nowait()
                msg_type = task[0]
                
                if msg_type == "status":
                    self.set_status(task[1], task[2] if len(task) > 2 else "")
                elif msg_type == "chat":
                    self._append_chat(task[1], task[2])
                elif msg_type == "energy":
                    level = min(1.0, task[1] * 12.0)
                    self.energy_bar.set(level)
                elif msg_type == "execute_done":
                    if not self.is_continuous.get():
                        self.set_status("idle")
                        
                self._msg_queue.task_done()
        except queue.Empty:
            pass
        self.after(50, self._process_queue)

    # -----------------------------------------------------------------
    # SPEECH & COMMAND WORKFLOW
    # -----------------------------------------------------------------
    def _initial_greeting(self):
        greeting_text = (
            f"ሰላም ጤና ይስጥልኝ! እኔ {ASSISTANT_NAME_AM} ({ASSISTANT_NAME}) ነኝ። "
            "የአማርኛ እና እንግሊዝኛ ወንድ ድምፅ ታጥቄያለሁ። "
            "እንደ አሌክሳ (Alexa) ታይመር ለመሙላት፣ የአየር ሁኔታ ለመጠየቅ፣ ዜና ለማዳመጥ፣ ሳንቲም ወይም ዳይስ ለመጣል፣ "
            "መተግበሪያዎችን ለመክፈት እና ሰዓት ለመጠየቅ ማይክራፎኑን ተጭነው ያናግሩኝ።"
        )
        self._append_chat("bot", greeting_text)
        self.tts_engine.speak(
            text=f"ሰላም! እኔ {ASSISTANT_NAME_AM} ነኝ። ዛሬ በምን ልርዳዎት?",
            language="am",
            voice=self._get_current_voice_code(),
            rate=self.speech_rate.get()
        )

    def _on_timer_expired(self, expire_text: str, duration_label: str):
        """Callback invoked when a background timer fires."""
        self._msg_queue.put(("chat", "bot", f"🔔 {expire_text}"))
        self.tts_engine.speak(
            text=expire_text,
            language=self.current_language.get(),
            voice=self._get_current_voice_code(),
            rate=self.speech_rate.get()
        )

    def _toggle_listening(self):
        if self.status_state == "listening":
            self._stop_listening = True
            self.audio_recorder.stop_recording()
            self.set_status("idle", "ማዳመጥ ተቋርጧል (Listening stopped)")
        else:
            self._start_listening_thread()

    def _start_listening_thread(self):
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._stop_listening = False
        self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._listen_thread.start()

    def _listen_worker(self):
        while not self._stop_listening:
            self._msg_queue.put(("status", "listening", "እያደመጥኩ ነው... ይናገሩ (Listening...)"))

            def on_speech_start():
                self._msg_queue.put(("status", "listening", "ድምፅ ተገኝቷል... (Speech detected...)"))

            def on_audio_level(rms: float):
                self._msg_queue.put(("energy", rms))

            wav_buffer = self.audio_recorder.record_audio_buffer(
                on_speech_start=on_speech_start,
                on_audio_level=on_audio_level
            )

            if self._stop_listening:
                break

            if wav_buffer is None:
                if not self.is_continuous.get():
                    self._msg_queue.put(("status", "idle", "ድምፅ አልተሰማም (No speech detected)"))
                    break
                else:
                    time.sleep(0.3)
                    continue

            self._msg_queue.put(("status", "processing", "ትእዛዝዎን እየተረዳሁ ነው... (Transcribing...)"))
            
            selected_lang = self.current_language.get()
            text, used_lang, err = self.speech_recognizer.transcribe_wav_buffer(
                wav_buffer=wav_buffer,
                language=selected_lang
            )

            if text:
                self._msg_queue.put(("chat", "user", text))
                self._process_and_respond(text, used_lang or selected_lang)
            else:
                err_msg = "ይቅርታ፣ ድምፅዎ በደንብ አልተሰማኝም። እባክዎ እንደገና ይሞክሩ።" if selected_lang == "am" else "Sorry, I couldn't hear clearly. Please try again."
                self._msg_queue.put(("chat", "system", f"⚠️ {err_msg} ({err})"))
                
                if not self.is_continuous.get():
                    self.tts_engine.speak(
                        text=err_msg,
                        language=selected_lang,
                        voice=self._get_current_voice_code(),
                        rate=self.speech_rate.get()
                    )

            if not self.is_continuous.get():
                break

        self._msg_queue.put(("status", "idle"))

    def _process_and_respond(self, user_text: str, language: str):
        spoken_resp, display_resp, meta = self.command_processor.process_command(
            raw_text=user_text,
            language=language
        )

        self._msg_queue.put(("chat", "bot", display_resp))

        def on_tts_start():
            self._msg_queue.put(("status", "speaking", "እየመለስኩ ነው... (Speaking...)"))

        def on_tts_finish():
            self._msg_queue.put(("execute_done",))

        if spoken_resp:
            self.tts_engine.speak(
                text=spoken_resp,
                language=language,
                voice=self._get_current_voice_code(),
                rate=self.speech_rate.get(),
                on_start=on_tts_start,
                on_finish=on_tts_finish
            )
        else:
            self._msg_queue.put(("execute_done",))

    def _on_send_text(self):
        text = self.text_entry.get().strip()
        if not text:
            return
        self.text_entry.delete(0, "end")
        self._execute_text_command(text)

    def _execute_text_command(self, text: str):
        self._append_chat("user", text)
        lang = self.current_language.get()
        self._process_and_respond(text, lang)

    # -----------------------------------------------------------------
    # SETTINGS & HELPERS
    # -----------------------------------------------------------------
    def _on_language_changed(self, value: str):
        if "Amharic" in value:
            self.current_language.set("am")
            self.voice_option.set("Ameha (Amharic Male)")
            self.current_voice.set("am-ET-AmehaNeural")
            self.text_entry.configure(placeholder_text="ትእዛዝ እዚህ ይተይቡ (ለምሳሌ 'የ 5 ደቂቃ ታይመር' ወይም 'የአየር ሁኔታ')...")
        elif "English" in value:
            self.current_language.set("en")
            self.voice_option.set("Guy (English Male)")
            self.current_voice.set("en-US-GuyNeural")
            self.text_entry.configure(placeholder_text="Type command here (e.g. 'set a timer for 5 minutes')...")
        else:
            self.current_language.set("auto")
            self.text_entry.configure(placeholder_text="ትእዛዝ ይተይቡ / Type command here...")

    def _on_voice_changed(self, value: str):
        if "Ameha" in value:
            self.current_voice.set("am-ET-AmehaNeural")
        elif "Guy" in value:
            self.current_voice.set("en-US-GuyNeural")
        elif "Mekdes" in value:
            self.current_voice.set("am-ET-MekdesNeural")
        elif "Jenny" in value:
            self.current_voice.set("en-US-JennyNeural")

    def _on_speed_changed(self, value: float):
        val_int = int(value)
        sign = "+" if val_int >= 0 else ""
        self.speech_rate.set(f"{sign}{val_int}%")

    def _on_continuous_toggle(self):
        if self.is_continuous.get():
            self._start_listening_thread()
        else:
            self._stop_listening = True

    def _get_current_voice_code(self) -> str:
        return self.current_voice.get()

    def _test_voice(self, lang: str):
        if lang == "am":
            test_phrase = f"ሰላም! እኔ ያዕቆብ ነኝ፤ የአማርኛ ወንድ ድምፅ ስርዓት በትክክል እየሰራ ነው።"
            voice = "am-ET-AmehaNeural"
        else:
            test_phrase = f"Hello! I am {ASSISTANT_NAME}, and the English male text-to-speech system is functioning perfectly."
            voice = "en-US-GuyNeural"

        self._append_chat("bot", f"🔊 [Voice Test]: {test_phrase}")
        self.tts_engine.speak(
            text=test_phrase,
            language=lang,
            voice=voice,
            rate=self.speech_rate.get()
        )

    def _stop_tts(self):
        self.tts_engine.stop()
        self.set_status("idle", "ንግግር ተቋርጧል (Speech stopped)")

    def _clear_chat(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
