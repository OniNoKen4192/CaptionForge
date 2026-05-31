# CaptionForge Foundation Slice — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core editing loop of a local dataset caption editor — scan a directory, parse the labeled-section caption format, preview images, edit tags and natural-language text, manage section breaks, and save safely.

**Architecture:** A Python/FastAPI backend owns the canonical caption format as a pure, fully-tested `captions` module; the REST API layers filesystem scanning, image serving, and safe atomic writes on top. A React/Vite frontend is a thin view over JSON and never parses caption text itself (the one raw-text editing mode round-trips through the backend parser).

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, pytest, httpx (TestClient); React + Vite + TypeScript, Vitest + Testing Library.

Reference spec: `docs/superpowers/specs/2026-05-31-caption-editor-foundation-design.md`
Reference dataset: `N:\AiProjects\MasamiAnimaLora` (55 pairs + an `Imported/` subfolder of unpaired PNGs).

---

## File Structure

```text
CaptionForge/
  backend/
    pyproject.toml                     package + dev deps (setuptools, src layout)
    src/captionforge/
      __init__.py
      captions/
        __init__.py                    re-exports the public API
        model.py                       Section, CaptionDoc, TAGS, NL
        tags.py                        tokenize_tags, join_tags
        kind.py                        classify_label, infer_kind
        parser.py                      parse
        serializer.py                  serialize
      api/
        __init__.py
        dataset.py                     IMAGE_EXTS, scan_dataset, resolve_within
        storage.py                     read_text, file_mtime, atomic_write
        app.py                         create_app + routes
      __main__.py                      `python -m captionforge` dev server
    tests/
      conftest.py                      shared fixtures (sample dataset)
      fixtures/sample_caption.txt      real 3-section MasamiAnima caption
      test_tags.py
      test_kind.py
      test_parser.py
      test_serializer.py
      test_dataset.py
      test_storage.py
      test_api.py
  frontend/
    package.json, vite.config.ts, tsconfig*.json, index.html
    src/
      main.tsx
      App.tsx                          top-level state + layout
      api.ts                           typed REST client
      types.ts                         Section, CaptionDoc, Item, SaveBody
      components/
        DatasetOpen.tsx
        ItemList.tsx
        ReviewPane.tsx
        ImagePreview.tsx
        NLSectionEditor.tsx
        TagChipEditor.tsx
        SectionManager.tsx
        RawMode.tsx
        TagChipEditor.test.tsx
```

**Responsibilities (one job each):**
- `captions/*` — pure format logic, no IO. The crown jewel; everything else depends on it.
- `api/dataset.py` — directory → item list; path-confinement guard.
- `api/storage.py` — read/write/mtime, atomic writes only.
- `api/app.py` — HTTP wiring; holds the single open-dataset root in `app.state`.
- Frontend `components/*` — each renders one concern; `App.tsx` owns shared state.

---

## PART 1 — BACKEND

### Task 1: Backend scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/captionforge/__init__.py` (empty)
- Create: `backend/src/captionforge/captions/__init__.py` (empty for now)
- Create: `backend/tests/test_smoke.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "captionforge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.110", "uvicorn[standard]>=0.29"]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create the two empty `__init__.py` files and a smoke test**

`backend/tests/test_smoke.py`:
```python
import captionforge

def test_package_imports():
    assert captionforge is not None
```

- [ ] **Step 3: Create venv and install (run from `backend/`)**

Run:
```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```
Expected: installs fastapi, uvicorn, pytest, httpx, and `captionforge` in editable mode.

> On PowerShell the interpreter path is `.venv\Scripts\python.exe`. All later `pytest`/`python` commands use this venv interpreter: `.venv/Scripts/python -m pytest ...`.

- [ ] **Step 4: Run the smoke test**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/src backend/tests/test_smoke.py
git commit -m "chore: backend package scaffold"
```

---

### Task 2: Caption model

**Files:**
- Create: `backend/src/captionforge/captions/model.py`
- Test: `backend/tests/test_model.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_model.py`:
```python
from captionforge.captions.model import Section, CaptionDoc, TAGS, NL


def test_tag_section_roundtrips_through_dict():
    s = Section(label="WD14-Tags", kind=TAGS, tags=["Masami", "1girl"])
    assert Section.from_dict(s.to_dict()) == s


def test_nl_section_roundtrips_through_dict():
    s = Section(label="Qwen-VL", kind=NL, text="A cat.")
    assert Section.from_dict(s.to_dict()) == s


def test_tag_dict_omits_text_and_vice_versa():
    assert "text" not in Section(label="t", kind=TAGS, tags=["a"]).to_dict()
    assert "tags" not in Section(label="n", kind=NL, text="x").to_dict()


def test_doc_roundtrips():
    doc = CaptionDoc(sections=[
        Section(label="WD14-Tags", kind=TAGS, tags=["a", "b"]),
        Section(label=None, kind=NL, text="hi"),
    ])
    assert CaptionDoc.from_dict(doc.to_dict()) == doc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_model.py -v`
Expected: FAIL with `ModuleNotFoundError: captionforge.captions.model`.

- [ ] **Step 3: Implement the model**

`backend/src/captionforge/captions/model.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_model.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/captions/model.py backend/tests/test_model.py
git commit -m "feat: caption Section/CaptionDoc model"
```

---

### Task 3: Tag tokenizer and joiner

**Files:**
- Create: `backend/src/captionforge/captions/tags.py`
- Test: `backend/tests/test_tags.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_tags.py`:
```python
from captionforge.captions.tags import tokenize_tags, join_tags


def test_splits_jammed_trigger():
    # Real quirk: "Masami,1girl" has no space after the first comma.
    assert tokenize_tags("Masami,1girl, solo") == ["Masami", "1girl", "solo"]


def test_drops_trailing_comma_phantom():
    assert tokenize_tags("a, b, c,") == ["a", "b", "c"]


def test_strips_and_drops_empties():
    assert tokenize_tags("  a ,, b ") == ["a", "b"]


def test_preserves_duplicates():
    assert tokenize_tags("a, a, b") == ["a", "a", "b"]


def test_join_uses_comma_space():
    assert join_tags(["a", "b", "c"]) == "a, b, c"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_tags.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`backend/src/captionforge/captions/tags.py`:
```python
from __future__ import annotations


