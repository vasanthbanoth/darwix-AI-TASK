"""
main.py — Empathy Engine FastAPI Application
"""

import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel
from .emotion_detector import detect_emotion
from .emotion_voice_map import get_voice_config
from .tts_engine import synthesize

import tempfile

app = FastAPI(title="Empathy Engine", version="1.0.0")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/empathy-engine/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

tmp_outputs = Path(tempfile.gettempdir()) / "outputs"
tmp_outputs.mkdir(exist_ok=True)
app.mount("/empathy-engine/outputs", StaticFiles(directory=str(tmp_outputs)), name="outputs")


class TextInput(BaseModel):
    text: str


class SynthesizeInput(BaseModel):
    text: str
    emotion: str | None = None
    intensity: float | None = None


@app.get("/", response_class=HTMLResponse)
@app.get("/empathy-engine/", response_class=HTMLResponse)
@app.get("/empathy-engine", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/empathy-engine/analyze")
async def analyze(body: TextInput):
    """Analyze text and return emotion + voice config."""
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty.")

    result = detect_emotion(body.text)
    voice = get_voice_config(result["emotion"], result["intensity"])

    return {
        "emotion": result["emotion"],
        "intensity": result["intensity"],
        "confidence": result["confidence"],
        "all_scores": result["all_scores"],
        "polarity": result["polarity"],
        "subjectivity": result["subjectivity"],
        "voice_config": {
            "rate": voice.rate,
            "pitch": voice.pitch,
            "volume": voice.volume,
            "description": voice.description,
            "color": voice.color,
        },
    }


@app.post("/empathy-engine/synthesize")
async def synthesize_endpoint(body: SynthesizeInput):
    """Synthesize speech with emotion-driven vocal modulation."""
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty.")

    # Detect or use provided emotion
    if body.emotion and body.intensity is not None:
        emotion = body.emotion
        intensity = body.intensity
        analysis = detect_emotion(body.text)
        analysis["emotion"] = emotion
        analysis["intensity"] = intensity
    else:
        analysis = detect_emotion(body.text)
        emotion = analysis["emotion"]
        intensity = analysis["intensity"]

    voice = get_voice_config(emotion, intensity)

    try:
        audio_path = synthesize(body.text, voice)
    except Exception as e:
        raise HTTPException(500, f"TTS synthesis failed: {str(e)}")

    filename = audio_path.name
    return {
        "audio_url": f"/empathy-engine/outputs/{filename}",
        "emotion": emotion,
        "intensity": intensity,
        "voice_config": {
            "rate": voice.rate,
            "pitch": voice.pitch,
            "volume": voice.volume,
            "description": voice.description,
            "color": voice.color,
        },
        "analysis": {
            "polarity": analysis["polarity"],
            "subjectivity": analysis["subjectivity"],
            "confidence": analysis["confidence"],
            "all_scores": analysis.get("all_scores", {}),
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Empathy Engine"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
