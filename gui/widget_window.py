"""
Desktop Floating Widget Window for Yakob Assistant.
A sleek, draggable, always-on-top floating pill widget (like Siri / Dynamic Island)
with microphone animation, quick speech responses, and expand/tray controls.
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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FloatingWidget(ctk.CTkToplevel):
    def __init__(self, parent=None, on_expand: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.on_expand_callback = on_expand

        # Initialize Core Services
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
        self.status_state = "idle"
        self._listen_thread = None
        self._stop_listening = False
        self._msg_queue = queue.Queue()

        # Window Styling: Frameless, Always on Top, Rounded Pill
        self.title("Yakob Widget")
        self.overrideredirect(True)  # Frameless window
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.96)
        
        # Geometry: 340x80 floating at top-right of screen
        screen_width = self.winfo_screenwidth()
        x_pos = screen_width - 380
        y_pos = 60
        self.geometry(f"360x90+{x_pos}+{y_pos}")

        # Drag & Move support
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self._process_queue()

    def _build_ui(self):
        # Main Pill Container
        self.pill_frame = ctk.CTkFrame(
            self,
            corner_radius=26,
            fg_color="#18222d",
            border_width=2,
            border_color="#2b5b84"
        )
        self.pill_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Enable dragging by clicking on the background frame
        self.pill_frame.bind("<Button-1>", self._start_drag)
        self.pill_frame.bind("<B1-Motion>", self._do_drag)

        # Left: Pulsing Mic Button
        self.mic_btn = ctk.CTkButton(
            self.pill_frame,
            text="🎙️",
            width=50,
            height=50,
            corner_radius=25,
            font=ctk.CTkFont(size=20),
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._toggle_listening
        )
        self.mic_btn.pack(side="left", padx=(12, 10), pady=12)

        # Center: Info & Live Text
        self.info_box = ctk.CTkFrame(self.pill_frame, fg_color="transparent")
        self.info_box.pack(side="left", fill="both", expand=True, pady=12)
        self.info_box.bind("<Button-1>", self._start_drag)
        self.info_box.bind("<B1-Motion>", self._do_drag)

        self.name_label = ctk.CTkLabel(
            self.info_box,
            text=f"ያዕቆብ (Yakob)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#64B5F6"
        )
        self.name_label.pack(anchor="w")

        self.status_label = ctk.CTkLabel(
            self.info_box,
            text="ዝግጁ ነው (Ready)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="gray80"
        )
        self.status_label.pack(anchor="w")

        # Right: Quick Controls (Language toggle, Expand, Close)
        self.btn_col = ctk.CTkFrame(self.pill_frame, fg_color="transparent")
        self.btn_col.pack(side="right", padx=(5, 12), pady=8)

        # Top row in right col: Expand and Close
        self.top_row = ctk.CTkFrame(self.btn_col, fg_color="transparent")
        self.top_row.pack(anchor="e")

        self.expand_btn = ctk.CTkButton(
            self.top_row,
            text="🗖",
            width=24,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=11),
            fg_color="#2b3b4c",
            hover_color="#3b4f66",
            command=self._expand_to_full
        )
        self.expand_btn.pack(side="left", padx=(0, 4))

        self.close_btn = ctk.CTkButton(
            self.top_row,
            text="✕",
            width=24,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=11),
            fg_color="#442222",
            hover_color="#662222",
            command=self.destroy
        )
        self.close_btn.pack(side="left")

        # Bottom row in right col: Language toggle
        self.lang_btn = ctk.CTkButton(
            self.btn_col,
            text="🇪🇹 AM",
            width=52,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#234567",
            hover_color="#183048",
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
            self.lang_btn.configure(text="🇬🇧 EN")
        else:
            self.current_language = "am"
            self.lang_btn.configure(text="🇪🇹 AM")

    def _expand_to_full(self):
        if self.on_expand_callback:
            self.on_expand_callback()
        self.destroy()

    def set_status(self, state: str, text: str = ""):
        self.status_state = state
        if state == "idle":
            self.mic_btn.configure(text="🎙️", fg_color="#1f6aa5")
            self.status_label.configure(text=text or "ዝግጁ ነው (Ready)")
            self.pill_frame.configure(border_color="#2b5b84")
        elif state == "listening":
            self.mic_btn.configure(text="🔴", fg_color="#c0392b")
            self.status_label.configure(text=text or "እያደመጥኩ ነው...")
            self.pill_frame.configure(border_color="#e74c3c")
        elif state == "processing":
            self.mic_btn.configure(text="⏳", fg_color="#d35400")
            self.status_label.configure(text=text or "እየተረዳሁ ነው...")
            self.pill_frame.configure(border_color="#f39c12")
        elif state == "speaking":
            self.mic_btn.configure(text="🔊", fg_color="#27ae60")
            self.status_label.configure(text=text or "እየመለስኩ ነው...")
            self.pill_frame.configure(border_color="#2ecc71")

    def _toggle_listening(self):
        if self.status_state == "listening":
            self._stop_listening = True
            self.audio_recorder.stop_recording()
            self.set_status("idle", "ማዳመጥ ቆሟል")
        else:
            self._start_listening()

    def _start_listening(self):
        if self._listen_thread and self._listen_thread.is_alive():
            return
        self._stop_listening = False
        self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._listen_thread.start()

    def _listen_worker(self):
        self._msg_queue.put(("status", "listening", "ይናገሩ... (Speak now)"))
        
        wav_buf = self.audio_recorder.record_audio_buffer()
        if not wav_buf or self._stop_listening:
            self._msg_queue.put(("status", "idle", "ድምፅ አልተሰማም"))
            return

        self._msg_queue.put(("status", "processing", "እየተተረጎመ ነው..."))
        text, detected_lang, err = self.speech_recognizer.transcribe_wav_buffer(
            wav_buf,
            language=self.current_language
        )

        if text:
            spoken_resp, display_resp, meta = self.command_processor.process_command(
                raw_text=text,
                language=detected_lang or self.current_language
            )

            # Truncate preview in widget
            preview = (display_resp[:28] + "..") if len(display_resp) > 28 else display_resp
            self._msg_queue.put(("status", "speaking", preview))

            def on_tts_finish():
                self._msg_queue.put(("status", "idle", "ዝግጁ ነው (Ready)"))

            voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["am"])["male"]
            self.tts_engine.speak(
                text=spoken_resp,
                language=self.current_language,
                voice=voice,
                on_finish=on_tts_finish
            )
        else:
            self._msg_queue.put(("status", "idle", "ይቅርታ አልተረዳሁም"))

    def _on_timer_expired(self, expire_text: str, dur: str):
        self._msg_queue.put(("status", "speaking", f"🔔 {dur} ታይመር አልቋል!"))
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
        self.after(50, self._process_queue)


def launch_standalone_widget():
    """Runs the floating widget as a standalone desktop application."""
    root = ctk.CTk()
    root.withdraw()  # Hide main root window, only show floating widget

    def on_expand():
        from gui.app_window import AssistantApp
        app = AssistantApp()
        app.mainloop()

    widget = FloatingWidget(parent=root, on_expand=on_expand)
    widget.mainloop()
