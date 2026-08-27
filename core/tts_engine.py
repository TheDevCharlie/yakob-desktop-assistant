"""
Text-to-Speech (TTS) Engine
Synthesizes speech using Microsoft Edge Neural voices (Edge-TTS) with fallback to gTTS.
Manages asynchronous non-blocking audio playback using pygame.mixer.
"""
import os
import time
import queue
import asyncio
import tempfile
import threading
import pygame
from typing import Optional, Callable
from gtts import gTTS
import edge_tts

from config import VOICE_CONFIG


class TTSEngine:
    def __init__(self):
        # Initialize Pygame Mixer for smooth audio playback
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[TTSEngine] Pygame mixer init note: {e}")
            
        self._is_speaking = False
        self._stop_requested = False
        self._playback_thread: Optional[threading.Thread] = None
        self._temp_files = []
        self._lock = threading.Lock()

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self):
        """Immediately halts any currently playing speech."""
        self._stop_requested = True
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass
        self._is_speaking = False

    def speak(
        self,
        text: str,
        language: str = "am",
        voice: Optional[str] = None,
        rate: str = "+0%",
        on_start: Optional[Callable[[], None]] = None,
        on_finish: Optional[Callable[[], None]] = None,
        block: bool = False
    ):
        """
        Asynchronously synthesizes and speaks the given text.
        
        Args:
            text: The text to be spoken (Amharic or English).
            language: "am" or "en".
            voice: Specific voice name (e.g. 'am-ET-MekdesNeural', 'en-US-JennyNeural').
            rate: Speech rate modifier (e.g. "+0%", "+10%", "-10%").
            on_start: Callback invoked when audio starts playing.
            on_finish: Callback invoked when audio finishes playing.
            block: If True, blocks until audio completes.
        """
        if not text or not text.strip():
            if on_finish:
                on_finish()
            return

        # Stop previous playback if any
        self.stop()
        self._stop_requested = False

        # Auto-detect language if not explicitly am/en
        if language not in ["am", "en"]:
            if any('\u1200' <= c <= '\u137F' for c in text):
                language = "am"
            else:
                language = "en"

        # Determine voice
        if not voice:
            voice = VOICE_CONFIG.get(language, VOICE_CONFIG["am"])["default"]

        def _worker():
            with self._lock:
                self._is_speaking = True
                
            audio_path = None
            try:
                # 1. Synthesize audio file
                audio_path = self._synthesize_audio(text, language, voice, rate)
                
                if self._stop_requested or not audio_path or not os.path.exists(audio_path):
                    return

                # 2. Play audio file with Pygame Mixer
                if on_start:
                    try:
                        on_start()
                    except Exception as e:
                        print(f"[TTSEngine] on_start error: {e}")

                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() and not self._stop_requested:
                    time.sleep(0.05)

                if self._stop_requested:
                    pygame.mixer.music.stop()

                pygame.mixer.music.unload()

            except Exception as e:
                print(f"[TTSEngine] Playback error: {e}")
            finally:
                with self._lock:
                    self._is_speaking = False
                
                if on_finish:
                    try:
                        on_finish()
                    except Exception as e:
                        print(f"[TTSEngine] on_finish error: {e}")
                        
                # Clean up temp file
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except Exception:
                        pass

        if block:
            _worker()
        else:
            self._playback_thread = threading.Thread(target=_worker, daemon=True)
            self._playback_thread.start()

    def _synthesize_audio(self, text: str, language: str, voice: str, rate: str) -> Optional[str]:
        """Synthesizes text to a temporary MP3 file using Edge-TTS with gTTS fallback."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)

        # Primary method: Microsoft Edge Neural TTS
        try:
            async def _edge_gen():
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                await communicate.save(temp_path)

            # Run in event loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_edge_gen())
                loop.close()
            except Exception:
                asyncio.run(_edge_gen())

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                return temp_path
        except Exception as e:
            print(f"[TTSEngine] Edge-TTS note, falling back to gTTS: {e}")

        # Fallback method: gTTS
        try:
            gtts_lang = "am" if language == "am" else "en"
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(temp_path)
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                return temp_path
        except Exception as e:
            print(f"[TTSEngine] gTTS fallback failed: {e}")

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return None
