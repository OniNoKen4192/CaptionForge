# Dataset Caption Editor Design

## Decision

Build a standalone local web app for dataset review/editing, with ComfyUI used as
the caption-generation backend where needed.

The existing ComfyUI workflow is already well suited for batch generation:

- `BatchImageLoader` walks an image directory.
- Qwen-VL, JoyCaption2, and WD14 generate captions/tags.
- `CaptionSaver` writes sidecar `<image_stem>.txt` files.
- The bundled web extension auto-requeues until the directory is complete.

The editor requirements are different. Bulk tag operations, Danbooru
autocomplete, long natural-language editing, filtering, scoring, review status,
and keyboard-first navigation all want an application-shaped UI, persistent
dataset state, and richer file APIs than a ComfyUI node graph naturally provides.

ComfyUI should remain responsible for expensive image/caption generation. The
dataset editor should be responsible for human review, cleanup, scoring, and
pre-training readiness.

## Goals

- Review a directory of image files and matching caption text files efficiently.
- Support both Danbooru-style comma tags and natural-language captions.
- Make bulk caption/tag cleanup safe and reversible.
- Provide fast local Danbooru tag autocomplete.
- Score captions to prioritize review before LoRA training.
- Integrate with existing ComfyUI caption workflows without requiring the editor
  itself to live inside the ComfyUI graph.

## Non-Goals

- Replace ComfyUI generation workflows.
- Train LoRAs directly.
- Depend on live Danbooru API calls for normal editing.
- Use AI scoring as the only quality signal.
- Force all captions into a single caption style.

## Existing Input Format

The current `CaptionSaver` writes labeled sections:

```text
=== JoyCaption ===
Natural language caption...

=== Qwen-VL ===
Natural language caption...

=== WD14 Tags ===
tag one, tag two, tag three
```

The editor should parse this format into sections, preserve unknown sections, and
write the same format back unless the user chooses an exported training-caption
format.

## Recommended Architecture

```text
Local Dataset Caption Editor
  Frontend
    - image viewer
    - section-aware caption editor
    - tag editor/autocomplete
    - bulk operation UI
    - scoring/filter views

  Backend
    - filesystem access
    - image/caption pairing
    - caption parsing/serialization
    - Danbooru tag database
    - deterministic scoring
    - optional ComfyUI API integration

ComfyUI
  - existing Batch-Caption workflow
  - optional selected-file recaption jobs
  - optional image-aware AI critique jobs
```

Preferred implementation:

- Python backend: FastAPI or Flask.
- Frontend: React/Vite or a simple framework-light TypeScript app.
- Local storage: JSON sidecar index plus direct caption file writes.
- Tag database: local SQLite or compact JSON/CSV-derived index.

The app can still be launched from inside this repo and point at the same dataset
directories ComfyUI uses.

## Why Not Build This Primarily Inside ComfyUI?

ComfyUI is strong at graph execution and image-processing workflows. This editor
needs application behaviors:

- editable long-form text areas with save state,
- keyboard navigation,
- multi-select file operations,
- filtering and sorting,
- tag autocomplete,
- status metadata,
- undoable bulk edits,
- scoring dashboards.

Those can be added as a ComfyUI web extension, but then the extension must also
provide backend routes, dataset state, file browsing, image serving, and a custom
UI shell. At that point it is effectively a standalone app embedded in ComfyUI.

Embedding later is reasonable. Starting standalone keeps the editor easier to
develop, test, and use independently from a running ComfyUI server.

## Core Workflows

### Open Dataset

User selects or enters a dataset directory.

The backend scans for supported image extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

For each image, the backend pairs a caption file by stem:

```text
image_001.png
image_001.txt
```

The scan produces a dataset index with:

- image path,
- caption path,
- parsed caption sections,
- file modified timestamps,
- review status,
- score,
- warnings.

### Review Single Item

The editor shows:

- large image preview,
- caption sections,
- final training caption preview,
- score and warnings,
- previous/next controls,
- save state,
- status controls.

Keyboard shortcuts:

- previous item,
- next item,
- save,
- mark reviewed,
- reject,
- focus tag editor,
- focus natural-language editor.

### Edit Tags

The WD14/Danbooru section is treated as a structured tag list.

Required operations:

- add tag,
- remove tag,
- reorder tag,
- deduplicate,
- normalize whitespace,
- convert underscores/spaces according to user preference,
- validate against Danbooru tag database,
- show aliases/deprecated tags,
- autocomplete tags while typing.

### Bulk Tag Operations

Bulk operations apply to selected files or filtered result sets.

Required operations:

- add one or more tags,
- remove one or more tags,
- replace tag,
- apply aliases,
- remove unknown tags,
- deduplicate all selected captions,
- ensure trigger keyword exists,
- remove banned/generic tags from selected files.

Bulk edits should create a change preview before writing:

```text
37 files selected
Add: masami, dragon girl
Remove: artist name, signature
Changed files: 34
Unchanged files: 3
```

The first version can use timestamped backup files or a dataset-level change log
instead of full undo.

### Edit Natural Language Captions

Natural-language sections need a large editor optimized for long strings.

Required features:

- soft wrap,
- large textarea/editor,
- section tabs or stacked sections,
- find within caption,
- preserve paragraphs,
- save without changing tag section order,
- warning highlights for banned phrases.

Useful later:

- sentence splitting,
- side-by-side JoyCaption/Qwen comparison,
- final caption composer,
- diff against generated caption,
- find/replace across selected files.

## Caption Sections

Recommended internal model:

```json
{
  "sections": [
    {
      "label": "JoyCaption",
      "kind": "natural_language",
      "text": "..."
    },
    {
      "label": "Qwen-VL",
      "kind": "natural_language",
      "text": "..."
    },
    {
      "label": "WD14 Tags",
      "kind": "tags",
      "tags": ["1girl", "solo", "blue eyes"]
    }
  ]
}
```