def tokenize_tags(body: str) -> list[str]:
    return [t.strip() for t in body.split(",") if t.strip()]


def join_tags(tags: list[str]) -> str:
    return ", ".join(tags)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_tags.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/captions/tags.py backend/tests/test_tags.py
git commit -m "feat: tag tokenizer/joiner surviving real quirks"
```

---

### Task 4: Section-kind classification

**Files:**
- Create: `backend/src/captionforge/captions/kind.py`
- Test: `backend/tests/test_kind.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_kind.py`:
```python
from captionforge.captions.kind import classify_label, infer_kind
from captionforge.captions.model import TAGS, NL


def test_label_match_tags():
    assert classify_label("WD14-Tags") == TAGS
    assert classify_label("danbooru tags") == TAGS


def test_label_match_nl():
    assert classify_label("Qwen-VL") == NL
    assert classify_label("JoyCaption2") == NL


def test_label_unknown_returns_none():
    assert classify_label("Notes") is None


def test_infer_tags_from_short_comma_fragments():
    body = "1girl, solo, long hair, blue eyes, simple background"
    assert infer_kind(body) == TAGS


def test_infer_nl_from_prose_with_commas():
    body = "A cat lies on a bed, facing the viewer. The lighting is soft."
    assert infer_kind(body) == NL


def test_infer_nl_from_empty():
    assert infer_kind("   ") == NL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_kind.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`backend/src/captionforge/captions/kind.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_kind.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/captions/kind.py backend/tests/test_kind.py
git commit -m "feat: section-kind classification (label + content heuristic)"
```

---

### Task 5: Test fixtures (real caption sample)

**Files:**
- Create: `backend/tests/fixtures/sample_caption.txt`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create the real-sample fixture**

`backend/tests/fixtures/sample_caption.txt` (mirrors `MasamiAnima (1).txt`, quirks intact — note `Masami,1girl` and the trailing comma):
```text
=== WD14-Tags ===
Masami,1girl, solo, long hair, blue eyes, black hair, cat ears, nude,

=== Qwen-VL ===
The image depicts an anthropomorphic cat character with black fur, blue eyes, and long black hair styled in a high ponytail.

=== JoyCaption2 ===
This digital drawing features an anthropomorphic black cat with blue eyes, lying on a white surface against a beige background.
```

- [ ] **Step 2: Create `conftest.py` with a loader fixture**

`backend/tests/conftest.py`:
```python
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_caption_text() -> str:
    return (FIXTURES / "sample_caption.txt").read_text(encoding="utf-8")
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/fixtures/sample_caption.txt backend/tests/conftest.py
git commit -m "test: real caption fixture + conftest"
```

---

### Task 6: Parser — headered captions

**Files:**
- Create: `backend/src/captionforge/captions/parser.py`
- Test: `backend/tests/test_parser.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_parser.py`:
```python
from captionforge.captions.parser import parse
from captionforge.captions.model import TAGS, NL


def test_parses_three_real_sections(sample_caption_text):
    doc = parse(sample_caption_text)
    labels = [s.label for s in doc.sections]
    kinds = [s.kind for s in doc.sections]
    assert labels == ["WD14-Tags", "Qwen-VL", "JoyCaption2"]
    assert kinds == [TAGS, NL, NL]


def test_tag_section_tokenized_with_quirks(sample_caption_text):
    doc = parse(sample_caption_text)
    tags = doc.sections[0].tags
    assert tags[:3] == ["Masami", "1girl", "solo"]
    assert "" not in tags  # trailing comma produced no phantom


def test_nl_section_text_is_stripped(sample_caption_text):
    doc = parse(sample_caption_text)
    assert doc.sections[1].text.startswith("The image depicts")
    assert not doc.sections[1].text.endswith("\n")


def test_label_order_is_preserved_not_assumed():
    text = "=== JoyCaption2 ===\nprose here.\n\n=== WD14-Tags ===\na, b, c"
    doc = parse(text)
    assert [s.label for s in doc.sections] == ["JoyCaption2", "WD14-Tags"]
    assert doc.sections[1].kind == TAGS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the parser**

`backend/src/captionforge/captions/parser.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/captions/parser.py backend/tests/test_parser.py
git commit -m "feat: parser for headered captions"
```

---

### Task 7: Parser — degradation ladder

**Files:**
- Modify: `backend/tests/test_parser.py` (append tests)

- [ ] **Step 1: Append failing tests**

Add to `backend/tests/test_parser.py`:
```python
def test_headerless_tag_blob_is_single_tag_section():
    doc = parse("1girl, solo, long hair, blue eyes")
    assert len(doc.sections) == 1
    assert doc.sections[0].label is None
    assert doc.sections[0].kind == TAGS
    assert doc.sections[0].tags == ["1girl", "solo", "long hair", "blue eyes"]


def test_headerless_prose_is_single_nl_section():
    doc = parse("A cat sits on a mat. It is calm.")
    assert len(doc.sections) == 1
    assert doc.sections[0].kind == NL
    assert doc.sections[0].label is None


def test_empty_file_yields_no_sections():
    assert parse("").sections == []
    assert parse("   \n  ").sections == []


def test_unknown_label_defaults_to_nl():
    doc = parse("=== Notes ===\nremember to recheck lighting")
    assert doc.sections[0].label == "Notes"
    assert doc.sections[0].kind == NL


def test_unknown_label_with_taglike_body_infers_tags():
    doc = parse("=== Misc ===\nred, blue, green, yellow, black")
    assert doc.sections[0].kind == TAGS
```

- [ ] **Step 2: Run to verify the new tests pass (parser already handles these)**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: PASS (all, including the 5 new). If any fail, fix `parser.py`/`kind.py` until green — do not weaken the assertions.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_parser.py
git commit -m "test: parser degradation ladder (headerless/empty/unknown)"
```

---

### Task 8: Serializer + round-trip invariant

