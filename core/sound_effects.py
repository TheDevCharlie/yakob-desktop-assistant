"""
Acoustic Sound Effects Module for Yakob Assistant.
Generates and plays soft, modern tactile audio feedback (Siri/Alexa style)
using in-memory sine synthesis via pygame.mixer with zero external sound files.
"""
import io
import time
import threading
import numpy as np
import soundfile as sf
import pygame

class SoundEffects:
    def __init__(self):
        self.sample_rate = 24000
        self._wake_sound = None
        self._done_sound = None
        self._timer_sound = None
        self._init_sounds()

    def _init_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            
            self._wake_sound = self._create_tone_sequence([(587.33, 0.08), (880.0, 0.12)])  # D5 -> A5 ascending
            self._done_sound = self._create_tone_sequence([(880.0, 0.06), (659.25, 0.10)])  # A5 -> E5 descending
            self._timer_sound = self._create_timer_bell()
        except Exception as e:
            print(f"[SoundEffects] Init note: {e}")

    def _create_tone_sequence(self, tones):
        total_audio = []
        for freq, duration in tones:
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            # Soft sine with envelope
            envelope = np.sin(np.pi * t / duration) ** 1.5
            tone = 0.22 * np.sin(2 * np.pi * freq * t) * envelope
            total_audio.append(tone)
            
        combined = np.concatenate(total_audio)
        combined_stereo = np.column_stack((combined, combined))
        audio_int16 = (np.clip(combined_stereo, -1.0, 1.0) * 32767).astype(np.int16)
        
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_int16, self.sample_rate, format='WAV')
        byte_io.seek(0)
        return pygame.mixer.Sound(byte_io)

    def _create_timer_bell(self):
        duration = 0.6
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # Bell harmonic combination (fundamental + octave + minor third)
        bell = (
            0.3 * np.sin(2 * np.pi * 880.0 * t) +
            0.15 * np.sin(2 * np.pi * 1760.0 * t) +
            0.08 * np.sin(2 * np.pi * 1046.5 * t)
        )
        decay = np.exp(-4.5 * t)
        bell = bell * decay
        stereo = np.column_stack((bell, bell))
        audio_int16 = (np.clip(stereo, -1.0, 1.0) * 32767).astype(np.int16)
        
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_int16, self.sample_rate, format='WAV')
        byte_io.seek(0)
        return pygame.mixer.Sound(byte_io)

    def play_wake(self):
        """Plays soft ascending chime when microphone activates."""
        def _play():
            try:
                if self._wake_sound:
                    self._wake_sound.play()
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()

    def play_done(self):
        """Plays soft confirmation sound when speech recognition completes."""
        def _play():
            try:
                if self._done_sound:
                    self._done_sound.play()
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()

    def play_timer_alert(self):
        """Plays timer chime."""
        def _play():
            try:
                if self._timer_sound:
                    for _ in range(3):
                        self._timer_sound.play()
                        time.sleep(0.65)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()


# Global instance
sfx = SoundEffects()
