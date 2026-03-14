"""
main.py — Pitch Visualizer FastAPI Application
Uses Server-Sent Events (SSE) for panel-by-panel streaming.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel

from segmenter import segment_into_scenes
from prompt_engineer import enhance_prompt, get_available_styles
from image_generator import generate_image

load_dotenv()

app = FastAPI(title="Pitch Visualizer", version="1.0.0")

import tempfile

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/pitch-visualizer/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

tmp_outputs = Path(tempfile.gettempdir()) / "outputs"
tmp_outputs.mkdir(exist_ok=True)
app.mount("/pitch-visualizer/outputs", StaticFiles(directory=str(tmp_outputs)), name="outputs")


class GenerateRequest(BaseModel):
    text: str
    style: str = "cinematic"


@app.get("/", response_class=HTMLResponse)
@app.get("/pitch-visualizer/", response_class=HTMLResponse)
@app.get("/pitch-visualizer", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "styles": get_available_styles(),
    })


@app.get("/styles")
async def list_styles():
    return {"styles": get_available_styles()}


@app.post("/pitch-visualizer/generate")
async def generate_storyboard(request: Request, body: GenerateRequest):
    """SSE endpoint — streams panels one by one as they complete."""
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty.")
    if len(body.text) > 3000:
        raise HTTPException(400, "Text too long (max 3000 chars).")

    style = body.style if body.style in get_available_styles() else "cinematic"

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'total': 0})}\n\n"

            # Segment text into scenes
            scenes = segment_into_scenes(body.text)
            total = len(scenes)
            yield f"data: {json.dumps({'type': 'total', 'total': total})}\n\n"

            # Process each scene
            for idx, scene in enumerate(scenes):
                # Yield "processing" event
                yield f"data: {json.dumps({'type': 'processing', 'index': idx, 'scene': scene})}\n\n"

                # Run blocking I/O in thread pool
                loop = asyncio.get_event_loop()

                # Generate enhanced prompt
                gemini_key = os.getenv("GEMINI_API_KEY", "")
                prompt = await loop.run_in_executor(
                    None, enhance_prompt, scene, style, gemini_key
                )

                # Generate image
                try:
                    img_path = await loop.run_in_executor(
                        None, generate_image, prompt, idx
                    )
                    image_url = f"/pitch-visualizer/outputs/{img_path.name}"
                    error = None
                except Exception as e:
                    image_url = None
                    error = str(e)
                    print(f"[Main] Image gen failed for scene {idx}: {e}")

                # Yield completed panel
                panel = {
                    "type": "panel",
                    "index": idx,
                    "total": total,
                    "scene": scene,
                    "prompt": prompt,
                    "image_url": image_url,
                    "error": error,
                }
                yield f"data: {json.dumps(panel)}\n\n"

            # Done
            yield f"data: {json.dumps({'type': 'done', 'total': total})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Pitch Visualizer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