**Files:**
- Create: `backend/src/captionforge/captions/serializer.py`
- Create: `backend/src/captionforge/captions/__init__.py` (re-exports — overwrite the empty file)
- Test: `backend/tests/test_serializer.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_serializer.py`:
```python
from captionforge.captions import parse, serialize, CaptionDoc, Section, TAGS, NL


def test_serializes_canonical_layout():
    doc = CaptionDoc(sections=[
        Section(label="WD14-Tags", kind=TAGS, tags=["Masami", "1girl"]),
        Section(label="Qwen-VL", kind=NL, text="A cat."),
    ])
    assert serialize(doc) == (
        "=== WD14-Tags ===\n"
        "Masami, 1girl\n"
        "\n"
        "=== Qwen-VL ===\n"
        "A cat.\n"
    )


def test_headerless_section_emits_no_header():
    doc = CaptionDoc(sections=[Section(label=None, kind=TAGS, tags=["a", "b"])])
    assert serialize(doc) == "a, b\n"


def test_empty_doc_serializes_to_empty_string():
    assert serialize(CaptionDoc(sections=[])) == ""


def test_roundtrip_idempotent_on_real_sample(sample_caption_text):
    once = parse(sample_caption_text)
    assert parse(serialize(once)) == once


def test_normalize_fixes_spacing_not_content(sample_caption_text):
    out = serialize(parse(sample_caption_text))
    assert "Masami, 1girl, solo" in out  # space added after the trigger
    assert "nude," not in out            # trailing comma gone
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_serializer.py -v`
Expected: FAIL with `ImportError` (no `serialize`, `__init__` not exporting).

- [ ] **Step 3: Implement serializer and package exports**

`backend/src/captionforge/captions/serializer.py`:
```python
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
```

`backend/src/captionforge/captions/__init__.py` (replace empty file):
```python
from .model import Section, CaptionDoc, TAGS, NL
from .tags import tokenize_tags, join_tags
from .kind import classify_label, infer_kind
from .parser import parse
from .serializer import serialize

__all__ = [
    "Section", "CaptionDoc", "TAGS", "NL",
    "tokenize_tags", "join_tags", "classify_label", "infer_kind",
    "parse", "serialize",
]
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_serializer.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Run the whole captions suite**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_model.py tests/test_tags.py tests/test_kind.py tests/test_parser.py tests/test_serializer.py -v`
Expected: PASS (all).

- [ ] **Step 6: Commit**

```bash
git add backend/src/captionforge/captions/serializer.py backend/src/captionforge/captions/__init__.py backend/tests/test_serializer.py
git commit -m "feat: serializer + round-trip idempotence; export captions API"
```

> **Known limitation (documented, not handled):** if a natural-language section's
> text itself contains a line matching `=== something ===`, round-trip will
> mis-split it into an extra section. Real captions don't do this; revisit only
> if it occurs.

> **Guardrail — do NOT extend the serializer to rewrite tag content.** It joins
> tags with `", "` and nothing more. Tag *text* (underscores, `@artist`,
> `score_X`) stays verbatim. Correct underscore/space/`@` normalization is
> **profile-dependent** (Anima: spaces except `score_X`; Pony: underscores
> tolerated; Illustrious: interchangeable) and belongs to the future profile
> layer (`Docs/captioning/curation-rules.md`), not here. The
> `test_normalize_fixes_spacing_not_content` test guards this — keep it.

---

### Task 9: Dataset scan + path confinement

**Files:**
- Create: `backend/src/captionforge/api/__init__.py` (empty)
- Create: `backend/src/captionforge/api/dataset.py`
- Test: `backend/tests/test_dataset.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_dataset.py`:
```python
from pathlib import Path

import pytest

from captionforge.api.dataset import scan_dataset, resolve_within, IMAGE_EXTS


def _touch(p: Path, content: str = "x"):
    p.write_text(content, encoding="utf-8")


def test_scan_pairs_by_stem_and_lists_unpaired(tmp_path: Path):
    _touch(tmp_path / "a.png")
    _touch(tmp_path / "a.txt")
    _touch(tmp_path / "b.jpg")  # unpaired image
    (tmp_path / "sub").mkdir()
    _touch(tmp_path / "sub" / "c.png")  # must NOT be found (non-recursive)

    items = scan_dataset(tmp_path)
    by_id = {it["id"]: it for it in items}

    assert set(by_id) == {"a.png", "b.jpg"}
    assert by_id["a.png"]["has_caption"] is True
    assert by_id["b.jpg"]["has_caption"] is False
    assert by_id["a.png"]["caption_mtime"] is not None
    assert by_id["b.jpg"]["caption_mtime"] is None


def test_scan_is_sorted(tmp_path: Path):
    for name in ["z.png", "m.png", "a.png"]:
        _touch(tmp_path / name)
    assert [it["id"] for it in scan_dataset(tmp_path)] == ["a.png", "m.png", "z.png"]


def test_supported_extensions():
    assert IMAGE_EXTS == {".png", ".jpg", ".jpeg", ".webp"}


def test_resolve_within_allows_direct_child(tmp_path: Path):
    _touch(tmp_path / "a.png")
    assert resolve_within(tmp_path, "a.png") == (tmp_path / "a.png").resolve()


def test_resolve_within_rejects_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        resolve_within(tmp_path, "../secret.txt")
    with pytest.raises(ValueError):
        resolve_within(tmp_path, "sub/c.png")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`backend/src/captionforge/api/dataset.py`:
```python
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
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        raise ValueError(f"illegal name: {name!r}")
    root_resolved = root.resolve()
    candidate = (root_resolved / name).resolve()
    if candidate.parent != root_resolved:
        raise ValueError(f"path escapes dataset root: {name!r}")
    return candidate
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_dataset.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/api/__init__.py backend/src/captionforge/api/dataset.py backend/tests/test_dataset.py
git commit -m "feat: dataset scan + path-confinement guard"
```

---

### Task 10: Storage — read, mtime, atomic write

**Files:**
- Create: `backend/src/captionforge/api/storage.py`
- Test: `backend/tests/test_storage.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_storage.py`:
```python
from pathlib import Path

from captionforge.api.storage import read_text, file_mtime, atomic_write


def test_file_mtime_none_when_missing(tmp_path: Path):
    assert file_mtime(tmp_path / "nope.txt") is None


def test_atomic_write_creates_file_lf_utf8(tmp_path: Path):
    target = tmp_path / "out.txt"
    mtime = atomic_write(target, "line1\nline2\n")
    raw = target.read_bytes()
    assert raw == b"line1\nline2\n"  # LF preserved, no CRLF, no BOM
    assert isinstance(mtime, float)
    assert file_mtime(target) == mtime


