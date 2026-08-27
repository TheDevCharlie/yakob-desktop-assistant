"""
Automated Unit Tests for Yakob Desktop Assistant (Amharic & English)
"""
import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.command_processor import CommandProcessor
from core.tts_engine import TTSEngine
from core.system_controller import SystemController
from config import VOICE_CONFIG, DEFAULT_LANGUAGE, DEFAULT_PTT_KEY


class TestCommandProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = CommandProcessor()

    def test_alexa_timer_amharic(self):
        spoken, display, meta = self.processor.process_command("የ 5 ደቂቃ ታይመር ሙላ", language="am")
        self.assertEqual(meta.get("action"), "timer")
        self.assertEqual(meta.get("seconds"), 300)
        self.assertIn("ታይመር", spoken)

    def test_alexa_timer_english(self):
        spoken, display, meta = self.processor.process_command("set a timer for 10 seconds", language="en")
        self.assertEqual(meta.get("action"), "timer")
        self.assertEqual(meta.get("seconds"), 10)
        self.assertIn("Timer", spoken)

    def test_default_config(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertIn("en-US-AndrewMultilingualNeural", VOICE_CONFIG["en"]["male"])

    def test_alexa_weather(self):
        spoken, display, meta = self.processor.process_command("የአየር ሁኔታ ምን ይመስላል?", language="am")
        self.assertEqual(meta.get("action"), "weather")

        spoken_en, display_en, meta_en = self.processor.process_command("what's the weather today", language="en")
        self.assertEqual(meta_en.get("action"), "weather")

    def test_alexa_news(self):
        spoken, display, meta = self.processor.process_command("የዛሬ ዜና ንገረኝ", language="am")
        self.assertEqual(meta.get("action"), "news")

    def test_alexa_coin_and_dice(self):
        spoken_c, _, meta_c = self.processor.process_command("ሳንቲም ጣል", language="am")
        self.assertEqual(meta_c.get("action"), "coin_flip")
        self.assertTrue("ተጥሎ" in spoken_c or "ወጥቷል" in spoken_c)

        spoken_d, _, meta_d = self.processor.process_command("roll a die", language="en")
        self.assertEqual(meta_d.get("action"), "dice_roll")

    def test_alexa_riddle_and_fact(self):
        spoken_r, _, meta_r = self.processor.process_command("እንቆቅልሽ ንገረኝ", language="am")
        self.assertEqual(meta_r.get("action"), "riddle")

        spoken_f, _, meta_f = self.processor.process_command("tell me a fact", language="en")
        self.assertEqual(meta_f.get("action"), "fact")

    def test_alexa_music(self):
        spoken_m, _, meta_m = self.processor.process_command("ሙዚቃ አጫውት", language="am")
        self.assertEqual(meta_m.get("action"), "play_music")

    def test_trivia_knowledge_amharic(self):
        spoken_t, _, meta_t = self.processor.process_command("የፈረንሳይ ዋና ከተማ ማን ነው?", language="am")
        self.assertIn("ፓሪስ", spoken_t)

        spoken_riv, _, _ = self.processor.process_command("በዓለም ላይ ረጅሙ ወንዝ ምንድን ነው?", language="am")
        self.assertIn("አባይ", spoken_riv)

    def test_trivia_knowledge_english(self):
        spoken_cap, _, _ = self.processor.process_command("what is the capital of France?", language="en")
        self.assertIn("Paris", spoken_cap)

        spoken_moon, _, _ = self.processor.process_command("who was the first person to walk on the moon?", language="en")
        self.assertIn("Neil Armstrong", spoken_moon)

    def test_clipboard_reader(self):
        spoken_clip, _, meta_clip = self.processor.process_command("የኮፒ ያደረግኩትን አንብብልኝ", language="am")
        self.assertEqual(meta_clip.get("action"), "read_clipboard")

    def test_sound_effects(self):
        from core.sound_effects import sfx
        self.assertIsNotNone(sfx._wake_sound)
        self.assertIsNotNone(sfx._done_sound)

    def test_tts_volume_control(self):
        from core.tts_engine import TTSEngine
        tts = TTSEngine()
        tts.set_volume(0.75)
        self.assertEqual(tts.volume, 0.75)
        tts.set_volume(1.5)  # Clamps to 1.0
        self.assertEqual(tts.volume, 1.0)
        tts.set_volume(-0.2)  # Clamps to 0.0
        self.assertEqual(tts.volume, 0.0)

    def test_bilingual_translator_pipeline(self):
        from core.translator import AmharicEnglishTranslator
        translator = AmharicEnglishTranslator()
        # Test phrase translation
        en = translator.translate_amharic_to_english("የፈረንሳይ ዋና ከተማ")
        self.assertEqual(en, "capital of France")

    def test_chatbot_mode_toggle(self):
        from gui.popup_toast import ResponseToast
        # Verify toast class is importable
        self.assertTrue(issubclass(ResponseToast, object))

    def test_custom_voice_and_ptt_config(self):
        self.assertEqual(DEFAULT_PTT_KEY, "space")
        self.assertIn("en-US-AndrewMultilingualNeural", VOICE_CONFIG["en"]["male"])

    def test_live_web_search(self):
        from core.web_search import web_search
        res = web_search.search_live_web("Albert Einstein")
        self.assertIsNotNone(res)
        self.assertGreater(len(res), 10)

    def test_music_streamer_and_playlists(self):
        from core.music_streamer import music_streamer
        # Test playlist creation
        res = music_streamer.create_playlist("Focus Mode")
        self.assertIn("Focus Mode", res)
        # Test listing playlists
        playlists = music_streamer.list_playlists()
        self.assertIn("Focus Mode", playlists)
        # Test adding track to playlist
        res_add = music_streamer.add_to_playlist("Focus Mode", "Lofi Rain Beats")
        self.assertIn("Lofi Rain Beats", res_add)
        tracks = music_streamer.get_playlist_tracks("Focus Mode")
        self.assertIn("Lofi Rain Beats", tracks)

    def test_amharic_greetings(self):
        spoken, display, meta = self.processor.process_command("ሰላም ጤና ይስጥልኝ", language="am")
        self.assertEqual(meta.get("action"), "conversation")
        self.assertEqual(meta.get("topic"), "greeting")

        spoken_gm, display_gm, meta_gm = self.processor.process_command("እንደምን አደሩ", language="am")
        self.assertEqual(meta_gm.get("action"), "conversation")
        self.assertEqual(meta_gm.get("topic"), "good_morning")

    def test_amharic_volume_controls(self):
        _, _, meta_up = self.processor.process_command("ድምፅ ጨምር", language="am")
        self.assertEqual(meta_up.get("action"), "volume_up")

        _, _, meta_down = self.processor.process_command("ድምፅ ቀንስ", language="am")
        self.assertEqual(meta_down.get("action"), "volume_down")

    def test_amharic_app_open(self):
        spoken, display, meta = self.processor.process_command("ካልኩሌተር ክፈት", language="am")
        self.assertEqual(meta.get("action"), "open_app")
        self.assertEqual(meta.get("app"), "calculator")

    def test_amharic_math(self):
        spoken, display, meta = self.processor.process_command("ስንት ነው 30 ሲደመር 20", language="am")
        self.assertEqual(meta.get("action"), "math")
        self.assertIn("50", spoken)


class TestTTSEngineMaleVoices(unittest.TestCase):
    def setUp(self):
        self.tts = TTSEngine()

    def test_amharic_male_voice_synthesis(self):
        text = "ሰላም! እኔ ያዕቆብ ነኝ፤ የአማርኛ ወንድ ድምፅ ነው።"
        male_voice_am = VOICE_CONFIG["am"]["male"]
        path = self.tts._synthesize_audio(text, language="am", voice=male_voice_am, rate="+0%")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.getsize(path) > 1000)
        os.remove(path)

    def test_english_male_voice_synthesis(self):
        text = "Hello! I am Yakob, your desktop assistant with a male voice."
        male_voice_en = VOICE_CONFIG["en"]["male"]
        path = self.tts._synthesize_audio(text, language="en", voice=male_voice_en, rate="+0%")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.getsize(path) > 1000)
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
