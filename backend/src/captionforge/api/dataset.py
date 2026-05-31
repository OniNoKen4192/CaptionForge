from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def scan_dataset(root: Path) -> list[dict]:
    items: list[dict] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTS:
            caption = entry.with_suffix(".txt")
            has = caption.is_file()
            items.append({
                "id": entry.name,
                "image": entry.name,
                "has_caption": has,
                "caption_mtime": caption.stat().st_mtime if has else None,
            })
    return items


def resolve_within(root: Path, name: str) -> Path:
    """Resolve `name` strictly as a direct file in `root`. Rejects any
    separators, parent refs, or symlink escapes."""
    if (
        "/" in name or "\\" in name or ":" in name or "\x00" in name
        or name in ("", ".", "..")
    ):
        raise ValueError(f"illegal name: {name!r}")
    root_resolved = root.resolve()
    candidate = (root_resolved / name).resolve()
    if candidate.parent != root_resolved:
        raise ValueError(f"path escapes dataset root: {name!r}")
    return candidate