def test_atomic_write_overwrites(tmp_path: Path):
    target = tmp_path / "out.txt"
    atomic_write(target, "old")
    atomic_write(target, "new")
    assert read_text(target) == "new"


def test_atomic_write_leaves_no_tmp_files(tmp_path: Path):
    target = tmp_path / "out.txt"
    atomic_write(target, "data")
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "out.txt"]
    assert leftovers == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_storage.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`backend/src/captionforge/api/storage.py`:
```python
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_storage.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/api/storage.py backend/tests/test_storage.py
git commit -m "feat: storage read/mtime/atomic-write (LF, UTF-8)"
```

---

### Task 11: FastAPI app — open dataset + parse

**Files:**
- Create: `backend/src/captionforge/api/app.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api.py`:
```python
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from captionforge.api.app import create_app


@pytest.fixture
def dataset_dir(tmp_path: Path) -> Path:
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG-ish bytes
    (tmp_path / "a.txt").write_text(
        "=== WD14-Tags ===\nMasami,1girl, solo,\n\n=== Qwen-VL ===\nA cat.\n",
        encoding="utf-8",
    )
    (tmp_path / "b.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # unpaired
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_open_lists_items(client, dataset_dir):
    r = client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    assert r.status_code == 200
    ids = {it["id"]: it for it in r.json()["items"]}
    assert set(ids) == {"a.png", "b.png"}
    assert ids["a.png"]["has_caption"] is True
    assert ids["b.png"]["has_caption"] is False


def test_open_rejects_missing_dir(client, tmp_path):
    r = client.post("/api/dataset/open", json={"path": str(tmp_path / "ghost")})
    assert r.status_code == 400


def test_parse_endpoint(client):
    r = client.post("/api/parse", json={"raw": "=== Misc ===\na, b, c"})
    assert r.status_code == 200
    secs = r.json()["sections"]
    assert secs[0]["kind"] == "tags"
    assert secs[0]["tags"] == ["a", "b", "c"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the app with the first two routes**

`backend/src/captionforge/api/app.py`:
```python
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..captions import parse, serialize, CaptionDoc
from . import dataset as ds
from . import storage


class OpenBody(BaseModel):
    path: str


class ParseBody(BaseModel):
    raw: str


