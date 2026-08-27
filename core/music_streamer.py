"""
Built-in YouTube Music Streamer & Playlist Curator for Yakob Assistant.
Downloads audio tracks directly via yt-dlp & imageio-ffmpeg into MP3 cache,
and streams them seamlessly via pygame.mixer with full playback controls.
"""
import os
import re
import json
import time
import tempfile
import threading
import pygame
from typing import Optional, List, Dict, Callable
import yt_dlp
import imageio_ffmpeg

PLAYLISTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "playlists.json")
MUSIC_CACHE_DIR = os.path.join(tempfile.gettempdir(), "yakob_music_cache")
os.makedirs(MUSIC_CACHE_DIR, exist_ok=True)


class MusicStreamer:
    def __init__(self):
        self.current_track = None
        self.is_paused = False
        self.volume = 0.85
        self.current_playlist_name: Optional[str] = None
        self.current_playlist_queue: List[str] = []
        self.current_playlist_index = 0
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        self._on_track_change_cb: Optional[Callable[[str], None]] = None
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        self._ensure_pygame_audio()

    def _ensure_pygame_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except Exception as e:
            print(f"[MusicStreamer] Pygame audio init note: {e}")

    def is_playing(self) -> bool:
        try:
            return pygame.mixer.music.get_busy() and not self.is_paused
        except Exception:
            return False

    def get_current_track(self) -> Optional[str]:
        return self.current_track

    def _clean_text(self, text: str) -> str:
        """Strips emojis and problematic characters for safe UI rendering."""
        clean = re.sub(r'[^\w\s\-\.\,\(\)\'\:\?\!\/]', '', text)
        return clean.strip() or "Track"

    def play(self, query: str, on_status_change: Optional[Callable[[str], None]] = None) -> str:
        """
        Searches YouTube for query, converts track to MP3, and plays in background.
        """
        self.stop()
        self._stop_requested = False
        self._on_track_change_cb = on_status_change

        def _worker():
            try:
                clean_q = self._clean_text(query)
                if on_status_change:
                    on_status_change(f"Searching: '{clean_q[:24]}...'")

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'default_search': 'ytsearch1:',
                    'noplaylist': True,
                    'quiet': True,
                    'no_warnings': True,
                    'ffmpeg_location': self.ffmpeg_exe,
                    'outtmpl': os.path.join(MUSIC_CACHE_DIR, '%(id)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=True)
                    if 'entries' in info and len(info['entries']) > 0:
                        track_info = info['entries'][0]
                    else:
                        track_info = info

                    track_id = track_info.get('id')
                    raw_title = track_info.get('title', query)
                    title = self._clean_text(raw_title)
                    self.current_track = title

                    mp3_path = os.path.join(MUSIC_CACHE_DIR, f"{track_id}.mp3")
                    
                    if not os.path.exists(mp3_path):
                        # Try searching for any file with track_id in cache
                        for fname in os.listdir(MUSIC_CACHE_DIR):
                            if fname.startswith(track_id):
                                mp3_path = os.path.join(MUSIC_CACHE_DIR, fname)
                                break

                    if self._stop_requested:
                        return

                    if os.path.exists(mp3_path):
                        self._ensure_pygame_audio()
                        pygame.mixer.music.load(mp3_path)
                        pygame.mixer.music.set_volume(self.volume)
                        pygame.mixer.music.play()
                        self.is_paused = False

                        if on_status_change:
                            on_status_change(f"Playing: {title[:28]}")

                        # Monitor playback loop
                        while pygame.mixer.music.get_busy() and not self._stop_requested:
                            time.sleep(0.5)

                        # Auto-play next in playlist if active
                        if not self._stop_requested and self.current_playlist_queue:
                            self._play_next_in_playlist()
                    else:
                        if on_status_change:
                            on_status_change("Audio file not found")

            except Exception as e:
                print(f"[MusicStreamer] Play error: {e}")
                if on_status_change:
                    on_status_change("Could not load track")

        self._playback_thread = threading.Thread(target=_worker, daemon=True)
        self._playback_thread.start()
        return f"Streaming '{query}'..."

    def pause(self):
        """Pauses active playback."""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.is_paused = True
        except Exception:
            pass

    def unpause(self):
        """Resumes paused playback."""
        try:
            pygame.mixer.music.unpause()
            self.is_paused = False
        except Exception:
            pass

    def stop(self):
        """Halts playback immediately."""
        self._stop_requested = True
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        self.current_track = None
        self.is_paused = False

    def set_volume(self, level: float):
        """Sets music volume between 0.0 and 1.0."""
        self.volume = max(0.0, min(1.0, float(level)))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    # -------------------------------------------------------------
    # PLAYLIST CURATION SYSTEM
    # -------------------------------------------------------------
    def _load_playlists(self) -> Dict[str, List[str]]:
        if not os.path.exists(PLAYLISTS_FILE):
            default_data = {
                "Chill Vibes": ["lofi hip hop beats", "ethiopian acoustic instrumental"],
                "Favorites": ["The Weeknd Starboy official audio", "Teddy Afro Ethiopia official audio"]
            }
            self._save_playlists(default_data)
            return default_data
        try:
            with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_playlists(self, data: Dict[str, List[str]]):
        try:
            with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MusicStreamer] Save playlist error: {e}")

    def create_playlist(self, name: str) -> str:
        data = self._load_playlists()
        name = name.strip().title()
        if name not in data:
            data[name] = []
            self._save_playlists(data)
            return f"Created playlist '{name}'."
        return f"Playlist '{name}' already exists."

    def add_to_playlist(self, playlist_name: str, song: str) -> str:
        data = self._load_playlists()
        playlist_name = playlist_name.strip().title()
        if playlist_name not in data:
            data[playlist_name] = []
        
        song = song.strip()
        if song not in data[playlist_name]:
            data[playlist_name].append(song)
            self._save_playlists(data)
            return f"Added '{song}' to playlist '{playlist_name}'."
        return f"'{song}' is already in playlist '{playlist_name}'."

    def list_playlists(self) -> List[str]:
        data = self._load_playlists()
        return list(data.keys())

    def get_playlist_tracks(self, playlist_name: str) -> List[str]:
        data = self._load_playlists()
        playlist_name = playlist_name.strip().title()
        return data.get(playlist_name, [])

    def play_playlist(self, playlist_name: str, on_status_change: Optional[Callable[[str], None]] = None) -> str:
        data = self._load_playlists()
        playlist_name = playlist_name.strip().title()
        if playlist_name not in data or not data[playlist_name]:
            return f"Playlist '{playlist_name}' is empty or does not exist."

        self.current_playlist_name = playlist_name
        self.current_playlist_queue = list(data[playlist_name])
        self.current_playlist_index = 0
        self._on_track_change_cb = on_status_change

        first_song = self.current_playlist_queue[0]
        self.play(first_song, on_status_change=on_status_change)
        return f"Playing playlist '{playlist_name}' ({len(self.current_playlist_queue)} tracks)."

    def next_track(self, on_status_change: Optional[Callable[[str], None]] = None) -> str:
        """Skips to the next track in current playlist queue."""
        if not self.current_playlist_queue:
            return "No playlist is currently playing."
        
        self.current_playlist_index = (self.current_playlist_index + 1) % len(self.current_playlist_queue)
        next_song = self.current_playlist_queue[self.current_playlist_index]
        self.play(next_song, on_status_change=on_status_change or self._on_track_change_cb)
        return f"Skipping to '{next_song}'."

    def _play_next_in_playlist(self):
        if self.current_playlist_queue:
            self.current_playlist_index = (self.current_playlist_index + 1) % len(self.current_playlist_queue)
            next_song = self.current_playlist_queue[self.current_playlist_index]
            self.play(next_song, on_status_change=self._on_track_change_cb)


# Global Singleton Instance
music_streamer = MusicStreamer()
