"""
Speech Recognizer Module
Transcribes audio streams using Google Speech Recognition API.
Supports Amharic (am-ET), English (en-US), and Auto dual-language mode.
"""
import io
import speech_recognition as sr
from typing import Tuple, Optional
from config import VOICE_CONFIG


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust energy thresholds and parameters
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False

    def transcribe_wav_buffer(
        self,
        wav_buffer: io.BytesIO,
        language: str = "am"
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Transcribes WAV audio buffer to text.
        
        Args:
            wav_buffer: In-memory WAV file BytesIO object.
            language: "am" for Amharic, "en" for English, or "auto" for dual-mode.
            
        Returns:
            Tuple of (transcribed_text, detected_or_used_language, error_message)
        """
        if wav_buffer is None:
            return None, None, "No audio data provided"
            
        wav_buffer.seek(0)
        try:
            with sr.AudioFile(wav_buffer) as source:
                audio_data = self.recognizer.record(source)
        except Exception as e:
            return None, None, f"Audio decode error: {e}"

        if language == "am":
            return self._recognize_single(audio_data, "am-ET", "am")
        elif language == "en":
            return self._recognize_single(audio_data, "en-US", "en")
        elif language == "auto":
            # In auto mode, try Amharic first (if Ge'ez script matches), else fallback to English
            text_am, lang_am, err_am = self._recognize_single(audio_data, "am-ET", "am")
            if text_am and any('\u1200' <= char <= '\u137F' for char in text_am):
                return text_am, "am", None
                
            # Try English
            text_en, lang_en, err_en = self._recognize_single(audio_data, "en-US", "en")
            if text_en:
                return text_en, "en", None
                
            # If both failed, return the primary result or error
            if text_am:
                return text_am, "am", None
            return None, None, err_am or err_en
        else:
            # Default to Amharic
            return self._recognize_single(audio_data, "am-ET", "am")

    def _recognize_single(
        self,
        audio_data: sr.AudioData,
        stt_code: str,
        lang_key: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            text = self.recognizer.recognize_google(audio_data, language=stt_code)
            text = text.strip()
            if text:
                return text, lang_key, None
            return None, None, "Empty transcription"
        except sr.UnknownValueError:
            return None, None, "UnknownValueError: Speech was unintelligible"
        except sr.RequestError as e:
            return None, None, f"RequestError: Could not reach recognition service ({e})"
        except Exception as e:
            return None, None, f"Recognition error: {e}"