def create_app() -> FastAPI:
    app = FastAPI(title="CaptionForge")
    app.state.root = None

    def require_root() -> Path:
        if app.state.root is None:
            raise HTTPException(status_code=409, detail="no dataset open")
        return app.state.root

    @app.post("/api/dataset/open")
    def open_dataset(body: OpenBody):
        root = Path(body.path)
        if not root.is_dir():
            raise HTTPException(status_code=400, detail="not a directory")
        app.state.root = root.resolve()
        return {"root": str(app.state.root), "items": ds.scan_dataset(app.state.root)}

    @app.post("/api/parse")
    def parse_raw(body: ParseBody):
        return parse(body.raw).to_dict()

    return app
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/api/app.py backend/tests/test_api.py
git commit -m "feat: API open-dataset + parse endpoints"
```

---

### Task 12: Item read + image serving

**Files:**
- Modify: `backend/src/captionforge/api/app.py`
- Modify: `backend/tests/test_api.py` (append)

- [ ] **Step 1: Append failing tests**

Add to `backend/tests/test_api.py`:
```python
def test_get_item_returns_parsed_sections(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/item/a.png")
    assert r.status_code == 200
    data = r.json()
    assert data["sections"][0]["tags"][:2] == ["Masami", "1girl"]
    assert data["caption_mtime"] is not None
    assert data["image_url"].endswith("/api/image/a.png")


def test_get_unpaired_item_has_empty_sections(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/item/b.png")
    assert r.status_code == 200
    assert r.json()["sections"] == []
    assert r.json()["caption_mtime"] is None


def test_get_image_returns_bytes(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/image/a.png")
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")


def test_item_rejects_traversal(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    assert client.get("/api/item/..%2Fsecret.txt").status_code == 400
```

- [ ] **Step 2: Run to verify the new tests fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: FAIL (404/405 on the new routes).

- [ ] **Step 3: Add the routes**

Insert into `create_app()` in `backend/src/captionforge/api/app.py`, before `return app`. Add `from urllib.parse import quote` and `from fastapi.responses import FileResponse` to the imports at the top:
```python
    @app.get("/api/item/{item_id}")
    def get_item(item_id: str):
        root = require_root()
        try:
            image_path = ds.resolve_within(root, item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad item id")
        if not image_path.is_file():
            raise HTTPException(status_code=404, detail="no such image")
        caption_path = image_path.with_suffix(".txt")
        if caption_path.is_file():
            doc = parse(storage.read_text(caption_path))
            mtime = storage.file_mtime(caption_path)
        else:
            doc = CaptionDoc(sections=[])
            mtime = None
        return {
            "image_url": f"/api/image/{quote(item_id)}",
            "sections": doc.to_dict()["sections"],
            "caption_mtime": mtime,
        }

    @app.get("/api/image/{item_id}")
    def get_image(item_id: str):
        root = require_root()
        try:
            image_path = ds.resolve_within(root, item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad item id")
        if not image_path.is_file():
            raise HTTPException(status_code=404, detail="no such image")
        return FileResponse(image_path)
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: PASS (7 tests total).

- [ ] **Step 5: Commit**

```bash
git add backend/src/captionforge/api/app.py backend/tests/test_api.py
git commit -m "feat: API get-item + image serving with path confinement"
```

---

### Task 13: Item save (sections | raw) with 409 guard + create-on-save

**Files:**
- Modify: `backend/src/captionforge/api/app.py`
- Modify: `backend/tests/test_api.py` (append)

- [ ] **Step 1: Append failing tests**

Add to `backend/tests/test_api.py`:
```python
def _open(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})


def test_save_sections_normalizes_and_returns_mtime(client, dataset_dir):
    _open(client, dataset_dir)
    base = client.get("/api/item/a.png").json()["caption_mtime"]
    body = {
        "sections": [
            {"label": "WD14-Tags", "kind": "tags", "tags": ["Masami", "1girl", "cat ears"]},
        ],
        "base_mtime": base,
    }
    r = client.put("/api/item/a.png", json=body)
    assert r.status_code == 200
    on_disk = (dataset_dir / "a.txt").read_text(encoding="utf-8")
    assert on_disk == "=== WD14-Tags ===\nMasami, 1girl, cat ears\n"


def test_save_raw_is_parsed_and_normalized(client, dataset_dir):
    _open(client, dataset_dir)
    base = client.get("/api/item/a.png").json()["caption_mtime"]
    r = client.put("/api/item/a.png", json={"raw": "=== T ===\nx,y,z,", "base_mtime": base})
    assert r.status_code == 200
    assert (dataset_dir / "a.txt").read_text(encoding="utf-8") == "=== T ===\nx, y, z\n"


def test_save_conflict_on_stale_mtime(client, dataset_dir):
    _open(client, dataset_dir)
    r = client.put("/api/item/a.png", json={"sections": [], "base_mtime": 1.0})
    assert r.status_code == 409


def test_save_creates_caption_for_unpaired(client, dataset_dir):
    _open(client, dataset_dir)
    body = {"sections": [{"label": None, "kind": "tags", "tags": ["a", "b"]}], "base_mtime": None}
    r = client.put("/api/item/b.png", json=body)
    assert r.status_code == 200
    assert (dataset_dir / "b.txt").read_text(encoding="utf-8") == "a, b\n"


def test_save_rejects_both_or_neither_payloads(client, dataset_dir):
    _open(client, dataset_dir)
    base = client.get("/api/item/a.png").json()["caption_mtime"]
    assert client.put("/api/item/a.png", json={"base_mtime": base}).status_code == 422
    assert client.put(
        "/api/item/a.png",
        json={"sections": [], "raw": "x", "base_mtime": base},
    ).status_code == 422
```

- [ ] **Step 2: Run to verify the new tests fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: FAIL (405/404 — PUT route missing).

- [ ] **Step 3: Add the save route**

Add a `SaveBody` model near the other models in `app.py`:
```python
class SaveBody(BaseModel):
    sections: list[dict] | None = None
    raw: str | None = None
    base_mtime: float | None = None
```

Insert this route into `create_app()` before `return app`:
```python
    @app.put("/api/item/{item_id}")
    def save_item(item_id: str, body: SaveBody):
        root = require_root()
        try:
            image_path = ds.resolve_within(root, item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad item id")
        if not image_path.is_file():
            raise HTTPException(status_code=404, detail="no such image")

        has_sections = body.sections is not None
        has_raw = body.raw is not None
        if has_sections == has_raw:  # both or neither
            raise HTTPException(status_code=422, detail="provide exactly one of sections|raw")

        if has_raw:
            doc = parse(body.raw)
        else:
            doc = CaptionDoc.from_dict({"sections": body.sections})

        caption_path = image_path.with_suffix(".txt")
        current = storage.file_mtime(caption_path)
        if current is not None and body.base_mtime != current:
            raise HTTPException(status_code=409, detail="file changed externally")

        new_mtime = storage.atomic_write(caption_path, serialize(doc))
        return {"sections": doc.to_dict()["sections"], "caption_mtime": new_mtime}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: PASS (12 tests total).

- [ ] **Step 5: Run the full backend suite**

Run: `cd backend && .venv/Scripts/python -m pytest -v`
Expected: PASS (all suites).

- [ ] **Step 6: Commit**

```bash
git add backend/src/captionforge/api/app.py backend/tests/test_api.py
git commit -m "feat: API save-item (sections|raw), 409 guard, create-on-save"
```

---

### Task 14: Dev server entrypoint

**Files:**
- Create: `backend/src/captionforge/__main__.py`

- [ ] **Step 1: Write the entrypoint**

`backend/src/captionforge/__main__.py`:
```python
from __future__ import annotations

import uvicorn

from .api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

- [ ] **Step 2: Manually verify the server boots**

Run: `cd backend && .venv/Scripts/python -m captionforge`
Expected: uvicorn logs "Uvicorn running on http://127.0.0.1:8000". In another shell:
`curl -s -X POST http://127.0.0.1:8000/api/dataset/open -H "Content-Type: application/json" -d "{\"path\": \"N:\\\\AiProjects\\\\MasamiAnimaLora\"}"`
Expected: JSON with 55 items. Stop the server (Ctrl+C).

- [ ] **Step 3: Commit**

```bash
git add backend/src/captionforge/__main__.py
git commit -m "feat: dev server entrypoint (python -m captionforge)"
```

---

## PART 2 — FRONTEND

### Task 15: Vite scaffold + dev proxy

**Files:**
- Create: `frontend/` (via Vite) then edit `vite.config.ts`

- [ ] **Step 1: Scaffold the app**

Run (from repo root):
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Add the API proxy and Vitest config**

Replace `frontend/vite.config.ts` with:
```ts
/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 3: Install test deps**

Run: `cd frontend && npm install -D vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom`

- [ ] **Step 4: Add the test script to `package.json`**

In `frontend/package.json`, add to `"scripts"`: `"test": "vitest run"`.

- [ ] **Step 5: Verify dev server starts**

Run: `cd frontend && npm run dev`
Expected: Vite serves on http://localhost:5173. Stop it (Ctrl+C).

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "chore: vite react-ts scaffold + api proxy + vitest"
```

> If `frontend/.gitignore` (from the Vite template) does not already ignore
> `node_modules`, add it before committing.

---

### Task 16: Types + API client

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Write the types**

`frontend/src/types.ts`:
```ts
export type Kind = "tags" | "natural_language";

export interface Section {
  label: string | null;
  kind: Kind;
  tags?: string[];
  text?: string;
}

export interface Item {
  id: string;
  image: string;
  has_caption: boolean;
  caption_mtime: number | null;
}

export interface ItemDetail {
  image_url: string;
  sections: Section[];
  caption_mtime: number | null;
}

export interface SaveResult {
  sections: Section[];
  caption_mtime: number;
}
```

- [ ] **Step 2: Write the API client**

`frontend/src/api.ts`:
```ts
import type { Item, ItemDetail, Section, SaveResult } from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw { status: res.status, detail: (detail as any).detail ?? res.statusText };
  }
  return res.json() as Promise<T>;
}

export async function openDataset(path: string): Promise<{ root: string; items: Item[] }> {
  return json(await fetch("/api/dataset/open", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  }));
}

export async function getItem(id: string): Promise<ItemDetail> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`));
}

export async function parseRaw(raw: string): Promise<{ sections: Section[] }> {
  return json(await fetch("/api/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw }),
  }));
}

export async function saveSections(
  id: string, sections: Section[], baseMtime: number | null,
): Promise<SaveResult> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections, base_mtime: baseMtime }),
  }));
}

