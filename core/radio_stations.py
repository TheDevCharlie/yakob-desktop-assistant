"""
Live World & Ethiopian Radio Stations Engine for Yakob Assistant.
Provides high-fidelity 24/7 live audio stream URLs for online radio stations.
"""
from typing import Dict, Optional, List

RADIO_STATIONS = {
    "sheger fm": {
        "name": "Sheger FM 102.1 (Ethiopia)",
        "name_am": "ሸገር ኤፍ ኤም 102.1",
        "url": "https://stream.zeno.fm/k2ydf2b15m0uv",
        "genre": "Talk, News & Music",
        "country": "Ethiopia"
    },
    "fana fm": {
        "name": "Fana FM 98.1 (Ethiopia)",
        "name_am": "ፋና ኤፍ ኤም 98.1",
        "url": "https://stream.zeno.fm/f9v27bvq2m0uv",
        "genre": "News & Ethiopian Music",
        "country": "Ethiopia"
    },
    "lofi radio": {
        "name": "Lofi Hip Hop 24/7 Beats",
        "name_am": "ሎፋይ ሂፕ ሆፕ ሬዲዮ",
        "url": "https://stream.zeno.fm/f3wvbbqmdg8uv",
        "genre": "Chill, Beats & Study",
        "country": "Global"
    },
    "bbc world service": {
        "name": "BBC World Service (UK)",
        "name_am": "ቢቢሲ ወርልድ ሰርቪስ",
        "url": "https://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "genre": "Global News & Features",
        "country": "United Kingdom"
    },
    "npr news": {
        "name": "NPR 24/7 News (USA)",
        "name_am": "ኤን ፒ አር ዜና",
        "url": "https://npr-ice.streamguys1.com/live.mp3",
        "genre": "News & Documentaries",
        "country": "USA"
    },
    "jazz lounge": {
        "name": "Classic Jazz & Lounge 24/7",
        "name_am": "ክላሲክ ጃዝ ሬዲዮ",
        "url": "https://stream.zeno.fm/yndptw2wdg8uv",
        "genre": "Smooth Jazz & Saxophone",
        "country": "Global"
    },
    "classical radio": {
        "name": "Classical Masterpieces 24/7",
        "name_am": "ክላሲካል ሙዚቃ ሬዲዮ",
        "url": "https://stream.zeno.fm/d40d9h4wdg8uv",
        "genre": "Classical & Symphony",
        "country": "Global"
    }
}


def find_radio_station(query: str) -> Optional[Dict[str, str]]:
    """Finds best matching radio station from query."""
    q = query.lower().strip()
    # Direct alias matches
    if any(k in q for k in ["sheger", "ሸገር"]):
        return RADIO_STATIONS["sheger fm"]
    if any(k in q for k in ["fana", "ፋና"]):
        return RADIO_STATIONS["fana fm"]
    if any(k in q for k in ["lofi", "ሎፋይ", "study beats", "chill beats"]):
        return RADIO_STATIONS["lofi radio"]
    if any(k in q for k in ["bbc", "ቢቢሲ"]):
        return RADIO_STATIONS["bbc world service"]
    if any(k in q for k in ["npr", "news radio"]):
        return RADIO_STATIONS["npr news"]
    if any(k in q for k in ["jazz", "ጃዝ"]):
        return RADIO_STATIONS["jazz lounge"]
    if any(k in q for k in ["classical", "ክላሲካል", "piano", "mozart", "beethoven"]):
        return RADIO_STATIONS["classical radio"]

    for key, station in RADIO_STATIONS.items():
        if key in q or station["name"].lower() in q or station["name_am"] in q:
            return station

    # Default to Sheger FM or Lofi
    return RADIO_STATIONS["sheger fm"]
