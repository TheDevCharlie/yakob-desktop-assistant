"""
Audio Recorder Module
Captures microphone audio using sounddevice and performs silence detection (VAD).
Encodes audio into an in-memory WAV stream for speech recognition without temp file clutter.
"""
import io
import time
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from typing import Optional, Callable

from config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    RECORD_MAX_SECONDS,
    RECORD_MIN_SECONDS
)


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int = AUDIO_SAMPLE_RATE,
        channels: int = AUDIO_CHANNELS,
        silence_threshold: float = SILENCE_THRESHOLD,
        silence_duration: float = SILENCE_DURATION,
        max_duration: float = RECORD_MAX_SECONDS,
        min_duration: float = RECORD_MIN_SECONDS
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration
        self.min_duration = min_duration
        self._is_recording = False
        self._stop_requested = False

    def is_recording(self) -> bool:
        return self._is_recording

    def stop_recording(self):
        """Signals the ongoing recording loop to stop immediately."""
        self._stop_requested = True

    def record_audio_buffer(
        self,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None
    ) -> Optional[io.BytesIO]:
        """
        Records audio from the default microphone until speech completes (silence detected)
        or maximum duration is reached.
        
        Returns:
            io.BytesIO containing WAV data if speech was captured, or None if cancelled/no speech.
        """
        self._is_recording = True
        self._stop_requested = False
        
        chunk_duration = 0.05  # 50ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        
        recorded_frames = []
        speech_started = False
        silence_frames_count = 0
        silence_frames_needed = int(self.silence_duration / chunk_duration)
        max_frames_count = int(self.max_duration / chunk_duration)
        
        start_time = time.time()
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=chunk_size
            ) as stream:
                frames_processed = 0
                
                while not self._stop_requested and frames_processed < max_frames_count:
                    # Read chunk from microphone
                    audio_chunk, overflowed = stream.read(chunk_size)
                    recorded_frames.append(audio_chunk.copy())
                    frames_processed += 1
                    
                    # Calculate Root Mean Square (RMS) energy level
                    rms = np.sqrt(np.mean(audio_chunk**2))
                    
                    if on_audio_level:
                        on_audio_level(float(rms))
                    
                    if rms > self.silence_threshold:
                        if not speech_started:
                            speech_started = True
                            if on_speech_start:
                                on_speech_start()
                        silence_frames_count = 0
                    else:
                        if speech_started:
                            silence_frames_count += 1
                            if silence_frames_count >= silence_frames_needed:
                                # User has stopped speaking
                                break
                                
                    # If we have recorded past min_duration with no speech, prevent hanging indefinitely
                    elapsed = time.time() - start_time
                    if not speech_started and elapsed > 7.0:
                        # 7 seconds of complete silence, exit
                        break
                        
        except Exception as e:
            print(f"[AudioRecorder] Error during audio capture: {e}")
            return None
        finally:
            self._is_recording = False

        if not recorded_frames or (time.time() - start_time) < self.min_duration:
            return None

        # Concatenate all audio frames
        full_audio = np.concatenate(recorded_frames, axis=0)
        
        # Check if the captured audio had any significant energy
        overall_rms = np.sqrt(np.mean(full_audio**2))
        if overall_rms < (self.silence_threshold * 0.5):
            return None
            
        # Convert float32 [-1.0, 1.0] to int16 PCM
        audio_int16 = (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16)
        
        # Write to in-memory WAV buffer
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_int16, self.sample_rate, format='WAV', subtype='PCM_16')
        wav_buffer.seek(0)
        
        return wav_buffer
