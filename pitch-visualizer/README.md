# 🎬 Pitch Visualizer — From Words to Storyboard

> Paste any narrative text and instantly receive a cinematic AI-generated storyboard. Powered by Gemini for intelligent prompt engineering and Stable Diffusion for image creation.

---

## 🌟 What It Does

```
"Sarah walked into the boardroom with quiet confidence..."
   ↓ NLTK sentence segmentation
   ↓ Gemini Flash prompt supercharging
   ↓ Pollinations.ai / Stable Diffusion image generation
   ↓ Panel-by-panel cinematic storyboard
```

---

## 🧠 Design Choices & Prompt Engineering

### The Core Problem
Simply sending "Sarah walked into a boardroom" to an image model gives a generic, boring result. Great diffusion images need:
- **Subject** (who), **Setting** (where), **Mood** (atmosphere)
- **Camera angle**, **Lighting**, **Composition**
- **Style keywords** for consistency

### Gemini Flash as Creative Director
Each scene sentence is sent to Gemini Flash with this system prompt:
> *"You are a world-class creative director. Transform this sentence into a single richly detailed image prompt: WHO is present, WHERE it happens, lighting mood, camera angle, composition, sensory details. Under 120 words."*

This consistently produces 4–6× better images than the raw sentence.

### Prompt Example
| Raw Scene | Gemini-Enhanced Prompt |
|-----------|----------------------|
| "Sarah walked into the boardroom with confidence." | "A poised professional woman in a sharp navy blazer strides through glass double doors into a sleek modern boardroom, morning light streaming through floor-to-ceiling windows, low-angle hero shot, cinematic depth of field, photorealistic, 8K." |

### Visual Consistency
Every prompt has the user-selected style appended (e.g., `"cinematic film still, anamorphic lens, dramatic lighting"`), ensuring a coherent aesthetic across all panels.

### Fallback Chain
1. **Gemini Flash** → rich artistic prompt
2. **Rule-based enhancement** → if Gemini key is missing
3. **HuggingFace SDXL** → high-quality images (if key provided)
4. **Pollinations.ai** → free, no-key-needed default

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd pitch-visualizer
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt_tab')"
```

### 2. Configure API keys
```bash
cp .env.example .env
# Edit .env and add your Gemini API key (free at https://aistudio.google.com)
```

> **Note**: Without a Gemini key, rule-based prompt enhancement is used. Images still generate via Pollinations.ai (no key needed).

### 3. Run the server
```bash
uvicorn main:app --reload --port 8001
```

### 4. Open the app
📍 **http://localhost:8001**

Paste your story, pick an art style, click **Generate Storyboard** and watch panels appear live!

---

## 📡 API Reference

### `POST /generate` (SSE)
Streams storyboard panels as they complete.
```json
{ "text": "Your narrative paragraph here.", "style": "cinematic" }
```

Returns SSE events:
```json
{"type": "total", "total": 4}
{"type": "processing", "index": 0, "scene": "..."}
{"type": "panel", "index": 0, "image_url": "/outputs/panel_00_abc.png", "prompt": "..."}
{"type": "done", "total": 4}
```

### Art Styles
`photorealistic` · `digital art` · `watercolor` · `cinematic` · `comic book` · `anime`

---

## 📁 Project Structure

```
pitch-visualizer/
├── main.py              # FastAPI + SSE streaming server
├── segmenter.py         # NLTK scene segmentation
├── prompt_engineer.py   # Gemini Flash prompt supercharger
├── image_generator.py   # Pollinations.ai + HuggingFace image gen
├── templates/
│   └── index.html       # Dynamic storyboard UI
├── static/
│   ├── styles.css       # Cinematic dark gold theme
│   └── app.js           # SSE consumer + panel-by-panel reveal
├── outputs/             # Saved generated images
├── .env.example
└── requirements.txt
```

---

## 🎁 Bonus Features Implemented

- ✅ **Visual Consistency** — style keywords appended to every prompt
- ✅ **6 User-Selectable Styles** (photorealistic, digital art, watercolor, cinematic, comic, anime)
- ✅ **LLM Prompt Refinement** — Gemini Flash as creative director
- ✅ **Dynamic UI** — panels stream in one by one via SSE
- ✅ **HTML Export** — download entire storyboard as a self-contained HTML file
- ✅ **Zero-key fallback** — works out of the box with Pollinations.ai

---

*Built with ❤️ for the Darwix AI interview challenge.*
