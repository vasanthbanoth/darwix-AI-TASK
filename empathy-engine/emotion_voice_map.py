"""
emotion_voice_map.py
Maps detected emotions to vocal parameter configurations compatible with edge-tts.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class VoiceConfig:
    """Vocal parameters for edge-tts modulation."""
    rate: str          # e.g. "+10%"
    pitch: str         # e.g. "+5Hz"
    volume: str        # e.g. "+10%"
    description: str   # human-readable label
    color: str         # UI badge color hex

# Base percentages/Hz at intensity = 1.0 (neutral is 0)
EMOTION_BASE: Dict[str, dict] = {
    "joy": {
        "rate_pct": 15,       # +15%
        "pitch_hz": 10,       # +10Hz
        "volume_pct": 10,     # +10%
        "description": "Joyful 😊",
        "color": "#F5A623",
    },
    "sadness": {
        "rate_pct": -20,      # -20%
        "pitch_hz": -10,      # -10Hz
        "volume_pct": -15,    # -15%
        "description": "Sad 😢",
        "color": "#4A90D9",
    },
    "anger": {
        "rate_pct": 25,
        "pitch_hz": 5,        # A bit higher
        "volume_pct": 20,
        "description": "Angry 😠",
        "color": "#D0021B",
    },
    "fear": {
        "rate_pct": 20,
        "pitch_hz": 15,
        "volume_pct": -5,
        "description": "Fearful 😨",
        "color": "#7B68EE",
    },
    "disgust": {
        "rate_pct": -10,
        "pitch_hz": -5,
        "volume_pct": 5,
        "description": "Disgusted 🤢",
        "color": "#6B8E23",
    },
    "surprise": {
        "rate_pct": 15,
        "pitch_hz": 20,
        "volume_pct": 10,
        "description": "Surprised 😲",
        "color": "#FF6F91",
    },
    "neutral": {
        "rate_pct": 0,
        "pitch_hz": 0,
        "volume_pct": 0,
        "description": "Neutral 😐",
        "color": "#9B9B9B",
    },
}

def get_voice_config(emotion: str, intensity: float = 1.0) -> VoiceConfig:
    """
    Returns a VoiceConfig with edge-tts compatible strings, scaled by intensity (0-1).
    """
    emotion = emotion.lower()
    base = EMOTION_BASE.get(emotion, EMOTION_BASE["neutral"])

    # Scale from 0.0 (neutral) to 1.0 (full)
    scale = max(0.0, min(1.0, intensity))

    rate_val = int(base["rate_pct"] * scale)
    pitch_val = int(base["pitch_hz"] * scale)
    volume_val = int(base["volume_pct"] * scale)

    # Format explicitly with +/- signs
    rate_str = f"+{rate_val}%" if rate_val >= 0 else f"{rate_val}%"
    pitch_str = f"+{pitch_val}Hz" if pitch_val >= 0 else f"{pitch_val}Hz"
    volume_str = f"+{volume_val}%" if volume_val >= 0 else f"{volume_val}%"

    return VoiceConfig(
        rate=rate_str,
        pitch=pitch_str,
        volume=volume_str,
        description=base["description"],
        color=base["color"],
    )
