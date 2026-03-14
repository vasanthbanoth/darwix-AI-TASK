"""
emotion_detector.py
Detects emotion from text using HuggingFace transformers (distilroberta).
Falls back to TextBlob for intensity scoring.
"""

import os
from typing import Tuple, Dict
from textblob import TextBlob


# Lazy-loaded model to avoid import slowdown
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline
            _pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
                device=-1,  # CPU
            )
            print("[EmotionDetector] HuggingFace model loaded.")
        except Exception as e:
            print(f"[EmotionDetector] HF model unavailable ({e}), using TextBlob fallback.")
            _pipeline = "textblob"
    return _pipeline


def _textblob_fallback(text: str) -> Tuple[str, float, Dict[str, float]]:
    """Simple TextBlob-based sentiment → 3-class emotion."""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    intensity = min(abs(polarity) + subjectivity * 0.3, 1.0)

    if polarity > 0.1:
        emotion = "joy"
        scores = {"joy": polarity, "neutral": 1 - polarity}
    elif polarity < -0.1:
        emotion = "sadness"
        scores = {"sadness": abs(polarity), "neutral": 1 - abs(polarity)}
    else:
        emotion = "neutral"
        scores = {"neutral": 1.0}

    return emotion, round(intensity, 3), scores


def detect_emotion(text: str) -> Dict:
    """
    Returns:
        {
          "emotion": str,           # top emotion label
          "intensity": float,       # 0–1 intensity scale
          "confidence": float,      # model confidence
          "all_scores": dict,       # all emotion probabilities
          "polarity": float,        # TextBlob polarity
          "subjectivity": float,    # TextBlob subjectivity
        }
    """
    pipe = _get_pipeline()

    # TextBlob polarity for intensity scaling
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)
    intensity = min(abs(polarity) * 0.6 + subjectivity * 0.4, 1.0)

    if pipe == "textblob":
        emotion, intensity, all_scores = _textblob_fallback(text)
        confidence = all_scores.get(emotion, 0.5)
    else:
        try:
            results = pipe(text, truncation=True, max_length=512)[0]
            # results is a list of {label, score}
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            top = sorted_results[0]
            emotion = top["label"].lower()
            confidence = round(top["score"], 4)
            all_scores = {r["label"].lower(): round(r["score"], 4) for r in sorted_results}

            # Use HF confidence to refine intensity
            intensity = round(min(confidence * 0.7 + abs(polarity) * 0.3, 1.0), 3)
        except Exception as e:
            print(f"[EmotionDetector] Inference error: {e}. Falling back to TextBlob.")
            emotion, intensity, all_scores = _textblob_fallback(text)
            confidence = all_scores.get(emotion, 0.5)

    return {
        "emotion": emotion,
        "intensity": round(intensity, 3),
        "confidence": round(confidence if isinstance(confidence, float) else 0.5, 4),
        "all_scores": all_scores,
        "polarity": polarity,
        "subjectivity": subjectivity,
    }
