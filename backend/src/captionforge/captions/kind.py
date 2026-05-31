from __future__ import annotations

import re

from .model import TAGS, NL

_SENTENCE_END = re.compile(r"[.!?]")


def classify_label(label: str) -> str | None:
    """Known labels -> kind. Unknown -> None (caller infers/defaults)."""
    low = label.lower()
    if "wd14" in low or "tag" in low:
        return TAGS
    if "qwen" in low or "joycaption" in low or "caption" in low:
        return NL
    return None


def infer_kind(body: str) -> str:
    """Content heuristic, used when a label is absent or unrecognized.

    Tags look like many short, comma-separated fragments with little
    sentence punctuation. Everything else is natural language.
    """
    text = body.strip()
    if not text:
        return NL
    tokens = [t.strip() for t in text.split(",") if t.strip()]
    if len(tokens) < 2:
        return NL
    avg_words = sum(len(t.split()) for t in tokens) / len(tokens)
    sentence_ends = len(_SENTENCE_END.findall(text))
    if avg_words <= 3 and sentence_ends <= 1:
        return TAGS
    return NL
