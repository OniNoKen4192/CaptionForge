from __future__ import annotations

import os
import tempfile
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_mtime(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


def atomic_write(path: Path, content: str) -> float:
    """Write atomically via a temp file in the same directory + os.replace.
    Always writes UTF-8 with LF newlines."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return path.stat().st_mtime
