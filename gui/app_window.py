import os
import time
import queue
import threading
import tkinter as tk
from typing import Optional, Callable
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
import keyboard

from config import (
    ASSISTANT_NAME,
    ASSISTANT_NAME_AM,
    VOICE_CONFIG,
    DEFAULT_LANGUAGE
)
from core.audio_recorder import AudioRecorder
from core.speech_recognizer import SpeechRecognizer
from core.tts_engine import TTSEngine
from core.command_processor import CommandProcessor
from core.system_controller import SystemController
from core.sound_effects import sfx

# Modern Grounded Dark Theme Palette
THEME = {
    "bg_dark": "#0d0f14",          # Deep obsidian background
    "sidebar_bg": "#12151c",       # Grounded dark slate sidebar
    "card_bg": "#181c25",          # Elevated surface card
    "card_hover": "#1e232f",       # Card hover state
    "card_subtle": "#141720",      # Recessed container
    "border": "#222735",           # Subtle border
    "border_focus": "#384158",     # Highlight border
    "primary": "#3b82f6",          # Muted electric blue accent
    "primary_hover": "#2563eb",    # Darker blue on hover
    "mic_idle": "#202533",         # Minimalist idle mic
    "mic_idle_hover": "#2a3144",   # Idle mic hover
    "mic_active": "#dc2626",       # Recording red
    "mic_active_hover": "#b91c1c",
    "text_primary": "#f8fafc",     # High-contrast crisp white
    "text_secondary": "#94a3b8",   # Soft silver gray
    "text_muted": "#64748b",       # Dim subtitle text
    "chip_bg": "#1a1e29",          # Pill chips
    "chip_hover": "#252b3b",       # Pill chips hover
    "user_bubble": "#1e2536",      # User message bubble
    "bot_bubble": "#161a23",       # Yakob message bubble
}

ctk.set_appearance_mode("Dark")


