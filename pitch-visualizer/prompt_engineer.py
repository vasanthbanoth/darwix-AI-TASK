"""
prompt_engineer.py
Uses Google Gemini Flash to supercharge plain text sentences into
rich, visually detailed image generation prompts.
Falls back to rule-based enhancement if Gemini is unavailable.
"""

import os
import re
from typing import Optional


STYLE_SUFFIXES = {
    "photorealistic": "photorealistic, 8K ultra-HD, DSLR photography, sharp focus, cinematic lighting",
    "digital art": "digital art, detailed illustration, vibrant colors, concept art, trending on ArtStation",
    "watercolor": "delicate watercolor painting, soft washes of color, loose brushwork, whimsical, artistic",
    "cinematic": "cinematic film still, anamorphic lens, dramatic lighting, shallow depth of field, blockbuster movie",
    "comic book": "comic book art, bold outlines, dynamic composition, vivid colors, graphic novel style",
    "anime": "anime art style, detailed cel shading, Studio Ghibli inspired, expressive characters, beautiful scenery",
}

DEFAULT_STYLE = "cinematic"

SYSTEM_PROMPT = """You are a world-class creative director and AI art prompt engineer.
Your task: transform a plain narrative sentence into a single, richly detailed visual prompt
for an AI image generator (like Stable Diffusion or DALL-E).

Rules:
1. Focus on the core visual scene: WHO, WHERE, WHAT is happening.
2. Add atmospheric details: lighting mood, camera angle, composition.
3. Include sensory details: textures, colors, time of day, weather.
4. Do NOT describe text, captions, or logos.
5. Keep it to 1-2 sentences, under 120 words.
6. Return ONLY the refined prompt, nothing else.
"""


def _gemini_enhance(sentence: str, style: str, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        style_suffix = STYLE_SUFFIXES.get(style, STYLE_SUFFIXES[DEFAULT_STYLE])

        user_msg = f"""Scene sentence: "{sentence}"
Target art style: {style} — append these style keywords at the end: {style_suffix}
Generate the enhanced visual prompt:"""

        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + user_msg]}
            ]
        )
        text = response.text.strip()
        # Remove any markdown code fences if Gemini wraps it
        text = re.sub(r'^```.*\n?', '', text, flags=re.MULTILINE).strip('`').strip()
        return text
    except Exception as e:
        print(f"[PromptEngineer] Gemini error: {e}")
        return None


def _rule_based_enhance(sentence: str, style: str) -> str:
    """Deterministic fallback: add visual, atmospheric, and style cues."""
    style_suffix = STYLE_SUFFIXES.get(style, STYLE_SUFFIXES[DEFAULT_STYLE])
    enhanced = (
        f"A vivid scene depicting: {sentence.rstrip('.')} — "
        f"dramatic composition, professional lighting, highly detailed. "
        f"{style_suffix}."
    )
    return enhanced


def enhance_prompt(sentence: str, style: str = DEFAULT_STYLE, api_key: Optional[str] = None) -> str:
    """
    Returns a supercharged image prompt for the given scene sentence.
    Tries Gemini first, falls back to rule-based enhancement.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    if api_key:
        result = _gemini_enhance(sentence, style, api_key)
        if result:
            return result

    return _rule_based_enhance(sentence, style)


def get_available_styles() -> list:
    return list(STYLE_SUFFIXES.keys())
