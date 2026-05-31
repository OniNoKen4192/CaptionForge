from __future__ import annotations

from .model import CaptionDoc, TAGS
from .tags import join_tags


def serialize(doc: CaptionDoc) -> str:
    blocks: list[str] = []
    for s in doc.sections:
        lines: list[str] = []
        if s.label is not None:
            lines.append(f"=== {s.label} ===")
        if s.kind == TAGS:
            lines.append(join_tags(s.tags))
        else:
            lines.append(s.text.strip())
        blocks.append("\n".join(lines))
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"
