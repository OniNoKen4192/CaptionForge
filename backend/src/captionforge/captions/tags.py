from __future__ import annotations


def tokenize_tags(body: str) -> list[str]:
    return [t.strip() for t in body.split(",") if t.strip()]


def join_tags(tags: list[str]) -> str:
    return ", ".join(tags)
