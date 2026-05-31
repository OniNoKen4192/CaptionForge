from __future__ import annotations

import re

from .model import Section, CaptionDoc, TAGS, NL
from .kind import classify_label, infer_kind
from .tags import tokenize_tags

_HEADER = re.compile(r"^===\s*(.+?)\s*===\s*$", re.MULTILINE)


def _make_section(label: str | None, body: str) -> Section:
    kind = classify_label(label) if label is not None else None
    if kind is None:
        kind = infer_kind(body)
    if kind == TAGS:
        return Section(label=label, kind=TAGS, tags=tokenize_tags(body))
    return Section(label=label, kind=NL, text=body.strip())


def parse(text: str) -> CaptionDoc:
    if not text.strip():
        return CaptionDoc(sections=[])
    matches = list(_HEADER.finditer(text))
    if not matches:
        return CaptionDoc(sections=[_make_section(None, text)])
    sections: list[Section] = []
    for i, m in enumerate(matches):
        label = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(_make_section(label, text[start:end]))
    return CaptionDoc(sections=sections)