export async function saveRaw(
  id: string, raw: string, baseMtime: number | null,
): Promise<SaveResult> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw, base_mtime: baseMtime }),
  }));
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts
git commit -m "feat: frontend types + REST client"
```

---

### Task 17: Tag chip editor (the one tested component)

**Files:**
- Create: `frontend/src/components/TagChipEditor.tsx`
- Test: `frontend/src/components/TagChipEditor.test.tsx`

- [ ] **Step 1: Write the failing test**

`frontend/src/components/TagChipEditor.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, it, expect } from "vitest";
import { TagChipEditor } from "./TagChipEditor";

function Harness({ initial }: { initial: string[] }) {
  const [tags, setTags] = useState(initial);
  return <TagChipEditor tags={tags} onChange={setTags} />;
}

describe("TagChipEditor", () => {
  it("adds a tag via the input on Enter", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a"]} />);
    await user.type(screen.getByPlaceholderText("add tag"), "blue eyes{Enter}");
    expect(screen.getByText("blue eyes")).toBeInTheDocument();
  });

  it("removes a tag via its ✕ button", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b"]} />);
    await user.click(screen.getByRole("button", { name: "remove a" }));
    expect(screen.queryByText("a")).not.toBeInTheDocument();
    expect(screen.getByText("b")).toBeInTheDocument();
  });

  it("dedupes preserving first-seen order", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b", "a", "c", "b"]} />);
    await user.click(screen.getByRole("button", { name: "dedupe" }));
    const chips = screen.getAllByTestId("chip").map((c) => c.textContent?.replace("✕", "").trim());
    expect(chips).toEqual(["a", "b", "c"]);
  });
});
```

- [ ] **Step 2: Add the jest-dom matchers setup**

Create `frontend/src/setupTests.ts`:
```ts
import "@testing-library/jest-dom";
```
Add to `vite.config.ts` `test` block: `setupFiles: ["./src/setupTests.ts"],`.

- [ ] **Step 3: Run to verify it fails**

Run: `cd frontend && npm run test`
Expected: FAIL (no `TagChipEditor`).

- [ ] **Step 4: Implement the component**

`frontend/src/components/TagChipEditor.tsx`:
```tsx
import { useState } from "react";

interface Props {
  tags: string[];
  onChange: (tags: string[]) => void;
}

export function TagChipEditor({ tags, onChange }: Props) {
  const [draft, setDraft] = useState("");

  function addDraft() {
    const t = draft.trim();
    if (t) onChange([...tags, t]);
    setDraft("");
  }

  function removeAt(i: number) {
    onChange(tags.filter((_, idx) => idx !== i));
  }

  function dedupe() {
    const seen = new Set<string>();
    onChange(tags.filter((t) => (seen.has(t) ? false : (seen.add(t), true))));
  }

  return (
    <div className="tag-chip-editor">
      <div className="chips">
        {tags.map((t, i) => (
          <span className="chip" data-testid="chip" key={`${t}-${i}`}>
            {t}
            <button aria-label={`remove ${t}`} onClick={() => removeAt(i)}>✕</button>
          </span>
        ))}
      </div>
      <div className="chip-controls">
        <input
          placeholder="add tag"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addDraft();
            }
          }}
        />
        <button onClick={dedupe}>dedupe</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd frontend && npm run test`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/TagChipEditor.tsx frontend/src/components/TagChipEditor.test.tsx frontend/src/setupTests.ts frontend/vite.config.ts
git commit -m "feat: TagChipEditor with add/remove/dedupe (tested)"
```

> Reorder (drag or up/down) is part of the spec. Keep it out of this task to keep
> the tested component small; it is added in Task 20's SectionManager context via
> simple up/down buttons on the tag list. If you prefer it here, add ↑/↓ buttons
> calling an `onChange` with swapped indices — but do it test-first.

---

### Task 18: NL section editor + image preview

**Files:**
- Create: `frontend/src/components/NLSectionEditor.tsx`
- Create: `frontend/src/components/ImagePreview.tsx`

- [ ] **Step 1: Implement the NL editor**

`frontend/src/components/NLSectionEditor.tsx`:
```tsx
interface Props {
  text: string;
  onChange: (text: string) => void;
}

export function NLSectionEditor({ text, onChange }: Props) {
  return (
    <textarea
      className="nl-editor"
      style={{ width: "100%", minHeight: "8rem", whiteSpace: "pre-wrap" }}
      value={text}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
```

- [ ] **Step 2: Implement the image preview**

`frontend/src/components/ImagePreview.tsx`:
```tsx
interface Props {
  url: string | null;
}

export function ImagePreview({ url }: Props) {
  if (!url) return <div className="image-preview empty">No image</div>;
  return (
    <div className="image-preview">
      <img src={url} alt="" style={{ maxWidth: "100%", maxHeight: "80vh" }} />
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/NLSectionEditor.tsx frontend/src/components/ImagePreview.tsx
git commit -m "feat: NL section editor + image preview components"
```

---

### Task 19: Section manager (add/label/kind-toggle/remove/reorder)

**Files:**
- Create: `frontend/src/components/SectionManager.tsx`

- [ ] **Step 1: Implement the section manager**