Section kind can be inferred from known labels, with manual override available.

Unknown labels should be preserved as natural-language sections by default.

## Danbooru Tag Autocomplete

Use a local tag database for speed and offline reliability.

Minimum fields:

- tag name,
- display name,
- category,
- post count,
- aliases,
- deprecated flag.

Preferred source format:

- imported CSV/JSON files,
- converted once into SQLite or a compact JSON index.

Autocomplete behavior:

- fuzzy prefix search,
- rank by exact prefix first,
- then post count,
- show category and alias target,
- warn before inserting deprecated tags,
- optionally insert with underscores or spaces based on project setting.

Tag categories should be visually distinct but restrained:

- general,
- character,
- copyright,
- artist,
- metadata.

## Caption Scoring

Scoring should be deterministic first. The score is a review-priority signal, not
a guarantee of training quality.

Recommended score:

```text
100 = likely ready
70-99 = probably okay
40-69 = review recommended
0-39 = likely bad or incomplete
```

Initial scoring categories:

```text
Completeness          30
Tag quality           25
Natural-language fit  25
Dataset consistency   20
```

### Completeness Checks

- missing caption file,
- empty caption,
- missing final caption section,
- missing tag section,
- missing natural-language section,
- caption too short,
- caption extremely long.

### Tag Quality Checks

- duplicate tags,
- unknown Danbooru tags,
- deprecated tags,
- unresolved aliases,
- too many generic tags,
- missing trigger keyword,
- missing subject/class tag,
- banned tags,
- inconsistent underscore/space style.

### Natural-Language Checks

- banned hedging phrases:
  - `appears to`
  - `seems`
  - `possibly`
  - `maybe`
  - `as if`
- overly speculative language,
- repeated sentence fragments,
- too many style words if the project wants factual captions,
- missing subject description,
- missing pose/clothing/environment detail.

### Dataset Consistency Checks

- duplicate captions across multiple images,
- near-duplicate captions,
- trigger keyword not used consistently,
- unusually short or long caption compared with dataset median,
- tag frequency outliers,
- files with different section structures.

### Optional AI Scoring

AI scoring can be added later through ComfyUI:

- send selected image and caption to Qwen-VL/JoyCaption-like critique workflow,
- ask whether the caption contradicts visible image content,
- return issues instead of overwriting the caption.

This should be opt-in because it is slower, GPU-dependent, and less explainable
than deterministic checks.

## Review Status

Store review metadata outside the caption files.

Recommended file:

```text
.caption-editor/index.json
```

Per-image metadata:

```json
{
  "image_001.png": {
    "status": "needs_review",
    "score": 82,
    "reviewed_at": null,
    "notes": "",
    "rejected": false
  }
}
```

Statuses:

- `needs_review`
- `reviewed`
- `needs_fix`
- `rejected`
- `ready`

Do not write editor-only metadata into the training caption unless explicitly
exporting.

## ComfyUI Integration

Initial integration can be loose:

- the editor reads captions generated by the existing workflow,
- the user runs ComfyUI generation separately,
- the editor can rescan the directory when generation finishes.

Later integration:

- configure ComfyUI server URL,
- queue the existing `Batch-Caption.json` workflow from the editor,
- recaption selected files,
- open the current image in a ComfyUI workflow,
- run optional AI critique jobs,
- show ComfyUI job progress.

The existing `BatchImageLoader` is directory-oriented, so selected-file
recaptioning may require one of:

- a new single-image caption workflow,
- a new node that accepts an explicit file path,
- temporary staging of selected files into a queue directory.

The cleanest future addition is a single-image loader node that emits:

- image,
- filename stem,
- source directory.

That would let the editor queue targeted recaption jobs without disturbing the
batch workflow.

## Safety

Caption edits should be recoverable.

Minimum safety features:

- write files atomically,
- detect external file changes before overwrite,
- create timestamped backups for bulk operations,
- preview bulk edits before applying,
- keep a simple operation log.

Recommended backup layout:

```text
.caption-editor/backups/2026-05-31T153000/
  image_001.txt
  image_002.txt
```

## MVP

The first useful version should include:

- open dataset by path,
- scan image/caption pairs,
- image preview,
- section-aware caption parsing,
- large natural-language editor,
- structured tag editor,
- save/previous/next,
- bulk add/remove tags,
- local Danbooru autocomplete,
- deterministic scoring,
- filter by score/status/warnings,
- backup before bulk edits.

## Later Features

- selected-file recaption through ComfyUI,
- AI critique through ComfyUI,
- final training caption composer,
- export cleaned captions to separate directory,
- duplicate/near-duplicate image detection,
- tag frequency dashboard,
- caption length distribution,
- project profiles for different LoRA styles,
- keyboard shortcut customization,
- embedded ComfyUI panel version if standalone workflow proves awkward.

## Open Questions

- Should final training captions be stored in the same `.txt` file or exported to
  a clean training directory?
- Should the editor preserve the generated multi-section caption file forever, or
  treat it as source material for a separate final caption?
- Which Danbooru tag dump format should be the default import target?
- Should rejected images be moved to a folder or only marked in metadata?
- Should bulk operations apply to all sections or only the designated tag section?

## Proposed Build Sequence

1. Create standalone local app scaffold.
2. Implement dataset scanning and image serving.
3. Implement caption section parser/serializer.
4. Build single-image review UI.
5. Add save/next/previous/status.
6. Add structured tag editor.
7. Add bulk add/remove/replace operations.
8. Add Danbooru tag import and autocomplete.
9. Add deterministic scoring and filters.
10. Add ComfyUI recaption/critique integration.

