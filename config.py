"""
Configuration and settings for Yakob - The Multilingual Desktop Assistant (English & Amharic).
"""
import os
from pathlib import Path

# Assistant Metadata
ASSISTANT_NAME = "Yakob"
ASSISTANT_NAME_AM = "ያዕቆብ"
ASSISTANT_VERSION = "2.0.0"

# Language & Default Male Voice Configuration
DEFAULT_LANGUAGE = "am"  # "am" (Amharic), "en" (English), or "auto"
DEFAULT_SPEECH_RATE = "+15%"  # Lively, fast, conversational speech speed

VOICE_CONFIG = {
    "am": {
        "male": "am-ET-AmehaNeural",          # Default Male Voice
        "female": "am-ET-MekdesNeural",
        "default": "am-ET-AmehaNeural",        # Set to Male by default
        "stt_code": "am-ET",
        "name": "አማርኛ (Amharic)"
    },
    "en": {
        "male": "en-US-AndrewMultilingualNeural",  # Ultra-modern natural multilingual male voice
        "male_alt": "en-US-GuyNeural",
        "female": "en-US-AvaMultilingualNeural",
        "female_alt": "en-US-JennyNeural",
        "default": "en-US-AndrewMultilingualNeural",
        "stt_code": "en-US",
        "name": "English"
    }
}

# Audio Recording Settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
SILENCE_THRESHOLD = 0.015  # RMS audio energy threshold
SILENCE_DURATION = 1.6     # Seconds of silence to consider speech finished
RECORD_MAX_SECONDS = 12    # Max seconds per voice command
RECORD_MIN_SECONDS = 1.0   # Min recording length