`frontend/src/components/SectionManager.tsx`:
```tsx
import type { Section, Kind } from "../types";
import { TagChipEditor } from "./TagChipEditor";
import { NLSectionEditor } from "./NLSectionEditor";

interface Props {
  sections: Section[];
  onChange: (sections: Section[]) => void;
}

function toTags(text: string): string[] {
  return text.split(",").map((t) => t.trim()).filter(Boolean);
}

export function SectionManager({ sections, onChange }: Props) {
  function update(i: number, patch: Partial<Section>) {
    onChange(sections.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));
  }

  function toggleKind(i: number) {
    const s = sections[i];
    if (s.kind === "tags") {
      update(i, { kind: "natural_language", text: (s.tags ?? []).join(", "), tags: [] });
    } else {
      update(i, { kind: "tags", tags: toTags(s.text ?? ""), text: "" });
    }
  }

  function move(i: number, delta: number) {
    const j = i + delta;
    if (j < 0 || j >= sections.length) return;
    const next = [...sections];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }

  function remove(i: number) {
    onChange(sections.filter((_, idx) => idx !== i));
  }

  function add() {
    onChange([...sections, { label: "New Section", kind: "natural_language", text: "" }]);
  }

  return (
    <div className="section-manager">
      {sections.map((s, i) => (
        <div className="section" key={i}>
          <div className="section-head">
            <input
              value={s.label ?? ""}
              placeholder="(no label)"
              onChange={(e) => update(i, { label: e.target.value || null })}
            />
            <button onClick={() => toggleKind(i)}>
              {s.kind === "tags" ? "tags → NL" : "NL → tags"}
            </button>
            <button aria-label="move up" onClick={() => move(i, -1)}>↑</button>
            <button aria-label="move down" onClick={() => move(i, 1)}>↓</button>
            <button aria-label="remove section" onClick={() => remove(i)}>🗑</button>
          </div>
          {s.kind === "tags" ? (
            <TagChipEditor tags={s.tags ?? []} onChange={(tags) => update(i, { tags })} />
          ) : (
            <NLSectionEditor text={s.text ?? ""} onChange={(text) => update(i, { text })} />
          )}
        </div>
      ))}
      <button className="add-section" onClick={add}>+ Add section</button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SectionManager.tsx
git commit -m "feat: section manager (add/label/kind-toggle/reorder/remove)"
```

---

### Task 20: Raw-text mode

**Files:**
- Create: `frontend/src/components/RawMode.tsx`

- [ ] **Step 1: Implement raw mode**

`frontend/src/components/RawMode.tsx`:
```tsx
interface Props {
  raw: string;
  onChange: (raw: string) => void;
}

export function RawMode({ raw, onChange }: Props) {
  return (
    <textarea
      className="raw-mode"
      style={{ width: "100%", minHeight: "24rem", fontFamily: "monospace", whiteSpace: "pre" }}
      value={raw}
      onChange={(e) => onChange(e.target.value)}
      spellCheck={false}
    />
  );
}
```

> Note: raw↔structured conversion lives in `ReviewPane` (Task 21), which calls
> `parseRaw` (backend) when switching from raw to structured, and serializes
> structured→raw locally only as a *display seed* when entering raw mode. On
> save, raw mode always sends `{raw}` so the backend is the single parser.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/RawMode.tsx
git commit -m "feat: raw-text editing mode component"
```

---

### Task 21: Review pane (wires editors + save + 409 reload)

**Files:**
- Create: `frontend/src/components/ReviewPane.tsx`

- [ ] **Step 1: Implement the review pane**

`frontend/src/components/ReviewPane.tsx`:
```tsx
import { useEffect, useState } from "react";
import type { Item, Section } from "../types";
import { getItem, parseRaw, saveRaw, saveSections } from "../api";
import { ImagePreview } from "./ImagePreview";
import { SectionManager } from "./SectionManager";
import { RawMode } from "./RawMode";

interface Props {
  item: Item;
  onSaved: (mtime: number) => void;
}

function sectionsToRaw(sections: Section[]): string {
  return sections
    .map((s) => {
      const head = s.label !== null ? `=== ${s.label} ===\n` : "";
      const body = s.kind === "tags" ? (s.tags ?? []).join(", ") : (s.text ?? "");
      return head + body;
    })
    .join("\n\n");
}

