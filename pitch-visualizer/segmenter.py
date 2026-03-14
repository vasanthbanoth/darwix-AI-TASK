"""
segmenter.py
Breaks narrative text into logically grouped scenes using NLTK.
Falls back to simple sentence split if NLTK unavailable.
"""

import re
from typing import List


def _nltk_tokenize(text: str) -> List[str]:
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    return nltk.sent_tokenize(text)


def _simple_split(text: str) -> List[str]:
    """Fallback: split on sentence-ending punctuation."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def segment_into_scenes(text: str, min_scenes: int = 3, max_scenes: int = 6) -> List[str]:
    """
    Tokenize text into sentences, then group short consecutive sentences
    to ensure between min_scenes and max_scenes panels.
    Returns a list of scene strings.
    """
    try:
        sentences = _nltk_tokenize(text)
    except Exception:
        sentences = _simple_split(text)

    # Clean up
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return [text]

    # If fewer than min_scenes sentences, return as-is
    if len(sentences) <= min_scenes:
        return sentences

    # If more than max_scenes, group consecutive sentences
    if len(sentences) > max_scenes:
        per_group = len(sentences) / max_scenes
        groups = []
        buf = []
        for i, sent in enumerate(sentences):
            buf.append(sent)
            if len(buf) >= per_group and len(groups) < max_scenes - 1:
                groups.append(" ".join(buf))
                buf = []
        if buf:
            groups.append(" ".join(buf))
        return groups

    return sentences
