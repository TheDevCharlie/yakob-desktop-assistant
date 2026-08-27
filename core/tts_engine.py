"""
State-of-the-Art Multi-Provider Neural Text-to-Speech (TTS) Engine for Yakob Assistant.
Supports:
1. ElevenLabs Multilingual Studio AI (Highest human realism, breath inflection, and warmth)
2. Microsoft Flagship Neural HD with SSML Conversational Prosody Tuning (Ameha, Andrew Multilingual, Brian, Mekdes)
3. Instant Voice Barge-In / Interruption
4. Fast Responsive Audio Pipeline via pygame.mixer
"""
import os
import re
import time
import queue
import asyncio
import tempfile
import threading
import urllib.request
import json
import pygame
from typing import Optional, Callable
from gtts import gTTS
import edge_tts

from config import VOICE_CONFIG, DEFAULT_SPEECH_RATE


class TTSEngine:
    def __init__(self, elevenlabs_api_key: Optional[str] = None):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[TTSEngine] Pygame mixer init note: {e}")
            
        self.elevenlabs_api_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.provider = "elevenlabs" if self.elevenlabs_api_key else "edge_neural"
        self._is_speaking = False
        self._stop_requested = False
        self._playback_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def set_elevenlabs_key(self, api_key: str):
        """Configures ElevenLabs API key and sets ElevenLabs as primary engine."""
        self.elevenlabs_api_key = api_key.strip()
        if self.elevenlabs_api_key:
            self.provider = "elevenlabs"

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self):
        """Immediately interrupts and halts any active audio playback."""
        self._stop_requested = True
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass
        with self._lock:
            self._is_speaking = False

    def speak(
        self,
        text: str,
        language: str = "am",
        voice: Optional[str] = None,
        rate: str = DEFAULT_SPEECH_RATE,
        pitch: str = "+0Hz",
        on_start: Optional[Callable[[], None]] = None,
        on_finish: Optional[Callable[[], None]] = None,
        block: bool = False
    ):
        """
        Asynchronously synthesizes and plays speech with instant barge-in support.
        """
        if not text or not text.strip():
            if on_finish:
                on_finish()
            return

        # Interrupt any previous speech immediately
        self.stop()
        self._stop_requested = False

        clean_text = self._prepare_human_text(text)

        if language not in ["am", "en"]:
            if any('\u1200' <= c <= '\u137F' for c in clean_text):
                language = "am"
            else:
                language = "en"

        if not voice:
            voice = VOICE_CONFIG.get(language, VOICE_CONFIG["am"])["default"]

        def _worker():
            with self._lock:
                self._is_speaking = True
                
            audio_path = None
            try:
                # Synthesize Audio via the best available provider
                audio_path = self._synthesize_audio(clean_text, language, voice, rate, pitch)
                
                if self._stop_requested or not audio_path or not os.path.exists(audio_path):
                    return

                if on_start:
                    try:
                        on_start()
                    except Exception as e:
                        print(f"[TTSEngine] on_start error: {e}")

                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()

                # Fast polling loop for instant barge-in response
                while pygame.mixer.music.get_busy() and not self._stop_requested:
                    time.sleep(0.02)

                if self._stop_requested:
                    pygame.mixer.music.stop()

                pygame.mixer.music.unload()

            except Exception as e:
                print(f"[TTSEngine] Playback error: {e}")
            finally:
                with self._lock:
                    self._is_speaking = False
                
                if on_finish and not self._stop_requested:
                    try:
                        on_finish()
                    except Exception as e:
                        print(f"[TTSEngine] on_finish error: {e}")
                        
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

    def _prepare_human_text(self, text: str) -> str:
        """Cleans and punctuates text to give speech a natural, warm rhythm."""
        cleaned = re.sub(r'[🎙️🤖🧑🕒📅🔋🔊🔉🔇🔒▶️🔍🚀🌐🧮👋✨🙏😄💡❓⏱️☀️🪙🎲📰🧩📜🎵🎤👨‍💻🔔✦]', '', text)
        cleaned = re.sub(r'[*_#`~]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Punctuation cadence
        if cleaned and not cleaned[-1] in '.!?።!':
            cleaned += '።' if any('\u1200' <= c <= '\u137F' for c in cleaned) else '.'
            
        return cleaned

    def _synthesize_audio(
        self,
        text: str,
        language: str,
        voice: str,
        rate: str = DEFAULT_SPEECH_RATE,
        pitch: str = "+0Hz"
    ) -> Optional[str]:
        """Synthesizes text to MP3 using ElevenLabs AI or Microsoft Edge Neural HD."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)

        # 1. Option 1: ElevenLabs Multilingual v2 (Ultra-Realistic AI Voice)
        if self.elevenlabs_api_key:
            try:
                # Default high-quality male voice: "pNInz6obpgDQGcFmaJgB" (Adam / Deep Male)
                voice_id = "pNInz6obpgDQGcFmaJgB"
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": self.elevenlabs_api_key,
                    "Content-Type": "application/json"
                }
                body = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.45,
                        "similarity_boost": 0.85,
                        "style": 0.2,
                        "use_speaker_boost": True
                    }
                }
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    with open(temp_path, "wb") as f:
                        f.write(resp.read())
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 200:
                        return temp_path
            except Exception as e:
                print(f"[TTSEngine] ElevenLabs fallback to Edge Neural: {e}")

        # 2. Option 2: Microsoft Flagship Neural HD with SSML Prosody Tuning (Free & Instant)
        try:
            async def _edge_gen():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    pitch=pitch
                )
                await communicate.save(temp_path)

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

        # 3. Option 3: gTTS Fallback
        try:
            gtts_lang = "am" if language == "am" else "en"
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(temp_path)
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                return temp_path
        except Exception as e:
            print(f"[TTSEngine] gTTS fallback error: {e}")

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return None
