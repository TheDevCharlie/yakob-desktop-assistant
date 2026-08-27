"""
Expanded 24/7 World Live Broadcast Radio Station Catalog for Yakob Assistant.
Features 20+ verified, high-uptime direct Icecast / Shoutcast live streams
organized by genre with zero YouTube dependency.
"""
from typing import Dict, Optional, List

RADIO_STATIONS = {
    # -------------------------------------------------------------
    # 1. NEWS & WORLD TALK
    # -------------------------------------------------------------
    "bbc world service": {
        "name": "BBC World Service (UK)",
        "name_am": "ቢቢሲ ወርልድ ሰርቪስ",
        "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "fallback_url": "https://npr-ice.streamguys1.com/live.mp3",
        "genre": "Global News & Current Affairs",
        "category": "News",
        "country": "United Kingdom"
    },
    "npr news": {
        "name": "NPR 24/7 News (USA)",
        "name_am": "ኤን ፒ አር ዜና",
        "url": "https://npr-ice.streamguys1.com/live.mp3",
        "fallback_url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "genre": "National & Breaking News",
        "category": "News",
        "country": "USA"
    },

    # -------------------------------------------------------------
    # 2. LOFI, CHILLOUT & INSTRUMENTAL
    # -------------------------------------------------------------
    "lofi radio": {
        "name": "Groove Salad Lofi & Chillout 24/7",
        "name_am": "ሎፋይ ሂፕ ሆፕ ሬዲዮ",
        "url": "http://ice1.somafm.com/groovesalad-128-mp3",
        "fallback_url": "http://ice1.somafm.com/fluid-128-mp3",
        "genre": "Lofi, Downtempo & Ambient Chill",
        "category": "Lofi & Chill",
        "country": "Global"
    },
    "fluid hiphop": {
        "name": "Fluid Instrumental Hip-Hop",
        "name_am": "ፍሉይድ ኢንስትሩመንታል ሂፕ ሆፕ",
        "url": "http://ice1.somafm.com/fluid-128-mp3",
        "fallback_url": "http://ice1.somafm.com/groovesalad-128-mp3",
        "genre": "Downtempo & Headphone Beats",
        "category": "Lofi & Chill",
        "country": "Global"
    },
    "lush vocal": {
        "name": "Lush Sensual Vocal Chill",
        "name_am": "ለሽ ቮካል ቺል",
        "url": "http://ice1.somafm.com/lush-128-mp3",
        "fallback_url": "http://ice1.somafm.com/groovesalad-128-mp3",
        "genre": "Sensual Female Vocals & Chill",
        "category": "Lofi & Chill",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 3. JAZZ & LOUNGE
    # -------------------------------------------------------------
    "jazz lounge": {
        "name": "Secret Agent Spy Jazz & Lounge",
        "name_am": "ክላሲክ ጃዝ ሬዲዮ",
        "url": "http://ice1.somafm.com/secretagent-128-mp3",
        "fallback_url": "http://ice1.somafm.com/sonicuniverse-128-mp3",
        "genre": "Spy Themes, Cool Jazz & Lounge",
        "category": "Jazz",
        "country": "Global"
    },
    "sonic universe": {
        "name": "Sonic Universe Nu-Jazz & Avant",
        "name_am": "ሶኒክ ዩኒቨርስ ጃዝ",
        "url": "http://ice1.somafm.com/sonicuniverse-128-mp3",
        "fallback_url": "http://ice1.somafm.com/secretagent-128-mp3",
        "genre": "Nu-Jazz, Eclectic & Avant-Garde",
        "category": "Jazz",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 4. AMBIENT & SPACE RELAXATION
    # -------------------------------------------------------------
    "drone zone": {
        "name": "Drone Zone Space Ambient",
        "name_am": "ድሮን ዞን ስፔስ አምቢያንት",
        "url": "http://ice1.somafm.com/dronezone-128-mp3",
        "fallback_url": "http://ice1.somafm.com/deepspaceone-128-mp3",
        "genre": "Atmospheric Space & Deep Ambient",
        "category": "Ambient",
        "country": "Global"
    },
    "deep space one": {
        "name": "Deep Space One Cosmic Ambient",
        "name_am": "ዲፕ ስፔስ ዋን አምቢያንት",
        "url": "http://ice1.somafm.com/deepspaceone-128-mp3",
        "fallback_url": "http://ice1.somafm.com/dronezone-128-mp3",
        "genre": "Deep Ambient Electronic Space",
        "category": "Ambient",
        "country": "Global"
    },
    "space station": {
        "name": "Space Station Soma Ambient Beats",
        "name_am": "ስፔስ ስቴሽን ሶማ",
        "url": "http://ice1.somafm.com/spacestation-128-mp3",
        "fallback_url": "http://ice1.somafm.com/dronezone-128-mp3",
        "genre": "Spaced-out Ambient Mid-Tempo",
        "category": "Ambient",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 5. RETRO, 80S, POP & DANCE
    # -------------------------------------------------------------
    "dance wave": {
        "name": "Dance Wave Retro Pop 24/7",
        "name_am": "ዳንስ ዌቭ ፖፕ ሬዲዮ",
        "url": "https://dancewave.online/dance.mp3",
        "fallback_url": "http://ice1.somafm.com/u80s-128-mp3",
        "genre": "80s, 90s, Pop & Dance Hits",
        "category": "Pop & Retro",
        "country": "Global"
    },
    "underground 80s": {
        "name": "Underground 80s Synthpop & Wave",
        "name_am": "አንደርግራውንድ ሰማንያዎች",
        "url": "http://ice1.somafm.com/u80s-128-mp3",
        "fallback_url": "https://dancewave.online/dance.mp3",
        "genre": "80s Synthpop, Post-Punk & Wave",
        "category": "Pop & Retro",
        "country": "Global"
    },
    "poptron": {
        "name": "PopTron Electropop & Indie Dance",
        "name_am": "ፖፕትሮን ኤሌክትሮፖፕ",
        "url": "http://ice1.somafm.com/poptron-128-mp3",
        "fallback_url": "https://dancewave.online/dance.mp3",
        "genre": "Modern Electropop & Indie Dance",
        "category": "Pop & Retro",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 6. ELECTRONIC, CYBERPUNK & CLUB
    # -------------------------------------------------------------
    "def con radio": {
        "name": "DEF CON Cyberpunk & Hacker Beats",
        "name_am": "ዴፍ ኮን ሳይበርፐንክ",
        "url": "http://ice1.somafm.com/defcon-128-mp3",
        "fallback_url": "http://ice1.somafm.com/beatblender-128-mp3",
        "genre": "Cyberpunk, Darkwave & Hacker Beats",
        "category": "Electronic",
        "country": "Global"
    },
    "beat blender": {
        "name": "Beat Blender Deep House & Techno",
        "name_am": "ቢት ብሌንደር ሃውስ",
        "url": "http://ice1.somafm.com/beatblender-128-mp3",
        "fallback_url": "http://ice1.somafm.com/defcon-128-mp3",
        "genre": "Deep House, Chill Techno & Club",
        "category": "Electronic",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 7. ROCK, INDIE & AMERICANA
    # -------------------------------------------------------------
    "indie pop": {
        "name": "Indie Pop Rocks 24/7",
        "name_am": "ኢንዲ ፖፕ ሮክስ",
        "url": "http://ice1.somafm.com/indiepop-128-mp3",
        "fallback_url": "http://ice1.somafm.com/covers-128-mp3",
        "genre": "New & Classic Indie Rock Tracks",
        "category": "Rock & Indie",
        "country": "Global"
    },
    "classic rock": {
        "name": "Covers & Classic Rock Planet",
        "name_am": "ክላሲክ ሮክ ፕላኔት",
        "url": "http://ice1.somafm.com/covers-128-mp3",
        "fallback_url": "http://ice1.somafm.com/indiepop-128-mp3",
        "genre": "Classic Rock, Covers & Anthems",
        "category": "Rock & Indie",
        "country": "Global"
    },
    "boot liquor": {
        "name": "Boot Liquor Americana & Country",
        "name_am": "ቡት ሊከር አሜሪካና",
        "url": "http://ice1.somafm.com/bootliquor-128-mp3",
        "fallback_url": "http://ice1.somafm.com/indiepop-128-mp3",
        "genre": "Americana, Roots Country & Bluegrass",
        "category": "Rock & Indie",
        "country": "Global"
    },

    # -------------------------------------------------------------
    # 8. ETHIOPIAN & EAST AFRICAN BROADCASTS
    # -------------------------------------------------------------
    "sheger fm": {
        "name": "Sheger FM 102.1 (Ethiopia)",
        "name_am": "ሸገር ኤፍ ኤም 102.1",
        "url": "https://stream.zeno.fm/k2ydf2b15m0uv",
        "fallback_url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "genre": "Talk, News & Ethiopian Music",
        "category": "Ethiopian",
        "country": "Ethiopia"
    },
    "fana fm": {
        "name": "Fana FM 98.1 (Ethiopia)",
        "name_am": "ፋና ኤፍ ኤም 98.1",
        "url": "https://stream.zeno.fm/f9v27bvq2m0uv",
        "fallback_url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "genre": "National News & Music",
        "category": "Ethiopian",
        "country": "Ethiopia"
    }
}


def find_radio_station(query: str) -> Optional[Dict[str, str]]:
    """Finds best matching radio station from query."""
    q = query.lower().strip()
    
    # 1. Exact or keyword aliases
    if any(k in q for k in ["sheger", "ሸገር"]):
        return RADIO_STATIONS["sheger fm"]
    if any(k in q for k in ["fana", "ፋና"]):
        return RADIO_STATIONS["fana fm"]
    if any(k in q for k in ["lofi", "ሎፋይ", "study beats", "chill beats", "groove"]):
        return RADIO_STATIONS["lofi radio"]
    if any(k in q for k in ["fluid", "hiphop", "hip hop", "beats"]):
        return RADIO_STATIONS["fluid hiphop"]
    if any(k in q for k in ["lush", "vocal chill", "female vocal"]):
        return RADIO_STATIONS["lush vocal"]
    if any(k in q for k in ["bbc", "ቢቢሲ", "world service"]):
        return RADIO_STATIONS["bbc world service"]
    if any(k in q for k in ["npr", "news radio", "news"]):
        return RADIO_STATIONS["npr news"]
    if any(k in q for k in ["jazz", "ጃዝ", "saxophone", "lounge", "secret agent"]):
        return RADIO_STATIONS["jazz lounge"]
    if any(k in q for k in ["sonic", "nu jazz", "avant"]):
        return RADIO_STATIONS["sonic universe"]
    if any(k in q for k in ["drone", "space ambient", "meditation"]):
        return RADIO_STATIONS["drone zone"]
    if any(k in q for k in ["deep space", "cosmic"]):
        return RADIO_STATIONS["deep space one"]
    if any(k in q for k in ["space station"]):
        return RADIO_STATIONS["space station"]
    if any(k in q for k in ["dance", "retro pop", "dance wave", "80s dance"]):
        return RADIO_STATIONS["dance wave"]
    if any(k in q for k in ["80s", "synthpop", "new wave", "underground"]):
        return RADIO_STATIONS["underground 80s"]
    if any(k in q for k in ["poptron", "electropop"]):
        return RADIO_STATIONS["poptron"]
    if any(k in q for k in ["def con", "defcon", "cyberpunk", "hacker"]):
        return RADIO_STATIONS["def con radio"]
    if any(k in q for k in ["house", "techno", "club", "blender"]):
        return RADIO_STATIONS["beat blender"]
    if any(k in q for k in ["indie", "indie rock", "indie pop"]):
        return RADIO_STATIONS["indie pop"]
    if any(k in q for k in ["classic rock", "rock", "covers"]):
        return RADIO_STATIONS["classic rock"]
    if any(k in q for k in ["country", "americana", "bluegrass", "boot liquor"]):
        return RADIO_STATIONS["boot liquor"]

    for key, station in RADIO_STATIONS.items():
        if key in q or station["name"].lower() in q or station["name_am"] in q:
            return station

    # Default to Groove Salad Lofi or BBC
    return RADIO_STATIONS["lofi radio"]
