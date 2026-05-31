from __future__ import annotations

from dataclasses import dataclass, field

TAGS = "tags"
NL = "natural_language"


@dataclass
class Section:
    label: str | None
    kind: str  # TAGS | NL
    tags: list[str] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> dict:
        d: dict = {"label": self.label, "kind": self.kind}
        if self.kind == TAGS:
            d["tags"] = list(self.tags)
        else:
            d["text"] = self.text
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Section":
        return cls(
            label=d.get("label"),
            kind=d["kind"],
            tags=list(d.get("tags", [])),
            text=d.get("text", ""),
        )


@dataclass
class CaptionDoc:
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"sections": [s.to_dict() for s in self.sections]}

    @classmethod
    def from_dict(cls, d: dict) -> "CaptionDoc":
        return cls(sections=[Section.from_dict(s) for s in d.get("sections", [])])
