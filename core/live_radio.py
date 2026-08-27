"""
True 24/7 Live Broadcast Radio Streaming Engine for Yakob Assistant.
Streams direct real-time Icecast, Shoutcast, and HLS online radio feeds
directly from official broadcast station servers without YouTube.
"""
import subprocess
import threading
import time
import numpy as np
import sounddevice as sd
import imageio_ffmpeg
from typing import Optional, List, Dict, Callable

from core.radio_stations import RADIO_STATIONS, find_radio_station


class LiveRadioStreamer:
    def __init__(self):
        self.current_station: Optional[Dict[str, str]] = None
        self.is_paused = False
        self.volume = 0.85
        self._proc: Optional[subprocess.Popen] = None
        self._stream: Optional[sd.RawOutputStream] = None
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        self._on_status_cb: Optional[Callable[[str], None]] = None
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def is_playing(self) -> bool:
        return self._proc is not None and not self.is_paused and not self._stop_requested

    def get_current_station(self) -> Optional[str]:
        if self.current_station:
            return self.current_station.get("name")
        return None

    def list_stations(self) -> List[Dict[str, str]]:
        return list(RADIO_STATIONS.values())

    def play_station(self, query: str, on_status_change: Optional[Callable[[str], None]] = None) -> str:
        """
        Tunes into direct live radio stream URL from official radio servers.
        """
        self.stop()
        self._stop_requested = False
        self._on_status_cb = on_status_change

        station = find_radio_station(query)
        if not station:
            station = RADIO_STATIONS.get("sheger fm")

        self.current_station = station
        station_name = station["name"]
        stream_url = station["url"]

        if on_status_change:
            on_status_change(f"Connecting: {station_name[:24]}...")

        def _stream_worker():
            active_url = stream_url
            for attempt in range(2):
                try:
                    cmd = [
                        self.ffmpeg_exe,
                        "-reconnect", "1",
                        "-reconnect_streamed", "1",
                        "-reconnect_delay_max", "5",
                        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "-i", active_url,
                        "-f", "s16le",
                        "-ar", "44100",
                        "-ac", "2",
                        "-"
                    ]

                    self._proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        bufsize=1024 * 64
                    )

                    self._stream = sd.RawOutputStream(
                        samplerate=44100,
                        channels=2,
                        dtype='int16'
                    )
                    self._stream.start()
                    self.is_paused = False

                    chunk_size = 4096
                    first_chunk = self._proc.stdout.read(chunk_size)
                    if not first_chunk:
                        # Fallback to secondary mirror if initial stream fails
                        if attempt == 0 and station.get("fallback_url"):
                            active_url = station.get("fallback_url")
                            self._cleanup()
                            continue
                        break

                    if on_status_change:
                        on_status_change(f"Live: {station_name[:24]}")

                    self._stream.write(first_chunk)

                    while not self._stop_requested and self._proc:
                        if self.is_paused:
                            time.sleep(0.1)
                            continue

                        raw_data = self._proc.stdout.read(chunk_size)
                        if not raw_data:
                            break

                        # Apply real-time volume scaling
                        if self.volume < 0.99:
                            audio_np = np.frombuffer(raw_data, dtype=np.int16)
                            scaled_np = (audio_np * self.volume).astype(np.int16)
                            self._stream.write(scaled_np.tobytes())
                        else:
                            self._stream.write(raw_data)

                    break
                except Exception as e:
                    print(f"[LiveRadio] Stream note (attempt {attempt}): {e}")
                    if attempt == 0 and station.get("fallback_url"):
                        active_url = station.get("fallback_url")
                        self._cleanup()
                        continue
                    if on_status_change:
                        on_status_change("Stream disconnected")
                    break
                finally:
                    self._cleanup()

        self._stream_thread = threading.Thread(target=_stream_worker, daemon=True)
        self._stream_thread.start()
        return f"Tuning into live {station_name}..."

    def pause(self):
        """Pauses live radio playback."""
        self.is_paused = True

    def unpause(self):
        """Resumes live radio playback."""
        self.is_paused = False

    def stop(self):
        """Halts live radio immediately."""
        self._stop_requested = True
        self._cleanup()
        self.current_station = None
        self.is_paused = False

    def set_volume(self, level: float):
        """Sets live radio volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, float(level)))

    def _cleanup(self):
        if self._proc:
            try:
                if self._proc.stdout:
                    self._proc.stdout.close()
                self._proc.kill()
            except Exception:
                pass
            self._proc = None

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None


# Global Singleton Instance
live_radio = LiveRadioStreamer()
