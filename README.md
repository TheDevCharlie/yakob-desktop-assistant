# 🎙️ Yakob (ያዕቆብ) - Multilingual Desktop Assistant (አማርኛ & English)

A modern, hands-free intelligent desktop voice assistant designed for Windows with native **Amharic (አማርኛ)** and **English** speech recognition, crisp **Male Neural Text-to-Speech** (powered by `am-ET-AmehaNeural` & `en-US-GuyNeural`), Alexa-style daily utilities (timers, weather, news, coin toss, dice, riddles, facts), and Windows application launching.

---

## ✨ Key Features

- **🗣️ Multilingual Speech Recognition**:
  - Full support for **Amharic (አማርኛ)** (`am-ET`) and **English** (`en-US`).
  - Automatic language detection / dual-mode recognition.
- **🔊 Male Neural Text-to-Speech (TTS)**:
  - **Amharic Male**: `am-ET-AmehaNeural` (with optional female `am-ET-MekdesNeural`).
  - **English Male**: `en-US-GuyNeural` (with optional female `en-US-JennyNeural`).
  - Built-in fallback to `gTTS`.
- **⏱️ Alexa-Style Day-to-Day Utilities**:
  - **Timers & Alarms**: Set custom duration timers with automatic audio chime and voice notification.
  - **Live Weather Forecast**: Instant temperature, humidity, and condition report for Addis Ababa or any global city.
  - **News & Headlines**: Instant access to top news and headlines.
  - **Coin Flip & Dice Roll**: Random coin toss (*"ሰው ወይስ ቁጥር / Heads or Tails"*) and 6-sided dice roll.
  - **Riddles, Facts & Inspiration**: Interactive Amharic and English riddles (*እንቆቅልሽ*), interesting trivia facts, and motivational quotes.
  - **Music & Songs**: Play any song or artist on YouTube or Spotify.
- **🚀 Desktop Application Launcher**:
  - Chrome, Edge, Firefox, Calculator, Notepad, File Explorer, Task Manager, Settings, Camera, Paint, Command Prompt, PowerShell, VS Code, Spotify, Telegram, MS Office.
- **⚙️ Windows System Automation**:
  - Adjust master volume (Up, Down, Mute/Unmute).
  - Desktop screenshots (saved to `Pictures` folder).
  - Battery percentage and power status.
  - Time and date in Amharic & English.
  - Lock computer workstation.

---

## 🚀 How to Run

### 1. Launch with One Click
Double-click:
```bat
run_assistant.bat
```

### 2. Launch via Terminal / PowerShell
```bash
cd "C:\Users\HP\.gemini\antigravity\scratch\desktop-assistant"
python main.py
```

### 3. Lightweight CLI Mode
```bash
python main.py --cli --lang am
```

---

## 📋 Comprehensive Voice Commands Reference

### 🇪🇹 የአማርኛ ትእዛዛት (Amharic Voice Commands)

