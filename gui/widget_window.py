"""
Minimalist Desktop Floating Widget Window for Yakob Assistant.
Supports:
1. Draggable obsidian pill widget with smooth glowing borders
2. In-Widget YouTube Music & Radio streaming controls (Play/Pause, Skip, Volume Slider)
3. Compact typing input bar for quick hands-on keyboard commands
4. Bi-directional Mute / Chatbot Mode synchronized with Main App
5. Single-instance response popup toasts & voice barge-in
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
from core.music_streamer import music_streamer
from gui.popup_toast import show_response_toast

WIDGET_THEME = {
    "bg": "#0e1117",
    "card": "#141822",
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
    "btn_bg": "#1a202c",
    "btn_hover": "#262f40",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
}


class FloatingWidget(ctk.CTkToplevel):
    def __init__(
        self,
        parent=None,
        is_silent: bool = False,
        on_expand: Optional[Callable[[bool], None]] = None,
        on_mute_change: Optional[Callable[[bool], None]] = None
    ):
        super().__init__(parent)
        self.on_expand_callback = on_expand
        self.on_mute_change_callback = on_mute_change

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
        self.is_silent_mode = is_silent
        self.status_state = "idle"
        self._listen_thread = None
        self._stop_listening = False
        self._msg_queue = queue.Queue()
        self._ptt_held = False

        # Window Configuration
        self.title("Yakob Floating Widget")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.98)
        self.configure(fg_color=WIDGET_THEME["bg"])
        
        # Geometry positioning (top right)
        screen_width = self.winfo_screenwidth()
        x_pos = max(50, screen_width - 430)
        y_pos = 45
        self.geometry(f"410x140+{x_pos}+{y_pos}")

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self._process_queue()
        self._start_music_monitor()

    def _build_ui(self):
        # Outer Container Frame
        self.pill_frame = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color=WIDGET_THEME["card"],
            border_width=1,
            border_color=WIDGET_THEME["border_idle"]
        )
        self.pill_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Drag bindings for background
        self.pill_frame.bind("<Button-1>", self._start_drag)
        self.pill_frame.bind("<B1-Motion>", self._do_drag)

        # =============================================================
        # ROW 1: HEADER (Mic, Status, Controls)
        # =============================================================
        self.header_row = ctk.CTkFrame(self.pill_frame, fg_color="transparent")
        self.header_row.pack(fill="x", padx=10, pady=(8, 4))
        self.header_row.bind("<Button-1>", self._start_drag)
        self.header_row.bind("<B1-Motion>", self._do_drag)

        # 1. Circular Microphone / PTT Button
        self.mic_btn = ctk.CTkButton(
            self.header_row,
            text="🎙",
            width=36,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=15),
            fg_color=WIDGET_THEME["mic_idle"],
            hover_color=WIDGET_THEME["mic_idle_hover"],
            border_width=1,
            border_color=WIDGET_THEME["border_idle"]
        )
        self.mic_btn.pack(side="left", padx=(0, 8))
        self.mic_btn.bind("<ButtonPress-1>", lambda e: self._on_widget_ptt_press())
        self.mic_btn.bind("<ButtonRelease-1>", lambda e: self._on_widget_ptt_release())

        # 2. Status & Title
        self.info_box = ctk.CTkFrame(self.header_row, fg_color="transparent")
        self.info_box.pack(side="left", fill="both", expand=True)
        self.info_box.bind("<Button-1>", self._start_drag)
        self.info_box.bind("<B1-Motion>", self._do_drag)

        self.name_label = ctk.CTkLabel(
            self.info_box,
            text=f"✦ {ASSISTANT_NAME}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=WIDGET_THEME["text_primary"]
        )
        self.name_label.pack(anchor="w")

        init_status = "Chatbot mode" if self.is_silent_mode else "Ready to listen"
        self.status_label = ctk.CTkLabel(
            self.info_box,
            text=init_status,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=WIDGET_THEME["text_secondary"]
        )
        self.status_label.pack(anchor="w", pady=(0, 0))

        # 3. Header Action Buttons (Mute, Language, Expand, Close)
        self.hdr_actions = ctk.CTkFrame(self.header_row, fg_color="transparent")
        self.hdr_actions.pack(side="right")

        self.lang_btn = ctk.CTkButton(
            self.hdr_actions,
            text="EN",
            width=28,
            height=22,
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            command=self._toggle_language
        )
        self.lang_btn.pack(side="left", padx=(0, 4))

        mute_icon = "🔇" if self.is_silent_mode else "🔊"
        mute_color = "#ef4444" if self.is_silent_mode else WIDGET_THEME["text_secondary"]
        self.mute_btn = ctk.CTkButton(
            self.hdr_actions,
            text=mute_icon,
            width=24,
            height=22,
            corner_radius=5,
            font=ctk.CTkFont(size=9),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            text_color=mute_color,
            command=self._toggle_mute_mode
        )
        self.mute_btn.pack(side="left", padx=(0, 4))

        self.expand_btn = ctk.CTkButton(
            self.hdr_actions,
            text="🗖",
            width=24,
            height=22,
            corner_radius=5,
            font=ctk.CTkFont(size=9),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            text_color=WIDGET_THEME["text_secondary"],
            command=self._expand_to_full
        )
        self.expand_btn.pack(side="left", padx=(0, 4))

        self.close_btn = ctk.CTkButton(
            self.hdr_actions,
            text="✕",
            width=24,
            height=22,
            corner_radius=5,
            font=ctk.CTkFont(size=9),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color="#441a1a",
            text_color=WIDGET_THEME["text_muted"],
            command=self.destroy
        )
        self.close_btn.pack(side="left")

        # =============================================================
        # ROW 2: MUSIC STREAMING & VOLUME BAR
        # =============================================================
        self.music_row = ctk.CTkFrame(self.pill_frame, corner_radius=8, fg_color="#10131a", border_width=1, border_color="#1e2433")
        self.music_row.pack(fill="x", padx=10, pady=(2, 4))

        self.track_label = ctk.CTkLabel(
            self.music_row,
            text="🎵 Music: Idle",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=WIDGET_THEME["text_secondary"]
        )
        self.track_label.pack(side="left", padx=(8, 6), pady=3)

        self.music_btn_group = ctk.CTkFrame(self.music_row, fg_color="transparent")
        self.music_btn_group.pack(side="right", padx=6, pady=3)

        self.play_pause_btn = ctk.CTkButton(
            self.music_btn_group,
            text="▶",
            width=24,
            height=20,
            corner_radius=4,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            command=self._toggle_music_playback
        )
        self.play_pause_btn.pack(side="left", padx=(0, 3))

        self.skip_btn = ctk.CTkButton(
            self.music_btn_group,
            text="⏭",
            width=24,
            height=20,
            corner_radius=4,
            font=ctk.CTkFont(size=9),
            fg_color=WIDGET_THEME["btn_bg"],
            hover_color=WIDGET_THEME["btn_hover"],
            command=self._skip_music
        )
        self.skip_btn.pack(side="left", padx=(0, 6))

        # Compact Volume Slider
        self.vol_lbl = ctk.CTkLabel(self.music_btn_group, text="🔉", font=ctk.CTkFont(size=9), text_color=WIDGET_THEME["text_muted"])
        self.vol_lbl.pack(side="left", padx=(0, 2))

        self.vol_slider = ctk.CTkSlider(
            self.music_btn_group,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=65,
            height=12,
            progress_color=WIDGET_THEME["primary"],
            button_color=WIDGET_THEME["text_primary"],
            button_hover_color="#60a5fa",
            command=self._on_volume_slider
        )
        self.vol_slider.set(0.85)
        self.vol_slider.pack(side="left")

        # =============================================================
        # ROW 3: COMPACT TEXT TYPING BAR
        # =============================================================
        self.input_row = ctk.CTkFrame(self.pill_frame, corner_radius=8, fg_color="#181d28", border_width=1, border_color="#242c3d")
        self.input_row.pack(fill="x", padx=10, pady=(2, 8))

        self.type_entry = ctk.CTkEntry(
            self.input_row,
            placeholder_text="Type command or 'play <song>'...",
            placeholder_text_color=WIDGET_THEME["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="transparent",
            border_width=0,
            text_color=WIDGET_THEME["text_primary"],
            height=24
        )
        self.type_entry.pack(side="left", fill="x", expand=True, padx=(8, 4))
        self.type_entry.bind("<Return>", lambda e: self._on_submit_typed_text())

        self.send_btn = ctk.CTkButton(
            self.input_row,
            text="↵",
            width=28,
            height=20,
            corner_radius=4,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=WIDGET_THEME["primary"],
            hover_color=WIDGET_THEME["primary_hover"],
            command=self._on_submit_typed_text
        )
        self.send_btn.pack(side="right", padx=(0, 4), pady=2)

    # -------------------------------------------------------------
    # MUSIC CONTROLS & MONITOR LOOP
    # -------------------------------------------------------------
    def _start_music_monitor(self):
        if hasattr(self, 'track_label') and self.track_label.winfo_exists():
            curr = music_streamer.get_current_track()
            if music_streamer.is_playing() and curr:
                clean = curr.replace("📻", "").strip()
                prefix = "📻" if "FM" in curr or "Radio" in curr else "🎵"
                self.track_label.configure(text=f"{prefix} {clean[:20]}")
                self.play_pause_btn.configure(text="⏸")
            elif music_streamer.is_paused and curr:
                clean = curr.replace("📻", "").strip()
                self.track_label.configure(text=f"⏸ {clean[:20]}")
                self.play_pause_btn.configure(text="▶")
            elif not music_streamer.is_playing() and not music_streamer.is_paused:
                self.track_label.configure(text="🎵 Music: Idle")
                self.play_pause_btn.configure(text="▶")

        self.after(350, self._start_music_monitor)

    def _toggle_music_playback(self):
        if music_streamer.is_paused:
            music_streamer.unpause()
        elif music_streamer.is_playing():
            music_streamer.pause()
        else:
            music_streamer.play_playlist("Chill Vibes")

    def _skip_music(self):
        music_streamer.next_track()

    def _on_volume_slider(self, val: float):
        music_streamer.set_volume(val)
        self.tts_engine.set_volume(val)

    # -------------------------------------------------------------
    # TEXT COMMAND EXECUTION
    # -------------------------------------------------------------
    def _on_submit_typed_text(self):
        text = self.type_entry.get().strip()
        if not text:
            return
        self.type_entry.delete(0, "end")
        self.set_status("processing", "Processing...")

        def _worker():
            spoken_resp, display_resp, meta = self.command_processor.process_command(
                raw_text=text,
                language=self.current_language
            )
            preview = (display_resp[:26] + "..") if len(display_resp) > 26 else display_resp
            self._msg_queue.put(("status", "speaking", preview))
            self.after(50, lambda: show_response_toast(self, display_resp))

            if self.is_silent_mode:
                self.tts_engine.stop()
                self._msg_queue.put(("status", "idle"))
                return

            def on_tts_finish():
                self._msg_queue.put(("status", "idle"))

            voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["en"])["default"]
            self.tts_engine.speak(
                text=spoken_resp,
                language=self.current_language,
                voice=voice,
                rate="+15%",
                on_finish=on_tts_finish
            )

        threading.Thread(target=_worker, daemon=True).start()

    # -------------------------------------------------------------
    # DRAGGING & CONTROLS
    # -------------------------------------------------------------
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
            self.lang_btn.configure(text="EN")
        else:
            self.current_language = "am"
            self.lang_btn.configure(text="አማ")

    def _expand_to_full(self):
        if self.on_expand_callback:
            self.on_expand_callback(self.is_silent_mode)
        self.destroy()

    def _toggle_mute_mode(self):
        self.is_silent_mode = not self.is_silent_mode
        if self.is_silent_mode:
            self.tts_engine.stop()
            self.mute_btn.configure(text="🔇", text_color="#ef4444")
            self.set_status("idle", "Chatbot mode")
        else:
            self.mute_btn.configure(text="🔊", text_color=WIDGET_THEME["text_secondary"])
            self.set_status("idle", "Voice mode")

        if self.on_mute_change_callback:
            self.on_mute_change_callback(self.is_silent_mode)

    def set_status(self, state: str, text: str = ""):
        self.status_state = state
        if state == "idle":
            self.mic_btn.configure(
                text="🎙",
                fg_color=WIDGET_THEME["mic_idle"],
                hover_color=WIDGET_THEME["mic_idle_hover"]
            )
            fallback_text = "Chatbot mode" if self.is_silent_mode else "Ready to listen"
            self.status_label.configure(text=text or fallback_text)
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

    def _on_widget_ptt_press(self):
        if hasattr(self, '_ptt_held') and self._ptt_held:
            return
        self._ptt_held = True
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
        sfx.play_wake()
        self.set_status("listening", "Recording (Hold)...")
        self.audio_recorder.start_ptt_recording()

    def _on_widget_ptt_release(self):
        if not getattr(self, '_ptt_held', False):
            return
        self._ptt_held = False
        self.set_status("processing", "Transcribing...")

        def _finish():
            wav_buf = self.audio_recorder.stop_ptt_recording()
            if not wav_buf:
                self._msg_queue.put(("status", "idle"))
                return

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
                self.after(50, lambda: show_response_toast(self, display_resp))

                if self.is_silent_mode:
                    self.tts_engine.stop()
                    self._msg_queue.put(("status", "idle"))
                    return

                def on_tts_finish():
                    self._msg_queue.put(("status", "idle"))

                voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["en"])["default"]
                self.tts_engine.speak(
                    text=spoken_resp,
                    language=self.current_language,
                    voice=voice,
                    rate="+15%",
                    on_finish=on_tts_finish
                )
            else:
                self._msg_queue.put(("status", "idle", "Could not hear"))

        threading.Thread(target=_finish, daemon=True).start()

    def _on_timer_expired(self, expire_text: str, dur: str):
        sfx.play_timer_alert()
        self.after(50, lambda: show_response_toast(self, f"🔔 {expire_text}"))
        if not self.is_silent_mode:
            voice = VOICE_CONFIG.get(self.current_language, VOICE_CONFIG["en"])["default"]
            self.tts_engine.speak(
                text=expire_text,
                language=self.current_language,
                voice=voice,
                rate="+15%"
            )

    def _process_queue(self):
        try:
            while True:
                item = self._msg_queue.get_nowait()
                msg_type = item[0]
                if msg_type == "status":
                    state = item[1]
                    extra = item[2] if len(item) > 2 else ""
                    self.set_status(state, extra)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)
