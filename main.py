import sys
import os
import argparse

# Enable UTF-8 encoding on Windows console for Ge'ez / Amharic text support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Yakob (ያዕቆብ) - Multilingual Desktop Voice Assistant (Amharic & English)")
    parser.add_argument("--cli", action="store_true", help="Run in interactive Terminal / CLI mode")
    parser.add_argument("--lang", default="am", choices=["am", "en", "auto"], help="Default language (am/en/auto)")
    args = parser.parse_args()

    if args.cli:
        run_cli_mode(args.lang)
    else:
        run_gui_mode()


def run_gui_mode():
    try:
        from gui.app_window import AssistantApp
        app = AssistantApp()
        app.mainloop()
    except Exception as e:
        print(f"[Main] GUI encountered an error: {e}")
        print("[Main] Launching CLI fallback mode...")
        run_cli_mode("am")


def run_cli_mode(initial_lang="am"):
    print("=" * 70)
    print("🎙️  YAKOB (ያዕቆብ) - DESKTOP VOICE ASSISTANT [MALE VOICE]")
    print("   ቋንቋዎች / Languages: አማርኛ (Amharic) & English")
    print("   Alexa-Style Utilities: Timers, Weather, News, Coin Flip, Dice, Riddles")
    print("   Type 'exit' or 'ውጣ' to quit.")
    print("   Type ':mic' to record from microphone.")
    print("   Type ':commands' or ':help' to print all available voice commands.")
    print("=" * 70)

    from core.command_processor import CommandProcessor
    from core.tts_engine import TTSEngine
    from core.audio_recorder import AudioRecorder
    from core.speech_recognizer import SpeechRecognizer
    from config import VOICE_CONFIG

    cmd_proc = CommandProcessor()
    tts = TTSEngine()
    recorder = AudioRecorder()
    recognizer = SpeechRecognizer()
    lang = initial_lang

    while True:
        try:
            user_input = input(f"\n[{lang.upper()}] You > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "ውጣ", "ዝጋ"]:
                print("👋 Bye! ደህና ሁኑ!")
                break

            if user_input.lower() in [":commands", ":help", "commands", "ትእዛዞች"]:
                print_commands_cheatsheet()
                continue

            if user_input.startswith(":lang"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1] in ["am", "en", "auto"]:
                    lang = parts[1]
                    print(f"Language set to: {lang}")
                continue

            if user_input == ":mic":
                print("🎙️ Listening for speech (speak into mic)...")
                wav_buf = recorder.record_audio_buffer()
                if not wav_buf:
                    print("⚠️ No speech captured.")
                    continue
                print("🔄 Transcribing...")
                text, detected_lang, err = recognizer.transcribe_wav_buffer(wav_buf, language=lang)
                if not text:
                    print(f"⚠️ Speech recognition error: {err}")
                    continue
                print(f"🧑 Recognized [{detected_lang}]: {text}")
                user_input = text
                lang = detected_lang or lang

            spoken, display, meta = cmd_proc.process_command(user_input, language=lang)
            print(f"🤖 Yakob > {display}")
            if spoken:
                voice = VOICE_CONFIG.get(lang, VOICE_CONFIG["am"])["male"]
                tts.speak(spoken, language=lang, voice=voice, block=True)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


def print_commands_cheatsheet():
    print("""
========================================================================================
📋 YAKOB (ያዕቆብ) - AVAILABLE VOICE COMMANDS CHEATSHEET
========================================================================================
🇪🇹 አማርኛ (Amharic Voice Commands):
  ⏱️ ታይመርና አላርም:
     - "የ 5 ደቂቃ ታይመር ሙላ" / "የ 10 ሰከንድ ታይመር" / "ለ 2 ደቂቃ ታይመር"
  ☀️ የአየር ሁኔታ (Weather):
     - "የአየር ሁኔታ ምን ይመስላል?" / "የዛሬ የአየር ሁኔታ" / "አዲስ አበባ የአየር ሁኔታ"
  📰 ዜና (News Headlines):
     - "የዛሬ ዜና ንገረኝ" / "አዳዲስ ዜናዎች" / "ዜና"
  🪙 ሳንቲም & ዳይስ (Coin & Dice):
     - "ሳንቲም ጣል" (ሰው ወይስ ቁጥር / Heads or Tails)
     - "ዳይስ ጣል" (1 እስከ 6 ቁጥር ይወጣል)
  🧩 እንቆቅልሽ & እውነታዎች (Riddles & Facts):
     - "እንቆቅልሽ ንገረኝ" (ጥያቄና መልስ)
     - "አስገራሚ እውነታ ንገረኝ" / "የሚገርም ነገር"
     - "ጥቅስ ንገረኝ" / "የዕለቱ ጥቅስ" (አነቃቂ ንግግር)
  🎵 ሙዚቃ ማጫወት (Music):
     - "ሙዚቃ አጫውት" / "ሙዚቃ ክፈት" / "ዩቲዩብ ላይ የኢትዮጵያ ሙዚቃ ፈልግ"
  🚀 መተግበሪያዎች መክፈት (Open Apps):
     - "ክሮምን ክፈት", "ካልኩሌተር ክፈት", "ኖትፓድ ክፈት", "ፋይል ኤክስፕሎረር ክፈት"
     - "ቪኤስ ኮድ ክፈት", "ሴቲንግ ክፈት", "ካሜራ ክፈት", "ፔይንት ክፈት", "ቴሌግራም ክፈት"
  🕒 ሰዓትና ቀን (Time & Date):
     - "ስንት ሰዓት ነው?" / "ዛሬ ምን ቀን ነው?"
  ⚙️ የኮምፒውተር ቁጥጥር (PC Controls):
     - "ድምፅ ጨምር" / "ድምፅ ቀንስ" / "ድምፅ አጥፋ (Mute)"
     - "ስክሪንሾት አንሳ" (Pictures ማህደር ውስጥ ይቀመጣል)
     - "የባትሪ መጠን ስንት ነው?" / "ኮምፒውተሩን ቆልፍ"
  🧮 ሒሳብ ማስላት (Math):
     - "ስንት ነው 25 ሲደመር 40", "50 ሲባዛ በ 3", "100 ሲካፈል ለ 4"
  💬 ንግግርና ሰላምታ (Casual Chat):
     - "ሰላም እንደምን አደሩ", "ማን ነህ?", "እንዴት ነህ?", "ቀልድ ንገረኝ", "ዘፈን ዘፍን", "ደህና እደር"

----------------------------------------------------------------------------------------
🇬🇧 English Voice Commands:
  ⏱️ Timers & Alarms:
     - "Set a timer for 5 minutes", "Timer for 30 seconds", "Set a 2 minute timer"
  ☀️ Weather Forecast:
     - "What's the weather like?", "What's the weather in Addis Ababa?", "Today's forecast"
  📰 News:
     - "What's the latest news?", "Tell me the news", "Today's headlines"
  🪙 Coin Flip & Dice Roll:
     - "Flip a coin", "Toss a coin", "Roll a die", "Roll a dice"
  🧩 Riddles, Facts & Inspiration:
     - "Tell me a riddle", "Tell me a fact", "Did you know?", "Tell me a quote"
  🎵 Music:
     - "Play music", "Play songs on YouTube", "Play The Weeknd"
  🚀 Launch Applications:
     - "Open Chrome", "Open Calculator", "Open Notepad", "Launch VS Code", "Open Settings"
  🕒 Time & Date:
     - "What time is it?", "What is today's date?"
  ⚙️ System Controls:
     - "Volume up", "Volume down", "Mute volume", "Take screenshot", "Battery status", "Lock PC"
  🧮 Spoken Math:
     - "What is 45 plus 55", "What is 20 times 8", "Calculate 150 divided by 3"
  💬 Conversation:
     - "Good morning", "Who are you?", "How are you?", "Tell me a joke", "Sing a song", "Good night"
========================================================================================
""")


if __name__ == "__main__":
    main()