| ምድብ (Category) | የድምፅ ትእዛዝ ምሳሌዎች (Spoken Command Examples) |
|---|---|
| ⏱️ **ታይመርና አላርም** | `"የ 5 ደቂቃ ታይመር ሙላ"`, `"የ 10 ሰከንድ ታይመር"`, `"ለ 2 ደቂቃ ታይመር"` |
| ☀️ **የአየር ሁኔታ (Weather)** | `"የአየር ሁኔታ ምን ይመስላል?"`, `"የዛሬ የአየር ሁኔታ"`, `"አዲስ አበባ የአየር ሁኔታ"` |
| 📰 **ዜና (News)** | `"የዛሬ ዜና ንገረኝ"`, `"አዳዲስ ዜናዎች"`, `"ዜና"` |
| 🪙 **ሳንቲም ጣል (Coin Flip)** | `"ሳንቲም ጣል"`, `"ሰው ወይስ ቁጥር"` |
| 🎲 **ዳይስ ጣል (Dice Roll)** | `"ዳይስ ጣል"`, `"ዳይስ"` |
| 🧩 **እንቆቅልሽ (Riddles)** | `"እንቆቅልሽ ንገረኝ"`, `"እንቆቅልሽ"` |
| 💡 **አስገራሚ እውነታ (Facts)** | `"አስገራሚ እውነታ ንገረኝ"`, `"የሚገርም ነገር ንገረኝ"`, `"እውነታ"` |
| 📜 **የዕለቱ ጥቅስ (Quotes)** | `"ጥቅስ ንገረኝ"`, `"የዕለቱ ጥቅስ"`, `"አነቃቂ ንግግር"` |
| 🎵 **ሙዚቃ (Music)** | `"ሙዚቃ አጫውት"`, `"ዘፈን ክፈትልኝ"`, `"ዩቲዩብ ላይ የኢትዮጵያ ሙዚቃ ፈልግ"` |
| 🚀 **መተግበሪያ መክፈት (Apps)** | `"ክሮምን ክፈት"`, `"ካልኩሌተር ክፈት"`, `"ኖትፓድ ክፈት"`, `"ፋይል ኤክስፕሎረር ክፈት"`, `"ቪኤስ ኮድ ክፈት"`, `"ሴቲንግ ክፈት"`, `"ካሜራ ክፈት"` |
| 🔍 **ኢንተርኔት ላይ መፈለግ** | `"ስለ ኢትዮጵያ ፈልግ"`, `"ስለ አርቴፊሻል ኢንተለጀንስ በጎግል ፈልግ"` |
| 🕒 **ሰዓትና ቀን (Time & Date)** | `"ስንት ሰዓት ነው?"`, `"ዛሬ ምን ቀን ነው?"` |
| 🔊 **ድምፅ መቆጣጠር (Volume)** | `"ድምፅ ጨምር"`, `"ድምፅ ቀንስ"`, `"ድምፅ አጥፋ / ድምፅ ዝጋ"` |
| 📸 **ስክሪንሾት ማንሳት** | `"ስክሪንሾት አንሳ"`, `"ስክሪኑን ፎቶ አንሳ"` |
| 🔋 **ባትሪ ማወቅ** | `"የባትሪ መጠን ስንት ነው?"`, `"ባትሪ"` |
| 🔒 **ኮምፒውተር መቆለፍ** | `"ኮምፒውተሩን ቆልፍ"` |
| 🧮 **ሒሳብ ማስላት (Math)** | `"ስንት ነው 45 ሲደመር 30"`, `"50 ሲባዛ በ 4"`, `"100 ሲካፈል ለ 5"` |
| 💬 **ሰላምታና ንግግር** | `"ሰላም እንደምን አደሩ"`, `"ማን ነህ?"`, `"እንዴት ነህ?"`, `"ቀልድ ንገረኝ"`, `"ዘፈን ዘፍን"`, `"ደህና እደር"`, `"አመሰግናለሁ"` |

---

### 🇬🇧 English Voice Commands

| Category | Spoken Command Examples |
|---|---|
| ⏱️ **Timers & Alarms** | `"Set a timer for 5 minutes"`, `"Timer for 30 seconds"`, `"Set a 2 minute timer"` |
| ☀️ **Weather Forecast** | `"What's the weather like?"`, `"What's the weather in Addis Ababa?"`, `"Today's forecast"` |
| 📰 **News Headlines** | `"What's the latest news?"`, `"Tell me the news"`, `"Today's headlines"` |
| 🪙 **Coin Flip & Dice** | `"Flip a coin"`, `"Toss a coin"`, `"Roll a die"`, `"Roll a dice"` |
| 🧩 **Riddles & Trivia** | `"Tell me a riddle"`, `"Tell me a fact"`, `"Did you know?"`, `"Tell me a quote"` |
| 🎵 **Music & Playback** | `"Play music"`, `"Play songs on YouTube"`, `"Play The Weeknd on YouTube"` |
| 🚀 **Launch Applications** | `"Open Chrome"`, `"Open Calculator"`, `"Open Notepad"`, `"Launch VS Code"`, `"Open Settings"`, `"Open Camera"` |
| 🔍 **Web Search** | `"Search for Python tutorials"`, `"Look up latest technology trends"` |
| 🕒 **Time & Date** | `"What time is it?"`, `"What is today's date?"` |
| 🔊 **Volume Control** | `"Volume up"`, `"Volume down"`, `"Mute volume"` |
| 📸 **Screenshot** | `"Take screenshot"`, `"Capture screen"` |
| 🔋 **Battery Status** | `"Check battery level"`, `"Power status"` |
| 🔒 **Lock Computer** | `"Lock computer"`, `"Lock PC"` |
| 🧮 **Spoken Math** | `"What is 45 plus 55"`, `"What is 20 times 8"`, `"Calculate 150 divided by 3"` |
| 💬 **Casual Conversation** | `"Good morning"`, `"Who are you?"`, `"How are you?"`, `"Tell me a joke"`, `"Sing a song"`, `"Good night"`, `"Thank you"` |
