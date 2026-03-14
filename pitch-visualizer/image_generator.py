"""
image_generator.py
Generates images using Pollinations.ai (free, no API key) with
optional HuggingFace Inference API upgrade.
"""

import os
import uuid
import time
import requests
from pathlib import Path
from urllib.parse import quote


OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=768&height=512&seed={seed}&nologo=true&model=flux"


def _pollinations_generate(prompt: str, seed: int) -> bytes:
    """Use Pollinations.ai — completely free, no API key needed."""
    encoded = quote(prompt[:500])  # URL-safe prompt
    url = POLLINATIONS_URL.format(prompt=encoded, seed=seed)
    res = requests.get(url, timeout=90)
    res.raise_for_status()
    return res.content


def _huggingface_generate(prompt: str, api_key: str) -> bytes:
    """Use HuggingFace Inference API with Stable Diffusion XL."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"width": 768, "height": 512, "num_inference_steps": 30},
    }
    for attempt in range(3):
        res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)
        if res.status_code == 503:
            wait = res.json().get("estimated_time", 30)
            print(f"[ImageGen] Model loading, waiting {wait:.0f}s…")
            time.sleep(min(wait, 45))
            continue
        res.raise_for_status()
        return res.content
    raise RuntimeError("HuggingFace model failed after 3 attempts.")


def generate_image(prompt: str, panel_index: int = 0) -> Path:
    """
    Generate an image for the given prompt.
    Returns the path to the saved PNG file.
    """
    hf_key = os.getenv("HUGGINGFACE_API_KEY", "")
    seed = 42 + panel_index * 7  # deterministic but varied per panel

    try:
        if hf_key:
            print(f"[ImageGen] Using HuggingFace for panel {panel_index}")
            img_bytes = _huggingface_generate(prompt, hf_key)
        else:
            print(f"[ImageGen] Using Pollinations for panel {panel_index}")
            img_bytes = _pollinations_generate(prompt, seed)
    except Exception as e:
        print(f"[ImageGen] Primary failed ({e}), trying Pollinations fallback")
        img_bytes = _pollinations_generate(prompt, seed)

    filename = f"panel_{panel_index:02d}_{uuid.uuid4().hex[:8]}.png"
    out_path = OUTPUT_DIR / filename
    out_path.write_bytes(img_bytes)
    print(f"[ImageGen] Saved: {out_path}")
    return out_path
