"""
tts_engine.py
Text-to-Speech using edge-tts.
"""

import os
import uuid
import asyncio
from pathlib import Path
from emotion_voice_map import VoiceConfig

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

VOICE = "en-US-AriaNeural"

async def _synthesize_async(text: str, config: VoiceConfig, out_path: Path) -> bool:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text,
            VOICE,
            rate=config.rate,
            pitch=config.pitch,
            volume=config.volume
        )
        await communicate.save(str(out_path))
        return True
    except Exception as e:
        print(f"[TTS] edge-tts error: {e}")
        return False

def synthesize(text: str, config: VoiceConfig) -> Path:
    """
    Synthesize speech using edge-tts. Returns .mp3 file path.
    """
    filename = f"{uuid.uuid4().hex}.mp3"
    out_path = OUTPUT_DIR / filename
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    success = loop.run_until_complete(_synthesize_async(text, config, out_path))

    if not success or not out_path.exists():
        raise RuntimeError("TTS synthesis failed using edge-tts.")

    return out_path
