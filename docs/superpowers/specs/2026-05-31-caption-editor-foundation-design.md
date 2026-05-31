# CaptionForge — Foundation Slice Design

**Date:** 2026-05-31
**Status:** Approved for planning
**Scope:** First vertical slice of the dataset caption editor, built to keep.

## Purpose

Build the foundation of a standalone local web app for reviewing and editing
image-caption datasets (per `Docs/dataset-caption-editor-design.md`). This slice
delivers the core editing loop — scan, parse, preview, edit, save — on real
data, with clean seams so later subsystems (scoring, autocomplete, bulk ops,
profiles, export, ComfyUI integration) bolt on without reworking it.

This is **not** throwaway. It is the real codebase's first layer.

## Context

- Reference dataset: `N:\AiProjects\MasamiAnimaLora` — 55 captioned `.png`/`.txt`
  pairs in the root; a subfolder `Imported/` holds 52 uncaptioned `.png` files.
- Trigger keyword for this dataset: `Masami`.
- Caption files use labeled sections written by ComfyUI's `CaptionSaver`. Real
  labels and order observed:

  ```text
  === WD14-Tags ===
  Masami,1girl, solo, long hair, ..., black fur,

  === Qwen-VL ===
  Natural-language caption...

  === JoyCaption2 ===
  Natural-language caption...
  ```

- Observed real-world quirks the parser must survive:
  - First tag jammed onto the trigger with no space: `Masami,1girl`.
  - Trailing comma at end of the tag line.
  - Natural-language sections contain commas (so global comma-splitting is
    wrong — only the designated tag section is comma-tokenized).

### Decisions carried in from brainstorming

- **Caption format is a function of the target base model** (Pony = tags-only,
  NL-only models = prose, Anima = TBD/hybrid). This slice does not implement
  base-model profiles, but keeps parser output **profile-agnostic** so a profile
  layer can drive scoring/compose later.
- **Section breaks are an editor construct.** The multi-section `.txt` is review
  *source material*; the flat caption a LoRA trainer consumes is a separate
  artifact produced by a later export/compose step. This slice does not build
  export; it preserves the multi-section format on save.