class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Core Services
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.tts_engine = TTSEngine()
        self.sys_controller = SystemController()
        self.command_processor = CommandProcessor(
            system_controller=self.sys_controller,
            on_timer_expire_callback=self._on_timer_expired
        )

        # State Variables
        self.current_language = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.current_voice = tk.StringVar(value=VOICE_CONFIG["am"]["male"])
        self.speech_rate = tk.StringVar(value="+15%")  # Fast, lively conversational default
        self.is_continuous = tk.BooleanVar(value=False)
        self.status_state = "idle"
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_listening = False
        self._msg_queue = queue.Queue()
        self.tray_icon = None

        # Window Setup
        self.title(f"{ASSISTANT_NAME} ({ASSISTANT_NAME_AM})")
        self.geometry("960x720")
        self.minsize(840, 600)
        self.configure(fg_color=THEME["bg_dark"])

        # Intercept window close -> Minimize to System Tray
        self.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

        # Layout
        self._create_layout()
        self._process_queue()

        # Initialize Global Hotkey (Alt+Y)
        self._init_global_hotkey()

        # Initialize System Tray in Background
        self._init_tray_icon()

        # Initial Welcome Message
        self.after(400, self._initial_greeting)

    def _create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 1. MINIMALIST LEFT SIDEBAR
        # -------------------------------------------------------------
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            corner_radius=0,
            fg_color=THEME["sidebar_bg"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(14, weight=1)

        # Brand Title
        self.brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.brand_frame.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")

        self.logo_label = ctk.CTkLabel(
            self.brand_frame,
            text=f"✦ {ASSISTANT_NAME}",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.logo_label.pack(anchor="w")

        self.sub_label = ctk.CTkLabel(
            self.brand_frame,
            text=f"{ASSISTANT_NAME_AM} • Voice Assistant",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"]
        )
        self.sub_label.pack(anchor="w", pady=(2, 0))

        # Language Segmented Pill
        self.lang_header = ctk.CTkLabel(
            self.sidebar,
            text="LANGUAGE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_muted"]
        )
        self.lang_header.grid(row=1, column=0, padx=20, pady=(10, 4), sticky="w")

        self.lang_seg = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["አማርኛ", "English", "Auto"],
            selected_color=THEME["primary"],
            selected_hover_color=THEME["primary_hover"],
            unselected_color=THEME["card_bg"],
            unselected_hover_color=THEME["card_hover"],
            text_color=THEME["text_primary"],
            corner_radius=10,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._on_language_changed
        )
        self.lang_seg.set("አማርኛ")
        self.lang_seg.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Voice Selector
        self.voice_header = ctk.CTkLabel(
            self.sidebar,
            text="VOICE MODEL",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_muted"]
        )
        self.voice_header.grid(row=3, column=0, padx=20, pady=(5, 4), sticky="w")

        self.voice_option = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "Ameha (Amharic Male)",
                "Guy (English Male)",
                "Mekdes (Amharic Female)",
                "Jenny (English Female)"
            ],
            fg_color=THEME["card_bg"],
            button_color=THEME["border"],
            button_hover_color=THEME["border_focus"],
            dropdown_fg_color=THEME["card_bg"],
            dropdown_hover_color=THEME["card_hover"],
            dropdown_text_color=THEME["text_primary"],
            text_color=THEME["text_primary"],
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._on_voice_changed
        )
        self.voice_option.set("Ameha (Amharic Male)")
        self.voice_option.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Speed Slider
        self.speed_header = ctk.CTkLabel(
            self.sidebar,
            text="SPEECH PACE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_muted"]
        )
        self.speed_header.grid(row=5, column=0, padx=20, pady=(5, 4), sticky="w")

        self.speed_slider = ctk.CTkSlider(
            self.sidebar,
            from_=-30,
            to=30,
            number_of_steps=12,
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            progress_color=THEME["primary"],
            fg_color=THEME["card_bg"],
            height=14,
            command=self._on_speed_changed
        )
        self.speed_slider.set(15)  # Fast by default
        self.speed_slider.grid(row=6, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Continuous Listening Toggle
        self.continuous_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Continuous Listen",
            progress_color=THEME["primary"],
            fg_color=THEME["card_bg"],
            text_color=THEME["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            variable=self.is_continuous,
            command=self._on_continuous_toggle
        )
        self.continuous_switch.grid(row=7, column=0, padx=20, pady=(5, 16), sticky="w")

        # Divider
        self.div1 = ctk.CTkFrame(self.sidebar, height=1, fg_color=THEME["border"])
        self.div1.grid(row=8, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Floating Widget Button
        self.widget_btn = ctk.CTkButton(
            self.sidebar,
            text="📱 Floating Widget Mode",
            fg_color=THEME["card_bg"],
            hover_color=THEME["card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
            corner_radius=8,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._switch_to_widget_mode
        )
        self.widget_btn.grid(row=9, column=0, padx=20, pady=(0, 8), sticky="ew")

        # AI Intelligence Settings Button
        self.ai_btn = ctk.CTkButton(
            self.sidebar,
            text="🧠 AI & Trivia Brain Settings",
            fg_color=THEME["card_bg"],
            hover_color=THEME["card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["primary"],
            corner_radius=8,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._open_ai_settings_dialog
        )
        self.ai_btn.grid(row=10, column=0, padx=20, pady=(0, 8), sticky="ew")

        # Test Voice Button
        self.test_voice_btn = ctk.CTkButton(
            self.sidebar,
            text="🔊 Test Voice Output",
            fg_color=THEME["card_bg"],
            hover_color=THEME["card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_secondary"],
            corner_radius=8,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._test_current_voice
        )
        self.test_voice_btn.grid(row=11, column=0, padx=20, pady=(0, 8), sticky="ew")

        # Stop Speech Button
        self.stop_tts_btn = ctk.CTkButton(
            self.sidebar,
            text="⏹ Stop Speech",
            fg_color="transparent",
            hover_color=THEME["card_bg"],
            text_color=THEME["text_muted"],
            corner_radius=8,
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._stop_tts
        )
        self.stop_tts_btn.grid(row=12, column=0, padx=20, pady=(0, 4), sticky="ew")

        # Clear Log Button
        self.clear_btn = ctk.CTkButton(
            self.sidebar,
            text="🗑 Clear Chat Log",
            fg_color="transparent",
            hover_color=THEME["card_bg"],
            text_color=THEME["text_muted"],
            corner_radius=8,
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._clear_chat
        )
        self.clear_btn.grid(row=13, column=0, padx=20, pady=(0, 20), sticky="ew")

        # -------------------------------------------------------------
        # 2. MAIN CONVERSATION & HERO AREA
        # -------------------------------------------------------------
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Hero Action Card (Clean Minimalist Mic & Status Header)
        self.hero_card = ctk.CTkFrame(
            self.main_frame,
            corner_radius=14,
            fg_color=THEME["card_bg"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.hero_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.hero_card.grid_columnconfigure(1, weight=1)

        # Microphone Button (Round Pill with Hover Glow)
        self.mic_btn = ctk.CTkButton(
            self.hero_card,
            text="🎙",
            font=ctk.CTkFont(size=20),
            width=54,
            height=54,
            corner_radius=27,
            fg_color=THEME["mic_idle"],
            hover_color=THEME["mic_idle_hover"],
            border_width=1,
            border_color=THEME["border_focus"],
            command=self._toggle_listening
        )
        self.mic_btn.grid(row=0, column=0, padx=(16, 14), pady=14)

        # Status Label & Indicator
        self.status_box = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.status_box.grid(row=0, column=1, sticky="w", pady=14)

        self.status_title = ctk.CTkLabel(
            self.status_box,
            text="Ready to listen",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"]
        )
        self.status_title.pack(anchor="w")

        self.status_sub = ctk.CTkLabel(
            self.status_box,
            text="Click mic or choose a quick prompt below",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"]
        )
        self.status_sub.pack(anchor="w", pady=(1, 0))

        # Audio Energy Bar (Thin minimalist meter)
        self.energy_bar = ctk.CTkProgressBar(
            self.hero_card,
            height=3,
            corner_radius=1,
            fg_color=THEME["card_subtle"],
            progress_color=THEME["primary"]
        )
        self.energy_bar.set(0)
        self.energy_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10))

        # Scrollable Chat History Container
        self.chat_container = ctk.CTkScrollableFrame(
            self.main_frame,
            corner_radius=14,
            fg_color=THEME["card_subtle"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.chat_container.grid(row=1, column=0, sticky="nsew", pady=(0, 14))

        # Quick Action Suggestion Chips (Minimalist pill chips)
        self.chips_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            height=40,
            orientation="horizontal",
            fg_color="transparent"
        )
        self.chips_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        chips = [
            ("⏱ የ 5 ደቂቃ ታይመር", "የ 5 ደቂቃ ታይመር ሙላ"),
            ("☀️ የአየር ሁኔታ", "የአየር ሁኔታ ምን ይመስላል?"),
            ("🪙 ሳንቲም ጣል", "ሳንቲም ጣል"),
            ("🎲 ዳይስ ጣል", "ዳይስ ጣል"),
            ("📰 የዛሬ ዜና", "የዛሬ ዜና ንገረኝ"),
            ("🧩 እንቆቅልሽ", "እንቆቅልሽ ንገረኝ"),
            ("💡 አስገራሚ እውነታ", "አስገራሚ እውነታ ንገረኝ"),
            ("🎵 ሙዚቃ አጫውት", "ሙዚቃ አጫውት"),
            ("🚀 ካልኩሌተር", "ካልኩሌተር ክፈት"),
            ("🕒 ስንት ሰዓት ነው?", "ስንት ሰዓት ነው"),
        ]

        for label, cmd_text in chips:
            btn = ctk.CTkButton(
                self.chips_frame,
                text=label,
                height=30,
                corner_radius=15,
                fg_color=THEME["chip_bg"],
                hover_color=THEME["chip_hover"],
                border_width=1,
                border_color=THEME["border"],
                text_color=THEME["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda c=cmd_text: self._execute_text_command(c)
            )
            btn.pack(side="left", padx=4)

        # Inset Text Input Bar
        self.input_card = ctk.CTkFrame(
            self.main_frame,
            height=48,
            corner_radius=12,
            fg_color=THEME["card_bg"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.input_card.grid(row=3, column=0, sticky="ew")
        self.input_card.grid_columnconfigure(0, weight=1)

        self.text_entry = ctk.CTkEntry(
            self.input_card,
            placeholder_text="Type a message or command (e.g., 'ካልኩሌተር ክፈት', 'weather', 'set a timer')...",
            placeholder_text_color=THEME["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            border_width=0,
            text_color=THEME["text_primary"],
            height=44
        )
        self.text_entry.grid(row=0, column=0, sticky="ew", padx=(14, 8))
        self.text_entry.bind("<Return>", lambda event: self._on_send_text())

        self.send_btn = ctk.CTkButton(
            self.input_card,
            text="Send ↵",
            width=76,
            height=34,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_send_text
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 8), pady=6)

    # -----------------------------------------------------------------
    # UI STATE & MESSAGE BUBBLES
    # -----------------------------------------------------------------
    def set_status(self, state: str, message: str = ""):
        self.status_state = state
        if state == "idle":
            self.mic_btn.configure(
                text="🎙",
                fg_color=THEME["mic_idle"],
                hover_color=THEME["mic_idle_hover"],
                border_color=THEME["border_focus"]
            )
            self.status_title.configure(text=message or "Ready to listen")
            self.status_sub.configure(text="Click mic or type a command")
            self.energy_bar.set(0)
        elif state == "listening":
            self.mic_btn.configure(
                text="⏹",
                fg_color=THEME["mic_active"],
                hover_color=THEME["mic_active_hover"],
                border_color="#ef4444"
            )
            self.status_title.configure(text="Listening...")
            self.status_sub.configure(text=message or "Speak naturally into your microphone")
        elif state == "processing":
            self.mic_btn.configure(
                text="✦",
                fg_color="#d97706",
                hover_color="#b45309",
                border_color="#f59e0b"
            )
            self.status_title.configure(text="Processing...")
            self.status_sub.configure(text=message or "Understanding command")
        elif state == "speaking":
            self.mic_btn.configure(
                text="🔊",
                fg_color="#059669",
                hover_color="#047857",
                border_color="#10b981"
            )
            self.status_title.configure(text="Speaking...")
            self.status_sub.configure(text=message or "Responding aloud")

    def _append_chat_card(self, sender: str, text: str):
        """Creates a clean message bubble card."""
        is_user = sender == "user"
        timestamp = time.strftime("%H:%M")

        bubble_frame = ctk.CTkFrame(
            self.chat_container,
            fg_color=THEME["user_bubble"] if is_user else THEME["bot_bubble"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"]
        )
        bubble_frame.pack(fill="x", padx=12, pady=6)

        # Header Row (Avatar/Name + Time)
        hdr_frame = ctk.CTkFrame(bubble_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=14, pady=(10, 4))

        author = "You" if is_user else ASSISTANT_NAME
        author_color = THEME["primary"] if is_user else "#10b981"
        
        name_lbl = ctk.CTkLabel(
            hdr_frame,
            text=author,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=author_color
        )
        name_lbl.pack(side="left")

        time_lbl = ctk.CTkLabel(
            hdr_frame,
            text=timestamp,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_muted"]
        )
        time_lbl.pack(side="right")

        # Body Text
        msg_lbl = ctk.CTkLabel(
            bubble_frame,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=THEME["text_primary"],
            wraplength=560,
            justify="left"
        )
        msg_lbl.pack(anchor="w", padx=14, pady=(0, 10))

    def _process_queue(self):
        try:
            while True:
                task = self._msg_queue.get_nowait()
                msg_type = task[0]
                if msg_type == "status":
                    self.set_status(task[1], task[2] if len(task) > 2 else "")
                elif msg_type == "chat":
                    self._append_chat_card(task[1], task[2])
                elif msg_type == "energy":
                    level = min(1.0, task[1] * 14.0)
                    self.energy_bar.set(level)
                elif msg_type == "execute_done":
                    if not self.is_continuous.get():
                        self.set_status("idle")
                self._msg_queue.task_done()
        except queue.Empty:
            pass
        self.after(40, self._process_queue)

    # -----------------------------------------------------------------
    # WORKFLOWS
    # -----------------------------------------------------------------
    def _initial_greeting(self):
        msg = f"ሰላም! እኔ {ASSISTANT_NAME_AM} ({ASSISTANT_NAME}) ነኝ። በምን ልርዳዎት?"
        self._append_chat_card("bot", msg)
        self.tts_engine.speak(
            text=msg,
            language="am",
            voice=self._get_current_voice_code(),
            rate=self.speech_rate.get()
        )

    def _on_timer_expired(self, expire_text: str, dur: str):
        sfx.play_timer_alert()
        self._msg_queue.put(("chat", "bot", f"🔔 {expire_text}"))
        self.tts_engine.speak(
            text=expire_text,
            language=self.current_language.get(),
            voice=self._get_current_voice_code(),
            rate=self.speech_rate.get()
        )

    def _toggle_listening(self):
        # 1. Voice Barge-In: If currently speaking, stop TTS immediately!
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()

        if self.status_state == "listening":
            self._stop_listening = True
            self.audio_recorder.stop_recording()
            self.set_status("idle", "Listening stopped")
        else:
            self._start_listening_thread()

    def _start_listening_thread(self):
        # Stop speech when starting to listen
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._stop_listening = False
        sfx.play_wake()  # Soft pleasant ascending chime
        self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._listen_thread.start()

    def _listen_worker(self):
        while not self._stop_listening:
            self._msg_queue.put(("status", "listening", "Listening for speech..."))

            def on_speech_start():
                # Barge-in: Cut off speech as soon as user starts speaking!
                if self.tts_engine.is_speaking():
                    self.tts_engine.stop()
                self._msg_queue.put(("status", "listening", "Recording audio..."))

            def on_audio_level(rms: float):
                # If audio level is high and TTS is speaking, interrupt!
                if rms > 0.02 and self.tts_engine.is_speaking():
                    self.tts_engine.stop()
                self._msg_queue.put(("energy", rms))

            wav_buffer = self.audio_recorder.record_audio_buffer(
                on_speech_start=on_speech_start,
                on_audio_level=on_audio_level
            )

            if self._stop_listening:
                break

            if wav_buffer is None:
                if not self.is_continuous.get():
                    self._msg_queue.put(("status", "idle", "No speech detected"))
                    break
                else:
                    time.sleep(0.2)
                    continue

            self._msg_queue.put(("status", "processing", "Transcribing..."))
            
            selected_lang = self._get_active_lang_code()
            text, used_lang, err = self.speech_recognizer.transcribe_wav_buffer(
                wav_buffer=wav_buffer,
                language=selected_lang
            )

            if text:
                sfx.play_done()  # Soft confirmation tone
                self._msg_queue.put(("chat", "user", text))
                self._process_and_respond(text, used_lang or selected_lang)
            else:
                err_msg = "ይቅርታ፣ ድምፅዎ በደንብ አልተሰማኝም።" if selected_lang == "am" else "Sorry, I couldn't hear clearly."
                self._msg_queue.put(("chat", "bot", err_msg))
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
            self._msg_queue.put(("status", "speaking", "Playing voice response"))

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
        self._append_chat_card("user", text)
        lang = self._get_active_lang_code()
        self._process_and_respond(text, lang)

    # -----------------------------------------------------------------
    # HELPERS & SETTINGS
    # -----------------------------------------------------------------
    def _get_active_lang_code(self) -> str:
        val = self.lang_seg.get()
        if "አማርኛ" in val:
            return "am"
        elif "English" in val:
            return "en"
        return "auto"

    def _on_language_changed(self, value: str):
        if "አማርኛ" in value:
            self.voice_option.set("Ameha (Amharic Male)")
            self.current_voice.set("am-ET-AmehaNeural")
        elif "English" in value:
            self.voice_option.set("Guy (English Male)")
            self.current_voice.set("en-US-GuyNeural")

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

    def _test_current_voice(self):
        lang = self._get_active_lang_code()
        if lang == "am":
            test_phrase = f"ሰላም! እኔ ያዕቆብ ነኝ፤ ድምፄ በትክክል እየሰራ ነው።"
        else:
            test_phrase = f"Hello! I am {ASSISTANT_NAME}, and my voice system is ready."
        self._append_chat_card("bot", f"🔊 [Voice Check]: {test_phrase}")
        self.tts_engine.speak(
            text=test_phrase,
            language=lang if lang in ["am", "en"] else "am",
            voice=self._get_current_voice_code(),
            rate=self.speech_rate.get()
        )

    def _stop_tts(self):
        self.tts_engine.stop()
        self.set_status("idle", "Speech stopped")

    def _clear_chat(self):
        for widget in self.chat_container.winfo_children():
            widget.destroy()

    def _open_ai_settings_dialog(self):
        """Opens a sleek minimalist modal to configure Gemini / Groq / OpenAI API keys."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("AI Intelligence & Trivia Settings")
        dialog.geometry("460x360")
        dialog.attributes("-topmost", True)
        dialog.configure(fg_color=THEME["bg_dark"])

        title = ctk.CTkLabel(
            dialog,
            text="🧠 Configure LLM & Trivia Engine",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=THEME["text_primary"]
        )
        title.pack(anchor="w", padx=24, pady=(20, 6))

        desc = ctk.CTkLabel(
            dialog,
            text="Select an AI model for deep trivia, general knowledge, and conversational reasoning in Amharic & English:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"],
            wraplength=410,
            justify="left"
        )
        desc.pack(anchor="w", padx=24, pady=(0, 16))

        # Provider Selector
        prov_lbl = ctk.CTkLabel(dialog, text="AI PROVIDER", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=THEME["text_muted"])
        prov_lbl.pack(anchor="w", padx=24, pady=(0, 4))

        prov_menu = ctk.CTkOptionMenu(
            dialog,
            values=["Google Gemini 2.5 Flash (Recommended)", "Groq (Llama 3.3 70B)", "OpenAI (GPT-4o-mini)", "Built-in Offline Trivia Engine"],
            fg_color=THEME["card_bg"],
            button_color=THEME["border"],
            dropdown_fg_color=THEME["card_bg"],
            dropdown_text_color=THEME["text_primary"],
            text_color=THEME["text_primary"],
            corner_radius=8,
            height=34
        )
        prov_menu.pack(fill="x", padx=24, pady=(0, 14))

        # API Key Input
        key_lbl = ctk.CTkLabel(dialog, text="API KEY (Optional if using built-in offline engine)", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=THEME["text_muted"])
        key_lbl.pack(anchor="w", padx=24, pady=(0, 4))

        key_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Paste your Gemini / Groq / OpenAI API key here...",
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["card_bg"],
            border_color=THEME["border"],
            text_color=THEME["text_primary"],
            show="•",
            height=36
        )
        key_entry.pack(fill="x", padx=24, pady=(0, 20))

        # Fill existing key if present
        if self.command_processor.llm_brain.api_key:
            key_entry.insert(0, self.command_processor.llm_brain.api_key)

        def save_and_close():
            sel = prov_menu.get()
            key = key_entry.get().strip()
            
            provider_map = {
                "Google Gemini 2.5 Flash (Recommended)": "gemini",
                "Groq (Llama 3.3 70B)": "groq",
                "OpenAI (GPT-4o-mini)": "openai",
                "Built-in Offline Trivia Engine": "offline"
            }
            chosen_provider = provider_map.get(sel, "gemini")
            self.command_processor.llm_brain.set_config(chosen_provider, key)
            self._append_chat_card("bot", f"🧠 AI Model updated to: {sel}")
            dialog.destroy()

        save_btn = ctk.CTkButton(
            dialog,
            text="Save Settings ✦",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=36,
            command=save_and_close
        )
        save_btn.pack(fill="x", padx=24, pady=(0, 10))

    # -------------------------------------------------------------
    # GLOBAL HOTKEY & SYSTEM TRAY
    # -------------------------------------------------------------
    def _init_global_hotkey(self):
        """Registers system-wide hotkey (Alt+Y) to summon Yakob from anywhere."""
        def _bind():
            try:
                keyboard.add_hotkey("alt+y", self._on_hotkey_pressed)
            except Exception as e:
                print(f"[AssistantApp] Global hotkey note: {e}")
        threading.Thread(target=_bind, daemon=True).start()

    def _on_hotkey_pressed(self):
        """Triggered when Alt+Y is pressed globally."""
        def _wake():
            self.deiconify()
            self.lift()
            self.focus_force()
            self._start_listening_thread()
        self.after(0, _wake)

    def _init_tray_icon(self):
        """Initializes Windows System Tray Icon in background thread."""
        def _tray_worker():
            try:
                # Generate clean 64x64 icon image
                img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Outer circle
                draw.ellipse([4, 4, 60, 60], fill="#181c25", outline="#3b82f6", width=3)
                # Inner sparkle
                draw.ellipse([22, 22, 42, 42], fill="#3b82f6")

                menu = pystray.Menu(
                    pystray.MenuItem("✦ Open Yakob", lambda: self.after(0, self._restore_from_tray)),
                    pystray.MenuItem("📱 Floating Widget", lambda: self.after(0, self._switch_to_widget_mode)),
                    pystray.MenuItem("🎙 Listen Now (Alt+Y)", lambda: self.after(0, self._on_hotkey_pressed)),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("✕ Exit Yakob", lambda: self.after(0, self._quit_app))
                )
                self.tray_icon = pystray.Icon("YakobAssistant", img, "Yakob Voice Assistant (Alt+Y)", menu)
                self.tray_icon.run()
            except Exception as e:
                print(f"[AssistantApp] Tray init note: {e}")
        threading.Thread(target=_tray_worker, daemon=True).start()

    def _minimize_to_tray(self):
        """Minimizes window to system tray instead of exiting."""
        self.withdraw()

    def _restore_from_tray(self):
        """Restores window from system tray."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_app(self):
        """Clean application shutdown."""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()
        os._exit(0)

    def _switch_to_widget_mode(self):
        self.withdraw()
        from gui.widget_window import FloatingWidget
        def on_expand():
            self.deiconify()
        FloatingWidget(parent=self, on_expand=on_expand)