# Desktop Application Aliases & Executable Names
APPLICATION_COMMANDS = {
    # Browsers
    "chrome": {
        "aliases": ["chrome", "google chrome", "ጎግል ክሮም", "ክሮም", "ክሮምን"],
        "command": "chrome",
        "path_fallbacks": [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    },
    "edge": {
        "aliases": ["edge", "microsoft edge", "ኤጅ", "ማይክሮሶፍት ኤጅ", "ኤጅን"],
        "command": "msedge",
        "path_fallbacks": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
    },
    "firefox": {
        "aliases": ["firefox", "ሞዚላ", "ፋየርፎክስ", "ሞዚላ ፋየርፎክስ"],
        "command": "firefox",
        "path_fallbacks": [
            os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
        ]
    },
    
    # Utilities & Tools
    "notepad": {
        "aliases": ["notepad", "text editor", "ኖትፓድ", "ኖት ፓድ", "ፅሁፍ መጻፊያ", "ማስታወሻ"],
        "command": "notepad"
    },
    "calculator": {
        "aliases": ["calculator", "calc", "ካልኩሌተር", "ካልኩሌተሩን", "ማስያ"],
        "command": "calc"
    },
    "explorer": {
        "aliases": ["file explorer", "explorer", "files", "my computer", "ፋይል", "ፋይል ኤክስፕሎረር", "ኮምፒውተር", "ፋይሎች"],
        "command": "explorer"
    },
    "cmd": {
        "aliases": ["command prompt", "cmd", "terminal", "ተርሚናል", "ኮማንድ ፕሮምፕት"],
        "command": "cmd"
    },
    "powershell": {
        "aliases": ["powershell", "ፓወር ሼል", "ፓወርሼል"],
        "command": "powershell"
    },
    "taskmanager": {
        "aliases": ["task manager", "ታስክ ማናጀር", "ታስክ ማኔጀር"],
        "command": "taskmgr"
    },
    "controlpanel": {
        "aliases": ["control panel", "ኮንትሮል ፓነል"],
        "command": "control"
    },
    "settings": {
        "aliases": ["settings", "windows settings", "ሴቲንግ", "ቅንብሮች", "ቅንብር"],
        "command": "start ms-settings:"
    },
    "paint": {
        "aliases": ["paint", "mspaint", "ስዕል መሳያ", "ፔይንት", "ፔንት"],
        "command": "mspaint"
    },
    "camera": {
        "aliases": ["camera", "webcam", "ካሜራ", "ካሜራውን"],
        "command": "start microsoft.windows.camera:"
    },
    
    # Developer & Productivity Tools
    "vscode": {
        "aliases": ["vs code", "vscode", "visual studio code", "ኮድ", "ቪኤስ ኮድ"],
        "command": "code",
        "path_fallbacks": [
            os.path.expandvars(r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
        ]
    },
    "spotify": {
        "aliases": ["spotify", "ስፖቲፋይ", "ሙዚቃ ማጫወቻ"],
        "command": "spotify",
        "path_fallbacks": [
            os.path.expandvars(r"%AppData%\Spotify\Spotify.exe")
        ]
    },
    "word": {
        "aliases": ["word", "microsoft word", "ዎርድ", "ማይክሮሶፍት ዎርድ"],
        "command": "winword"
    },
    "excel": {
        "aliases": ["excel", "microsoft excel", "ኤክሴል", "ማይክሮሶፍት ኤክሴል"],
        "command": "excel"
    },
    "powerpoint": {
        "aliases": ["powerpoint", "ፓወር ፖይንት", "ፓወርፖይንት"],
        "command": "powerpnt"
    },
    "telegram": {
        "aliases": ["telegram", "ቴሌግራም", "ቴሌግራምን"],
        "command": "telegram",
        "path_fallbacks": [
            os.path.expandvars(r"%AppData%\Telegram Desktop\Telegram.exe")
        ]
    }
}

# Popular Websites & Online Services
WEBSITE_SHORTCUTS = {
    "youtube": {
        "aliases": ["youtube", "ዩቲዩብ", "ዩቱብ"],
        "url": "https://www.youtube.com"
    },
    "google": {
        "aliases": ["google", "ጎግል", "ጉግል"],
        "url": "https://www.google.com"
    },
    "github": {
        "aliases": ["github", "ጊትሃብ", "ጊት ሀብ"],
        "url": "https://www.github.com"
    },
    "chatgpt": {
        "aliases": ["chatgpt", "openai", "ቻት ጂፒቲ", "ቻትጂፒቲ"],
        "url": "https://chat.openai.com"
    },
    "facebook": {
        "aliases": ["facebook", "ፌስቡክ", "ፌስ ቡክ"],
        "url": "https://www.facebook.com"
    },
    "gmail": {
        "aliases": ["gmail", "email", "ጂሜይል", "ኢሜል"],
        "url": "https://mail.google.com"
    },
    "wikipedia": {
        "aliases": ["wikipedia", "ዊኪፔዲያ", "ውክፔዲያ"],
        "url": "https://am.wikipedia.org"
    }
}

# Alexa-Style Day-to-Day Conversational & Utility Knowledge Base
FACTS_AM = [
    "በዓለም ላይ ከ 7000 በላይ ቋንቋዎች ይነገራሉ።",
    "የሰው ልጅ ልብ በቀን ውስጥ በአማካይ 100,000 ጊዜ ይመታል።",
    "ማር ለሺህ ዓመታት ሳይበላሽ መቆየት የሚችል ብቸኛው የተፈጥሮ ምግብ ነው።",
    "ኢትዮጵያ በዓለም ላይ የራሷ የሆነ ፊደል (ግዕዝ) እና የዘመን አቆጣጠር ካላቸው ጥቂት ሀገራት አንዷ ናት።",
    "ኦክቶፐስ (Octopus) ሶስት ልቦች እና ሰማያዊ ደም አለው።"
]

FACTS_EN = [
    "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
    "Did you know? The human brain operates on about 12 to 25 watts of electricity — enough to power a small LED bulb!",
    "Did you know? Ethiopia is home to the source of the Blue Nile and is the only African nation that was never colonized.",
    "Did you know? Octopuses have three hearts and blue blood!",
    "Did you know? The shortest war in history lasted only 38 minutes between Britain and Zanzibar in 1896."
]

RIDDLES_AM = [
    ("እግሩ አራት ሆኖ መራመድ የማይችል ምን ይባላል?", "መልሱ፡ ጠረጴዛ ወይም ወንበር ነው!"),
    ("ሲወልዱት ነጭ ሲሞት ጥቁር የሚሆነው ምንድን ነው?", "መልሱ፡ የከሰል እንጨት ነው!"),
    ("እኔን በበላኸኝ ቁጥር እያነሰ የሚሄደው ምንድን ነው?", "መልሱ፡ ሻማ ነው!"),
    ("ሳያጥቡት ንፁህ የሆነ፣ ቆሻሻ የማያጣብቀው ምንድን ነው?", "መልሱ፡ ውኃ ነው!"),
    ("በቀን ይተኛል፣ በሌሊት ይነቃል፤ ዓይኑ ትልቅ ነው፣ ምን ይባላል?", "መልሱ፡ ጉጉት ነው!")
]

RIDDLES_EN = [
    ("What has to be broken before you can use it?", "An egg!"),
    ("I’m tall when I’m young, and I’m short when I’m old. What am I?", "A candle!"),
    ("What month of the year has 28 days?", "All of them!"),
    ("What is full of holes but still holds water?", "A sponge!"),
    ("What question can you never answer yes to?", "Are you asleep yet?")
]

QUOTES_AM = [
    "“ትዕግሥት መራራ ናት፣ ፍሬዋ ግን እጅግ ጣፋጭ ነው።”",
    "“የአንድ ሺህ ማይል ጉዞ በአንዲት እርምጃ ይጀምራል።”",
    "“እውቀት ሀብት ነው፤ ማንም ሊሰርቀው የማይችል ታላቅ ንብረት።”",
    "“ዛሬ የጀመርከው ጥረት የነገው ስኬትህ መሰረት ነው። ጠንክረህ ቀጥል!”"
]

QUOTES_EN = [
    "“The secret of getting ahead is getting started.” – Mark Twain",
    "“It always seems impossible until it's done.” – Nelson Mandela",
    "“Believe you can and you're halfway there.” – Theodore Roosevelt",
    "“Do what you can, with what you have, where you are.” – Theodore Roosevelt"
]

CONVERSATION_RESPONSES = {
    "greetings": {
        "am": [
            f"ሰላም! እንደምን አደሩ? እኔ {ASSISTANT_NAME_AM} ነኝ፤ ዛሬ በምን ልርዳዎት?",
            f"ሰላም ጤና ይስጥልኝ! ያዕቆብ ነኝ፣ ትእዛዝዎን ይጠብቃል።",
            f"እንደምን አለህ! ዝግጁ ነኝ፣ ምን ላድርግልዎ?"
        ],
        "en": [
            f"Hello! I am {ASSISTANT_NAME}, your desktop assistant. How can I help you today?",
            f"Hi there! {ASSISTANT_NAME} here, ready for your command.",
            f"Good day! What can I do for you today?"
        ]
    },
    "good_morning": {
        "am": [
            "ደህና አደሩ! መልካም እና የተባረከ ቀን ይሁንልዎ። የዛሬውን ዜና፣ ሰዓት ወይም የአየር ሁኔታ ማወቅ ይፈልጋሉ?",
            "እንደምን አደሩ! ዛሬ አዲስ ቀን ነው፤ መልካም የስራ ቀን ይሁንልዎ!"
        ],
        "en": [
            "Good morning! I hope you have a productive and wonderful day ahead. Would you like to check the weather or time?",
            "Good morning! Rise and shine. What can I assist you with to start your day?"
        ]
    },
    "good_night": {
        "am": [
            "መልካም አዳር ይሁንልዎ! ጣፋጭ ህልም እና ጥሩ እረፍት እመኝልዎታለሁ። ደህና እደሩ!",
            "ደህና እደሩ! ነገ በሰላም ያገናኘን።"
        ],
        "en": [
            "Good night! Sleep well and have pleasant dreams. See you tomorrow!",
            "Good night! Rest up and recharge for tomorrow."
        ]
    },
    "identity": {
        "am": [
            f"እኔ {ASSISTANT_NAME_AM} እባላለሁ፤ የእርስዎ የኮምፒውተር ድምፅ ረዳት ነኝ። መተግበሪያዎችን መክፈት፣ ኢንተርኔት ላይ መፈለግ፣ ታይመር መሙላት፣ የአየር ሁኔታና ዜና መናገር፣ ሳንቲም ወይም ዳይስ መጣል፣ እንዲሁም የኮምፒውተሮን ድምጽ መቆጣጠር እችላለሁ።",
        ],
        "en": [
            f"I am {ASSISTANT_NAME}, your personal desktop voice assistant. I can launch apps, search the web, set timers, report weather and news, flip coins, roll dice, control volume, and assist with your daily desktop tasks.",
        ]
    },
    "creator": {
        "am": [
            "እኔ የተሰራሁት የኮምፒውተርዎን ስራዎች በቀላሉ በድምፅ ትእዛዝ እንዲያከናውኑ ለማገዝ ነው።",
        ],
        "en": [
            "I was developed to make your desktop computing experience seamless and hands-free through voice commands.",
        ]
    },
    "status": {
        "am": [
            "በጣም ደህና ነኝ፣ አመሰግናለሁ! እርስዎስ እንዴት ኖት?",
            "ሁሉ ሰላም ነው! ሲስተሞች በሙሉ በተሟላ ሁኔታ እየሰሩ ነው። ምን ማከናወን ይፈልጋሉ?"
        ],
        "en": [
            "I'm operating at 100% efficiency, thank you! How are you feeling today?",
            "All systems are running great! How can I assist you right now?"
        ]
    },
    "thanks": {
        "am": [
            "ምንም አይደል! በማገልገሌ ደስተኛ ነኝ።",
            "እንኳን አብሮ ረዳን! ሌላ የሚያስፈልግዎት ነገር ካለ ይንገሩኝ።"
        ],
        "en": [
            "You are very welcome! Always glad to be of help.",
            "Anytime! Let me know if there's anything else you need."
        ]
    },
    "jokes": {
        "am": [
            "አንድ ሰዉ ኮምፒውተሩን 'ለምን አትሰራም?' ቢለው፤ ኮምፒውተሩ 'እኔም ፋታ እፈልጋለሁ!' አለ አሉ።",
            "ፕሮግራመር እና ባለቤቱ ሱቅ ሲሄዱ፡ 'ዳቦ አምጣ፣ እንቁላል ካለ አስር አምጣ' አለችው። ፕሮግራመሩ አስር ዳቦ ይዞ መጣ፤ 'እንቁላል ስላለ አስር ዳቦ አመጣሁ' አለ!",
            "አንድ ተማሪ ፈተና ላይ 'የማይክሮሶፍት ዋና ስራ ምንድን ነው?' ሲባል፤ 'ኮምፒውተርን restart ማድረግ!' ብሎ ጻፈ።"
        ],
        "en": [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "There are only 10 types of people in the world: those who understand binary, and those who don't.",
            "Why did the computer keep freezing? Because it left its Windows open!",
            "What do you call a fake noodle? An Impasta!"
        ]
    },
    "sing": {
        "am": [
            "ላ ላ ላ... ድምፄ ለዘፈን ባይሆንም፣ የእርስዎን ትእዛዝ በደስታ እፈፅማለሁ! ሙዚቃ ለማዳመጥ 'ሙዚቃ ክፈት' ወይም 'ዩቲዩብ ክፈት' ማለት ይችላሉ።"
        ],
        "en": [
            "La la la... I might not be a pop star, but I can definitely play any music you want on YouTube or Spotify! Just say 'play music'."
        ]
    },
    "help": {
        "am": [
            f"እኔ {ASSISTANT_NAME_AM} ነኝ። የምችላቸው ትእዛዛት ምሳሌዎች፡ 'ክሮምን ክፈት'፣ 'ካልኩሌተር ክፈት'፣ 'የ 5 ደቂቃ ታይመር ሙላ'፣ 'የአየር ሁኔታ'፣ 'ዜና ንገረኝ'፣ 'ሳንቲም ጣል'፣ 'ዳይስ ጣል'፣ 'ስንት ሰዓት ነው'፣ 'ስለ ኢትዮጵያ ፈልግ'፣ 'ድምፅ ጨምር'፣ 'ስክሪንሾት አንሳ' ወይም 'እንቆቅልሽ ንገረኝ' ማለት ይችላሉ።"
        ],
        "en": [
            f"I am {ASSISTANT_NAME}. You can ask me to: 'Open Chrome', 'Open Calculator', 'Set a timer for 5 minutes', 'What's the weather', 'Latest news', 'Flip a coin', 'Roll a die', 'Tell me a riddle', 'What time is it', 'Search for ...', or 'Increase volume'."
        ]
    },
    "unknown": {
        "am": [
            "ይቅርታ፣ ትእዛዙ አልገባኝም። እባክዎ እንደገና ይሞክሩ ወይም 'እርዳታ' ይበሉ።",
            "ትእዛዝዎ ግልፅ አልሆነልኝም። መተግበሪያ ለመክፈት ለምሳሌ 'ክሮምን ክፈት'፣ ወይም 'ስንት ሰዓት ነው' ማለት ይችላሉ።"
        ],
        "en": [
            "I'm sorry, I didn't quite understand that command. Please try again or say 'help'.",
            "Could you repeat that? You can say things like 'open calculator', 'set a timer', or 'what time is it'."
        ]
    }
}
