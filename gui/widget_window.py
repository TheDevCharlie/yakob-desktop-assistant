"""
Minimalist Desktop Floating Widget Window for Yakob Assistant.
A sleek, draggable, always-on-top floating pill widget with grounded matte obsidian tones,
subtle border glow, and responsive micro-interactions.
"""
import time
import queue
import threading
import tkinter as tk
from typing import Optional, Callable
import customtkinter as ctk

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
from gui.popup_toast import show_response_toast

WIDGET_THEME = {
    "bg": "#0e1117",
    "card": "#151922",
    "card_hover": "#1c2230",
    "border_idle": "#242a3a",
    "border_listening": "#ef4444",
    "border_speaking": "#10b981",
    "border_processing": "#f59e0b",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "mic_idle": "#1e2433",
    "mic_idle_hover": "#283044",
    "mic_active": "#dc2626",
    "btn_bg": "#1a1f2c",
    "btn_hover": "#252c3e",
}


class FloatingWidget(ctk.CTkToplevel):
    def __init__(self, parent=None, on_expand: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.on_expand_callback = on_expand

        # Core Services
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.tts_engine = TTSEngine()
        self.sys_controller = SystemController()
        self.command_processor = CommandProcessor(
            system_controller=self.sys_controller,
            on_timer_expire_callback=self._on_timer_expired
        )

        # State
        self.current_language = DEFAULT_LANGUAGE
        self.is_silent_mode = False  # Chatbot / Text Only mode
        self.status_state = "idle"
        self._listen_thread = None
        self._stop_listening = False
        self._msg_queue = queue.Queue()

        # Window Configuration
        self.title("Yakob Widget")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.98)
        self.configure(fg_color=WIDGET_THEME["bg"])
        
        # Geometry positioning (top right)
        screen_width = self.winfo_screenwidth()
        x_pos = screen_width - 380
        y_pos = 50
        self.geometry(f"360x78+{x_pos}+{y_pos}")

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self._process_queue()

    def _build_ui(self):
        # Outer Container Frame
        self.pill_frame = ctk.CTkFrame(
            self,
            corner_radius=24,
            fg_color=WIDGET_THEME["card"],
            border_width=1,
            border_color=WIDGET_THEME["border_idle"]
        )
        self.pill_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Drag bindings
        self.pill_frame.bind("<Button-1>", self._start_drag)
        self.pill_frame.bind("<B1-Motion>", self._do_drag)

        # Left: Sleek Circular Microphone Button
        self.mic_btn = ctk.CTkButton(
            self.pill_frame,
            text="🎙",
            width=46,
            height=46,
            corner_radius=23,
            font=ctk.CTkFont(size=18),
            fg_color=WIDGET_THEME["mic_idle"],
            hover_color=WIDGET_THEME["mic_idle_hover"],
            border_width=1,
            border_color=WIDGET_THEME["border_idle"],
            command=self._toggle_listening
        )
        self.mic_btn.pack(side="left", padx=(12, 10), pady=12)

        # Center: Minimalist Label Stack
        self.info_box = ctk.CTkFrame(self.pill_frame, fg_color="transparent")
        self.info_box.pack(side="left", fill="both", expand=True, pady=14)
        self.info_box.bind("<Button-1>", self._start_drag)
        self.info_box.bind("<B1-Motion>", self._do_drag)

        self.name_label = ctk.CTkLabel(
            self.info_box,
            text=f"✦ {ASSISTANT_NAME} ({ASSISTANT_NAME_AM})",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=WIDGET_THEME["text_primary"]
        )
        self.name_label.pack(anchor="w")

        self.status_label = ctk.CTkLabel(
            self.info_box,
            text="Ready to listen",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=WIDGET_THEME["text_secondary"]
        )
        self.status_label.pack(anchor="w", pady=(1, 0))

        # Right: Action Controls
        self.btn_col = ctk.CTkFrame(self.pill_frame, fg_color="transparent")
        self.btn_col.pack(side="right", padx=(4, 12), pady=10)

        # Top row: Mute, Expand, Close
        self.top_row = ctk.CTkFrame(self.btn_col, fg_color="transparent")
        self.top_row.pack(anchor="e")

        self.mute_btn = ctk.CTkButton(
            self.top_row,
            text="🔊",
            width=22,
            height=22,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            text_color=WIDGET_THEME["text_secondary"],
            command=self._toggle_mute_mode
        )
        self.mute_btn.pack(side="left", padx=(0, 4))

        self.expand_btn = ctk.CTkButton(
            self.top_row,
            text="🗖",
            width=22,
            height=22,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            text_color=WIDGET_THEME["text_secondary"],
            command=self._expand_to_full
        )
        self.expand_btn.pack(side="left", padx=(0, 4))

        self.close_btn = ctk.CTkButton(
            self.top_row,
            text="✕",
            width=22,
            height=22,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color="#441a1a",
            text_color=WIDGET_THEME["text_muted"],
            command=self.destroy
        )
        self.close_btn.pack(side="left")

        # Bottom row: Language Pill
        self.lang_btn = ctk.CTkButton(
            self.btn_col,
            text="አማርኛ",
            width=50,
            height=22,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            text_color=WIDGET_THEME["text_secondary"],
            command=self._toggle_language
        )
        self.lang_btn.pack(anchor="e", pady=(4, 0))

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _toggle_language(self):
        if self.current_language == "am":
            self.current_language = "en"
            self.lang_btn.configure(text="English")
        else:
            self.current_language = "am"
            self.lang_btn.configure(text="አማርኛ")

    def _expand_to_full(self):
        if self.on_expand_callback:
            self.on_expand_callback()
        self.destroy()

    def set_status(self, state: str, text: str = ""):
        self.status_state = state
        if state == "idle":
            self.mic_btn.configure(
                text="🎙",
                fg_color=WIDGET_THEME["mic_idle"],
                hover_color=WIDGET_THEME["mic_idle_hover"]
            )
            self.status_label.configure(text=text or "Ready to listen")
            self.pill_frame.configure(border_color=WIDGET_THEME["border_idle"])
        elif state == "listening":
            self.mic_btn.configure(
                text="⏹",
                fg_color=WIDGET_THEME["mic_active"],
                hover_color="#b91c1c"
            )
            self.status_label.configure(text=text or "Listening...")
            self.pill_frame.configure(border_color=WIDGET_THEME["border_listening"])
        elif state == "processing":
            self.mic_btn.configure(
                text="✦",
                fg_color="#d97706",
                hover_color="#b45309"
            )
            self.status_label.configure(text=text or "Processing...")
            self.pill_frame.configure(border_color=WIDGET_THEME["border_processing"])
        elif state == "speaking":
            self.mic_btn.configure(
                text="🔊",
                fg_color="#059669",
                hover_color="#047857"
            )
            self.status_label.configure(text=text or "Speaking...")
            self.pill_frame.configure(border_color=WIDGET_THEME["border_speaking"])

    def _toggle_listening(self):
        # 1. Barge-in: Cut off speech immediately on mic toggle
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()

        if self.status_state == "listening":
            self._stop_listening = True
            self.audio_recorder.stop_recording()
            self.set_status("idle", "Ready to listen")
        else:
            self._start_listening()

    def _start_listening(self):
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._stop_listening = False
        sfx.play_wake()
        self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._listen_thread.start()

    def _toggle_mute_mode(self):
        self.is_silent_mode = not self.is_silent_mode
        if self.is_silent_mode:
            self.tts_engine.stop()
            self.mute_btn.configure(text="🔇", text_color="#ef4444")
            self.set_status("idle", "Chatbot mode (Silent)")
        else:
            self.mute_btn.configure(text="🔊", text_color=WIDGET_THEME["text_secondary"])
            self.set_status("idle", "Voice mode (Speech on)")

    def _listen_worker(self):
        self._msg_queue.put(("status", "listening", "Speak now..."))

        def on_speech_start():
            if self.tts_engine.is_speaking():
                self.tts_engine.stop()

        def on_audio_level(rms: float):
            if rms > 0.02 and self.tts_engine.is_speaking():
                self.tts_engine.stop()
        
        wav_buf = self.audio_recorder.record_audio_buffer(
            on_speech_start=on_speech_start,
            on_audio_level=on_audio_level
        )
        if not wav_buf or self._stop_listening:
            self._msg_queue.put(("status", "idle", "Ready to listen"))
            return

        self._msg_queue.put(("status", "processing", "Transcribing..."))
        text, detected_lang, err = self.speech_recognizer.transcribe_wav_buffer(
            wav_buf,
            language=self.current_language
        )

        if text:
            sfx.play_done()
            spoken_resp, display_resp, meta = self.command_processor.process_command(
                raw_text=text,
                language=detected_lang or self.current_language
            )

            preview = (display_resp[:26] + "..") if len(display_resp) > 26 else display_resp
            self._msg_queue.put(("status", "speaking", preview))

            # If silent chatbot mode is active, trigger text popup and skip TTS!
            if self.is_silent_mode:
                self.tts_engine.stop()
                self.after(50, lambda: show_response_toast(self, display_resp))
                self._msg_queue.put(("status", "idle", "Ready to listen"))
                return

            def on_tts_finish():
                self._msg_queue.put(("status", "idle", "Ready to listen"))

            voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["am"])["male"]
            self.tts_engine.speak(
                text=spoken_resp,
                language=self.current_language,
                voice=voice,
                rate="+15%",
                on_finish=on_tts_finish
            )
        else:
            self._msg_queue.put(("status", "idle", "Could not hear clearly"))

    def _on_timer_expired(self, expire_text: str, dur: str):
        sfx.play_timer_alert()
        self._msg_queue.put(("status", "speaking", f"🔔 {dur} timer up!"))
        voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["am"])["male"]
        self.tts_engine.speak(
            text=expire_text,
            language=self.current_language,
            voice=voice
        )

    def _process_queue(self):
        try:
            while True:
                task = self._msg_queue.get_nowait()
                msg_type = task[0]
                if msg_type == "status":
                    self.set_status(task[1], task[2] if len(task) > 2 else "")
                self._msg_queue.task_done()
        except queue.Empty:
            pass
        self.after(40, self._process_queue)


def launch_standalone_widget():
    root = ctk.CTk()
    root.withdraw()

    def on_expand():
        from gui.app_window import AssistantApp
        app = AssistantApp()
        app.mainloop()

    widget = FloatingWidget(parent=root, on_expand=on_expand)
    widget.mainloop()