- The **source-vs-training-caption storage decision is deferred** (decide after
  this slice, once real messy datasets and Anima's format are understood). The
  parser and review UI are identical regardless of how that resolves.
- **Scoring will be profile-relative** when it lands (a tags-only dataset must
  not be flagged for "missing natural-language section"). Out of scope here, but
  noted so no universal scoring rules get baked into the core.

## Goals (this slice)

- Open a dataset directory by path and list image/caption pairs, including
  unpaired images.
- Preview the image and edit its caption.
- Parse the labeled-section format robustly, degrading gracefully when sections
  are absent or malformed.
- Edit natural-language sections as text and the tag section as structured chips.
- Let the user **manage section breaks**: add, label, re-kind, reorder, and
  remove sections (structured controls), plus a raw-text escape hatch.
- Save safely: atomic writes, lossless canonical re-serialization, and
  protection against overwriting external changes.

## Non-Goals (this slice)

- Danbooru tag autocomplete and the tag database.
- Deterministic or AI scoring; filters; review status / metadata sidecar.
- Bulk tag operations.
- Base-model profiles and the export/compose step.
- ComfyUI API integration.
- Recursive directory scanning.

## Stack

- **Backend:** Python + FastAPI.
- **Frontend:** React + Vite (TypeScript).
- **Storage:** direct caption file reads/writes. No database in this slice.

Rationale: Python aligns with the ComfyUI ecosystem (future integration,
image/filesystem/SQLite work) and is the natural home for the canonical caption
parser. React/Vite suits a keyboard-first editor with chip editing and (later)
autocomplete and virtualized lists.

## Architecture

```text
CaptionForge/
  backend/
    captions/      canonical caption model: parser + serializer (pure, tested)
    api/           FastAPI routes + image serving
  frontend/        React + Vite — a view over JSON; never parses caption text
  docs/
```

**Single source of truth for the caption format is the Python `captions`
module.** The frontend exchanges structured JSON (sections) with the backend and
never parses raw caption text itself. The one exception — raw-text edit mode —
still round-trips through the backend parser, so the browser never owns format
logic.

### Components and responsibilities

- **`captions` module (backend, pure).**
  - *What it does:* parse caption text → `CaptionDoc`; serialize `CaptionDoc` →
    canonical text; tokenize/join tags; infer section kind.
  - *Interface:* `parse(text) -> CaptionDoc`, `serialize(doc) -> str`, plus the
    `CaptionDoc`/`Section` data types.
  - *Depends on:* nothing outside the standard library. No filesystem, no web.
- **`api` module (backend).**
  - *What it does:* dataset scan/pairing, image serving, item read/write,
    atomic writes, external-change detection, path confinement.
  - *Interface:* the REST endpoints below.
  - *Depends on:* `captions`, filesystem.
- **Frontend.**
  - *What it does:* dataset open screen, item list, review pane (image + section
    editors + section management + raw mode), keyboard nav, dirty/save state.
  - *Interface:* the REST API.
  - *Depends on:* the REST API only.

## Caption Model

```python
CaptionDoc(sections: list[Section])

Section(
  label: str | None,                 # e.g. "WD14-Tags"; None for a headerless section
  kind: "tags" | "natural_language",
  tags: list[str],                   # populated when kind == "tags"
  text: str,                         # populated when kind == "natural_language"
)
```

JSON shape exchanged with the frontend:

```json
{
  "sections": [
    { "label": "WD14-Tags", "kind": "tags", "tags": ["Masami", "1girl", "solo"] },
    { "label": "Qwen-VL", "kind": "natural_language", "text": "..." },
    { "label": "JoyCaption2", "kind": "natural_language", "text": "..." }
  ]
}
```

## Parser

Graceful-degradation ladder:

1. **Find headers.** Match section headers with `^===\s*(.+?)\s*===\s*$`
   (multiline). The body of a section is the text between its header and the
   next header (or end of file).
2. **Classify kind by loose label match** (case-insensitive substring):
   - contains `wd14` or `tag` → `tags`
   - contains `qwen`, `joycaption`, or `caption` → `natural_language`
   - otherwise → infer by content (step 4 heuristic); default `natural_language`.
   Section order is never assumed.
3. **No headers found** → the whole file is a single section with `label = None`,
   kind inferred by content. Handles a flat tag line or a flat prose blob.
4. **Content-kind heuristic** (used when label is absent or unrecognized): treat
   a body as `tags` when it is predominantly short, comma-separated fragments
   (high comma-to-token ratio, short tokens, few sentence-ending punctuation
   marks); otherwise `natural_language`.
5. **Empty file** → `CaptionDoc(sections=[])`.
6. **Unknown labels** → preserved as sections with their label; kind defaults to
   `natural_language` unless the content heuristic clearly says tags.

**Tag tokenizer:** split the body on commas, `strip()` each token, drop empties.
This recovers `Masami,1girl` as two tags and removes the trailing-comma phantom.
No special-casing.

**No automatic dedup.** The parser preserves duplicate tags so the UI can show
them. Removing duplicates is an explicit user action. The parser never silently
drops content.

## Serializer

Full re-serialization (normalize) from the model, matching `CaptionSaver`'s
layout so files stay drop-in compatible with the ComfyUI workflow:

```text
=== {label} ===
{tags joined with ", "   OR   text.strip()}
                              <- one blank line between sections
```

- A section with `label = None` (headerless single-section file) emits its
  content with no header line.
- Tags serialize as `", ".join(tags)`.
- Encoding UTF-8; newlines LF (matches ComfyUI's Python writes).

**Round-trip invariant (tested):** `parse → serialize → parse` is stable —
serializing an already-parsed doc and re-parsing yields the same model
(idempotent after the first normalize). Normalization only changes *spacing/
layout*, never tag content or prose text.

## REST API

All paths are validated and confined under the opened dataset root (no
traversal). One dataset is open at a time.

- `POST /api/dataset/open` — body `{ "path": "..." }`.
  - Non-recursive scan of the directory.
  - Supported image extensions: `.png`, `.jpg`, `.jpeg`, `.webp`.
  - Pairs a caption file to each image by stem (`image_001.png` ↔
    `image_001.txt`).
  - Returns `{ "root": "...", "items": [ { "id", "image", "has_caption",
    "caption_mtime" } ] }`. `id` is stable within the session (image filename).
  - Unpaired images are included with `has_caption: false`.
- `GET /api/item/{id}` → `{ "image_url", "sections", "caption_mtime" }`.
  For an unpaired image, `sections` is empty and `caption_mtime` is null.
- `PUT /api/item/{id}` — body is **either** `{ "sections": [...],
  "base_mtime": <number|null> }` **or** `{ "raw": "...", "base_mtime":
  <number|null> }`.
  - `raw` input is parsed, then serialized (so it normalizes identically).
  - Re-serialize → atomic write. If the caption file does not exist yet (unpaired
    image), the write creates it.
  - **External-change guard:** if the file exists and its current mtime differs
    from `base_mtime`, respond `409 Conflict` (the file changed underneath, e.g.
    a ComfyUI rewrite). The client offers to reload. `base_mtime: null` is used
    when creating a caption for a previously unpaired image.
  - On success returns `{ "sections", "caption_mtime" }` (the new mtime).
- `POST /api/parse` — body `{ "raw": "..." }` → `{ "sections": [...] }`.
  Lets the frontend flip raw↔structured live without saving.
- `GET /api/image/{id}` → image bytes with the correct content type.

### Save safety details

- **Atomic write:** write to a temp file in the same directory, flush/fsync,
  then `os.replace` onto the target. No torn files.
- **External-change guard** as above (mtime comparison). Content-hash comparison
  is a noted future hardening, not in this slice.

## Frontend

Single-page app, three regions:

1. **Dataset open** — a path input; on open, loads the index.
2. **Item list** — a simple scrollable list of items (image filename, paired/
   unpaired indicator). Virtualization is deferred. Selecting an item loads it.
3. **Review pane:**
   - Image preview on the left (served via `GET /api/image/{id}`).
   - Sections on the right:
     - **Natural-language sections** render as large, soft-wrapped textareas.
     - **The tag section** renders as a **chip editor**: add a tag via a typed
       input, remove via ✕, reorder, and a `dedupe` button (whitespace
       normalization happens automatically on save, so there is no separate
       normalize button). **No autocomplete in this slice.**
   - **Section management (structured controls):**
     - `+ Add section` — choose a label and kind (`tags` | `natural_language`).
     - Edit a section's label.
     - Toggle a section's kind. Toggling `tags → natural_language` joins tags
       with `", "`; `natural_language → tags` comma-tokenizes the text. Reuses
       the same tokenizer/join logic, reversible.
     - Remove a section; reorder sections.
   - **Raw-text mode** — a toggle that shows the literal caption text. The user
     can type `=== Label ===` breaks directly. Switching back to structured (or
     saving) round-trips through the backend parser (`POST /api/parse` for live
     switching; `PUT {raw}` on save). The browser never parses caption text
     itself.
   - **Save / dirty state** — a Save button enabled when there are unsaved edits.
     On a `409`, prompt to reload the on-disk version.
   - **Keyboard navigation:** `←` / `→` previous/next item, `Ctrl+S` save.
   - **Unpaired images:** open with an empty doc; the user can add sections and
     saving creates the `.txt`.

## Testing

- **`captions` module — TDD, the priority.**
  - Real fixtures extracted from `MasamiAnima` captions: the 3-section format,
    the `Masami,1girl` jammed trigger, the trailing comma, commas inside prose.
  - Synthetic edges: headerless tags-only, headerless prose-only, empty file,
    unknown labels, duplicate tags, mixed/garbage preserved verbatim.
  - Round-trip idempotence as a property: `parse → serialize → parse` stable.
  - Kind toggle/tokenizer reversibility.
- **`api` module:** tests over a temporary dataset directory — scan/pairing,
  unpaired image listing, item read, save (sections and raw), atomic write,
  the stale-`mtime` `409` path, path-traversal rejection, create-on-save.
- **Frontend:** light — one component test for the chip editor (add/remove/
  dedupe). Manual verification covers the rest in this slice.

## Seams Left Open (designed-for, not built)

Each future subsystem consumes the same caption model as a separate unit; none
requires reworking the parser:

- Base-model profiles → drive scoring, compose, tag style.
- Profile-relative scoring → reads `CaptionDoc`, returns issues.
- Metadata / review-status sidecar (`.caption-editor/index.json`) → a parallel
  store keyed by item `id`.
- Danbooru autocomplete + tag DB (SQLite, imported from ComfyUI's tag CSV).
- Bulk tag operations with preview + backups.
- Export/compose → a separate consumer that flattens sections into a
  profile-shaped training caption.
- ComfyUI integration → recaption/critique jobs.

## Done Criteria

Point the app at `N:\AiProjects\MasamiAnimaLora`, see all 55 pairs listed, click
through items, edit a tag (chip) and a natural-language section, add a new
section break, save, and confirm the on-disk `.txt` is updated in clean
canonical form. Editing in raw mode and saving produces the same normalized
result. Saving over a file that changed externally is rejected with a reload
prompt. Opening an unpaired image and saving creates a new `.txt`.

## Build Sequence

1. `captions` module — model, parser, serializer, tokenizer (TDD).
2. FastAPI app skeleton + path confinement + image serving.
3. `dataset/open` scan + pairing (incl. unpaired).
4. `item` read + `parse` endpoint.
5. `item` save (sections + raw) with atomic write and `409` guard.
6. React/Vite skeleton; dataset open + item list.
7. Review pane: image + NL textareas + tag chip editor.
8. Section management (add/label/kind-toggle/remove/reorder) + raw-text mode.
9. Keyboard nav, dirty/save state, `409` reload flow.
10. Frontend chip-editor component test; manual end-to-end against the real
    dataset.