export function ReviewPane({ item, onSaved }: Props) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [baseMtime, setBaseMtime] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);
  const [raw, setRaw] = useState<string | null>(null); // non-null => raw mode
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    const detail = await getItem(item.id);
    setImageUrl(detail.image_url);
    setSections(detail.sections);
    setBaseMtime(detail.caption_mtime);
    setDirty(false);
    setRaw(null);
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [item.id]);

  function editSections(next: Section[]) {
    setSections(next);
    setDirty(true);
  }

  async function enterRaw() {
    setRaw(sectionsToRaw(sections));
  }

  async function exitRaw() {
    if (raw !== null) {
      const parsed = await parseRaw(raw);
      setSections(parsed.sections);
      setDirty(true);
    }
    setRaw(null);
  }

  async function save() {
    setError(null);
    try {
      const result = raw !== null
        ? await saveRaw(item.id, raw, baseMtime)
        : await saveSections(item.id, sections, baseMtime);
      setSections(result.sections);
      setBaseMtime(result.caption_mtime);
      setDirty(false);
      setRaw(null);
      onSaved(result.caption_mtime);
    } catch (e: any) {
      if (e.status === 409) {
        setError("File changed on disk. Reload to get the latest (discards your edits)?");
      } else {
        setError(String(e.detail ?? e));
      }
    }
  }

  return (
    <div className="review-pane" style={{ display: "flex", gap: "1rem" }}>
      <div style={{ flex: 1 }}>
        <ImagePreview url={imageUrl} />
      </div>
      <div style={{ flex: 1 }}>
        <div className="toolbar">
          <button onClick={save} disabled={!dirty && raw === null}>Save{dirty ? " *" : ""}</button>
          {raw === null
            ? <button onClick={enterRaw}>Edit raw</button>
            : <button onClick={exitRaw}>Structured</button>}
        </div>
        {error && (
          <div className="error" role="alert">
            {error} <button onClick={load}>Reload</button>
          </div>
        )}
        {raw === null
          ? <SectionManager sections={sections} onChange={editSections} />
          : <RawMode raw={raw} onChange={(r) => { setRaw(r); setDirty(true); }} />}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ReviewPane.tsx
git commit -m "feat: review pane wiring editors, save, raw toggle, 409 reload"
```

---

### Task 22: Dataset open + item list + App shell + keyboard nav

**Files:**
- Create: `frontend/src/components/DatasetOpen.tsx`
- Create: `frontend/src/components/ItemList.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx` (ensure it renders `<App/>` — Vite default already does)

- [ ] **Step 1: Dataset open form**

`frontend/src/components/DatasetOpen.tsx`:
```tsx
import { useState } from "react";

interface Props {
  onOpen: (path: string) => void;
}

export function DatasetOpen({ onOpen }: Props) {
  const [path, setPath] = useState("");
  return (
    <form
      className="dataset-open"
      onSubmit={(e) => { e.preventDefault(); if (path.trim()) onOpen(path.trim()); }}
    >
      <input
        style={{ width: "30rem" }}
        placeholder="dataset directory path"
        value={path}
        onChange={(e) => setPath(e.target.value)}
      />
      <button type="submit">Open</button>
    </form>
  );
}
```

- [ ] **Step 2: Item list**

`frontend/src/components/ItemList.tsx`:
```tsx
import type { Item } from "../types";

interface Props {
  items: Item[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ItemList({ items, selectedId, onSelect }: Props) {
  return (
    <ul className="item-list" style={{ listStyle: "none", margin: 0, padding: 0, overflowY: "auto" }}>
      {items.map((it) => (
        <li key={it.id}>
          <button
            onClick={() => onSelect(it.id)}
            style={{ fontWeight: it.id === selectedId ? "bold" : "normal", width: "100%", textAlign: "left" }}
          >
            {it.has_caption ? "📝" : "◻"} {it.id}
          </button>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 3: App shell with state + keyboard nav**

`frontend/src/App.tsx` (replace the template contents):
```tsx
import { useCallback, useEffect, useState } from "react";
import type { Item } from "./types";
import { openDataset } from "./api";
import { DatasetOpen } from "./components/DatasetOpen";
import { ItemList } from "./components/ItemList";
import { ReviewPane } from "./components/ReviewPane";

export default function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function open(path: string) {
    setError(null);
    try {
      const { items } = await openDataset(path);
      setItems(items);
      setSelectedId(items.length ? items[0].id : null);
    } catch (e: any) {
      setError(String(e.detail ?? e));
    }
  }

  const step = useCallback((delta: number) => {
    setSelectedId((cur) => {
      const idx = items.findIndex((it) => it.id === cur);
      if (idx === -1) return cur;
      const next = Math.min(Math.max(idx + delta, 0), items.length - 1);
      return items[next].id;
    });
  }, [items]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "TEXTAREA" || tag === "INPUT";
      if (e.key === "ArrowLeft" && !typing) step(-1);
      if (e.key === "ArrowRight" && !typing) step(1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step]);

  function markSaved(id: string, mtime: number) {
    setItems((its) => its.map((it) => (it.id === id ? { ...it, has_caption: true, caption_mtime: mtime } : it)));
  }

  const selected = items.find((it) => it.id === selectedId) ?? null;

  return (
    <div className="app" style={{ display: "flex", height: "100vh" }}>
      <aside style={{ width: "16rem", borderRight: "1px solid #ccc", display: "flex", flexDirection: "column" }}>
        <DatasetOpen onOpen={open} />
        {error && <div className="error" role="alert">{error}</div>}
        <ItemList items={items} selectedId={selectedId} onSelect={setSelectedId} />
      </aside>
      <main style={{ flex: 1, padding: "1rem", overflow: "auto" }}>
        {selected
          ? <ReviewPane key={selected.id} item={selected} onSaved={(m) => markSaved(selected.id, m)} />
          : <p>Open a dataset to begin.</p>}
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Run the frontend test suite (no regressions)**

Run: `cd frontend && npm run test`
Expected: PASS (TagChipEditor tests still green).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/DatasetOpen.tsx frontend/src/components/ItemList.tsx
git commit -m "feat: app shell, dataset open, item list, keyboard nav"
```

---

### Task 23: End-to-end manual verification against the real dataset

**Files:** none (verification only)

- [ ] **Step 1: Start the backend**

Run: `cd backend && .venv/Scripts/python -m captionforge`
Expected: server on :8000.

- [ ] **Step 2: Start the frontend (separate shell)**

Run: `cd frontend && npm run dev`
Open http://localhost:5173.

- [ ] **Step 3: Walk the done-criteria checklist (from the spec)**

Verify each, fixing any defect before checking it off:
- [ ] Enter `N:\AiProjects\MasamiAnimaLora`, click Open → 55 items listed (paired marker on each).
- [ ] Select an item → image renders, three sections show (WD14 tags as chips, Qwen/JoyCaption as textareas).
- [ ] Add a tag chip and edit an NL section → Save → no error; the on-disk `.txt` updates in clean canonical form (verify by reopening the file).
- [ ] `← / →` move between items; editing in a textarea does not trigger nav.
- [ ] Add a new section via `+ Add section`, label it, save → header appears in the file.
- [ ] Toggle a section `tags → NL` and back → content converts losslessly.
- [ ] `Edit raw`, type a new `=== Label ===` break, `Structured` → section appears; Save → normalized output matches structured save.
- [ ] Externally edit a caption file on disk (e.g. in an editor) while it is loaded, then Save in the app → 409 surfaces the reload prompt; Reload loads the on-disk version.
- [ ] Open `N:\AiProjects\MasamiAnimaLora\Imported` (unpaired PNGs) → items show unpaired marker; opening one shows the image with empty sections; adding a section and saving creates a new `.txt`.

- [ ] **Step 4: Record the result**

If all pass, the slice meets its done criteria. Note any deferred follow-ups discovered (do not expand scope here).

- [ ] **Step 5: Commit any fixes made during verification**

```bash
git add -A
git commit -m "fix: address issues found in end-to-end verification"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** scan/pairing+unpaired (T9,T12,T22); parser ladder (T6,T7); tokenizer quirks (T3,T6); serializer/normalize+round-trip (T8); REST open/item/parse/save/image (T11–T13); 409 guard + create-on-save (T13); atomic LF writes (T10); chip editor (T17); NL editor (T18); section management incl. raw mode + kind toggle (T19,T20,T21); keyboard nav + dirty/save + 409 reload (T21,T22); non-recursive scan (T9); path confinement (T9,T12); TDD on the captions module + API (T2–T13); one frontend component test (T17). All spec requirements map to a task.
- **Placeholder scan:** no "TBD"/"add error handling"-style placeholders; every code step shows complete, runnable code. The one documented "Known limitation" (NL text containing a `=== … ===` line) is an explicit, accepted scope boundary, not unfinished work.
- **Type consistency:** `Section`/`CaptionDoc` shape identical across backend (`to_dict`/`from_dict`) and frontend `types.ts`; API client method names (`openDataset`,`getItem`,`parseRaw`,`saveSections`,`saveRaw`) match their callers in `ReviewPane`/`App`; `scan_dataset`/`resolve_within`/`atomic_write`/`file_mtime`/`read_text` signatures match their call sites.
```
