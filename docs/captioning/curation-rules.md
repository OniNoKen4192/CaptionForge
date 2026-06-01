# Dataset Curation Rules (CaptionForge spec)

The **actionable** layer. Where the per-model docs explain *why*, this doc says *what the
editor enforces* — the rules CaptionForge's project profiles, normalization pass, tag
validation, scoring, and final-caption composer implement directly.

> **In scope:** anything that lives in a caption file or is a dataset-level property —
> caption style, format/normalization, tag vocabulary, special-tag systems, length,
> trigger placement, what to caption vs omit.
>
> **Out of scope (training, not curation):** learning rate, step count, optimizer,
> rank/alpha, VRAM/quantization, "train on Full only," `llm_adapter_lr`, `keep_tokens` /
> `shuffle_caption`, NaN quirks. These belong to the *trainer*, not this tool. A few are
> worth carrying as **profile metadata** (a non-enforced note shown to the user) — flagged
> as `[meta]` below — but CaptionForge never sets them.

The editor's sections: **JoyCaption** + **Qwen-VL** (natural language) and **WD14 Tags**
(Danbooru). "Compose" = assembling the final training caption from these per the model's mode.

---

## The four jobs

1. **Normalize** — underscore/space style, separator, special syntax (`@artist`, paren
   escaping), trigger form. Deterministic cleanup.
2. **Validate** — is each tag real in the model's vocabulary (Danbooru / Gelbooru-spelling /
   e621 / none)? Flag unknowns, deprecated, aliases.
3. **Score** — model-aware review-priority signal: length within bounds, banned hedging
   phrases, required trigger present, identity-trait warnings (character), special-tag misuse.
4. **Compose** — emit the final caption in the model's mode and order.

---

## Master matrix

| Model | Mode | Primary section(s) | Tag vocab to validate | Underscores | Length (curation) |
|---|---|---|---|---|---|
| SD 1.5 | Tags | WD14 | Danbooru | →spaces optional, be consistent | short, ~5–15 tags |
| SDXL | Hybrid | WD14 + short NL phrase | Danbooru | →spaces optional | ~75 tok |
| Pony V6 | Tags + special | WD14 | Danbooru (**artist tags ineffective**) | tolerated, be consistent | tag list |
| Illustrious / NoobAI | Tags | WD14 | **Danbooru** (verify on site) | interchangeable, pick one | tag list |
| Flux | Prose | JoyCaption / Qwen | none (tags optional, CLIP-L only) | n/a | long OK |
| SD 3.5 | Prose (bounded) | JoyCaption / Qwen | none | n/a | **cap < 256 T5 tok** |
| Chroma | Flexible | both (mode switch) | Danbooru / **e621 ok** | depends on mode | flexible |
| Anima | Hybrid (native) | both | Danbooru, **prefer Gelbooru spelling** | **spaces, NOT underscores** (except `score_X`) | flexible |
| Qwen-Image | Prose | JoyCaption / Qwen | none (**raw tags → tag bleed**) | embed as plain English | ~15–40 words |
| HiDream-I1 | Prose | JoyCaption / Qwen | none (embed attrs in prose) | embed as plain English | ~128 tok |
| Lumina 2.0 (Neta) | Tags **or** prose (pick one) | both (mode switch) | Danbooru (Neta) | per chosen mode | flexible |
| Sana | Prose only | JoyCaption / Qwen | none | n/a | **min-length guard** (short = bad) |

Separator is `, ` everywhere tags are used.

---

## Per-model rules

Grouped by profile family. Only the curation-actionable deltas; see the linked doc for rationale.

### Booru-tag models — SD1.5, SDXL, Illustrious/NoobAI
[sd15.md](sd15.md) · [sdxl.md](sdxl.md) · [illustrious-noobai.md](illustrious-noobai.md)

- **Validate** every tag against the Danbooru DB; flag non-Danbooru tags as **ineffective**
  (not just "generic"), surface aliases/deprecated.
- **Normalize** one underscore/space style across the whole dataset (Illustrious/NoobAI:
  interchangeable, just consistent; kohya `--remove_underscore` convention = spaces).
- **Compose:** `trigger` first → variable content tags. SDXL may interleave one short NL
  framing phrase (`full body shot`, `from above`) from the NL section.
- **Quality/aesthetic/year tags** (Illustrious/NoobAI: `masterpiece`…`worst quality`,
  `very awa`, `newest`…): **training-optional.** Inject **only if dataset quality varies**;
  on a uniform-quality set they're constant noise → **score-flag** if present on every file.
  These are an *inference* prefix, composed separately from the training caption.
- **Artist tags** (Illustrious/NoobAI): bare tag, no `artist:` prefix. Character profile →
  tag the artist (factors style out of the trigger) or omit; never required.

### Pony V6 — [pony.md](pony.md)
- **Validate** against Danbooru, **but flag artist-name tags as INEFFECTIVE on Pony** (the
  model stripped them) — distinct warning from the anime forks.
- **Special tags:** score chain `score_9, score_8_up, score_7_up` (underscored), `rating_*`,
  `source_*`.
- **Score chain is training-optional and contested** → default **off** for the caption body,
  exposed as a toggle; if on, it's a fixed prefix. **Score-flag any low-quality image tagged
  `score_9`.** (Inference prefix is separate.)
- **Compose:** `[optional score chain] → trigger → [optional rating_/source_] → structural
  (1girl/anthro) → variable tags`.

### T5 prose — Flux, SD3.5
[flux.md](flux.md) · [sd35.md](sd35.md)
- **No tag validation** — prose only. The WD14 section may be concatenated to feed CLIP-L
  (optional), otherwise dropped.
- **Trigger is EMBEDDED in a phrase** ("a photo of a woman named `TRIGGER`"), not a leading
  token. Compose accordingly; validate the trigger phrase is present.
- **Score:** banned hedging phrases (`appears to`, `seems`, `possibly`) in the NL section —
  VLM output is full of them and they pollute training.
- **SD3.5 length is model-aware:** the "caption too long" check must cap at **< 256 T5
  tokens** (this is the concrete case where the length score is per-model, not global).
- `[trigger]` placeholder vs literal: `[meta]` — depends on trainer (ai-toolkit substitutes;
  others bake literal). Composer should support both, default to literal.

### LLM-prose — Qwen-Image, HiDream
[qwen-image.md](qwen-image.md) · [hidream.md](hidream.md)
- **Prose primary; trigger is a leading token** (unlike Flux/SD3.5's embedded phrase).
- **Do NOT append raw booru tags** — causes tag bleed (Qwen) / under-uses encoders (HiDream).
  For anime, **convert WD14 tags to plain-English attributes embedded in the sentence**
  (`twin tails`, `school uniform` — not `twintails`, `looking_at_viewer`). This is a real
  normalization job: underscore-strip + fold into prose, don't concatenate.
- **No quality-tag system** — strip any `masterpiece`/`score_*` imported from other profiles.
- **Score:** hedging-phrase check; Qwen length ~15–40 words; HiDream cap ~128 tokens.
- `[meta]`: Qwen — bake literal trigger when trainer caches embeddings; HiDream — "train on
  Full only," frozen TEs (notes only, not enforced).

### Booru-trained flexible — Chroma, Anima
[chroma.md](chroma.md) · [anima.md](anima.md)
- **Mode switch by dataset domain:** anime/furry → tags; photoreal → prose; mixed available.
  This is where the multi-section design pays off — the composer reads both sections.
- **Chroma:** validate booru tags against Danbooru **and e621**; trigger = leading tag (tag
  mode) or embedded (prose mode); length flexible.
- **Anima** (most normalization-heavy profile):
  - **Spaces, not underscores** in tags — **except `score_X`** (keep underscores). Normalize.
  - **`@` prefix on artist tags.**
  - **Prefer Gelbooru spelling** when the tag DB has both Danbooru and Gelbooru forms —
    validation note.
  - **Special prefix:** quality ladder + `score_1..9` + safety (`safe/sensitive/nsfw/
    explicit`) + year — training-optional; **omit `year` from training captions** (ties to
    era-style), inference-only.
  - **Compose order:** `quality/score/safety prefix → trigger → NL sentences → variable
    tags`. `[meta]`: warn that `keep_tokens` won't protect the trigger in this layout.

### Gemma lightweight — Lumina 2.0, Sana — [lumina-sana.md](lumina-sana.md)
- **Lumina (Neta):** tags **or** prose, **pick one — don't blend** (score-flag mixed
  captions). Validate Danbooru when in tag mode. **Must prepend the `<Prompt Start>` system
  prefix** (`You are an assistant designed to generate anime images… <Prompt Start>`) —
  composer prepends it; support `@artist` / `#character` syntax + paren escaping. Quality
  tags valid (Neta trained them). Trigger leads after the prefix.
- **Sana:** prose only, drop the tag section. Trigger embedded. **Minimum-length guard** —
  short captions are actively harmful, so score-flag *too short* (inverse of the usual
  too-long check). No quality tags.

---

## Cross-cutting: what to caption vs omit (character LoRAs)

CaptionForge's primary user trains **character** LoRAs, so the omit/keep guidance is
character-shaped by default (see [[trains-character-loras]] in project context):

- **Omit invariant identity traits** (hair color, eye color, face, signature features) so the
  trigger absorbs them. Score-flag a caption that tags the character's *constant* traits — it
  splits them off the trigger.
- **Caption the variables** (pose, expression, outfit, background, lighting, framing) so
  they're decoupled and promptable.
- **Exception to surface, not enforce:** some workflows deliberately *keep* identity traits as
  tags for override flexibility (the Chroma/Lumina examples do this). So this is a **warning**
  with a per-profile toggle, not a hard error.
- Style-LoRA guidance (caption everything, omit the style) is **de-prioritized** for this user —
  available in the per-model docs if needed, not a default scoring path.

---

## Implementation hooks (maps to the editor design)

| Curation job | CaptionForge feature it drives |
|---|---|
| Normalize | underscore/space toggle, separator, `@artist`/`<Prompt Start>` handling, trigger form |
| Validate | Danbooru/Gelbooru/e621 tag DB; non-vocab + deprecated + alias flags; Pony artist-ineffective flag |
| Score | model-aware length bounds (incl. SD3.5 cap, Sana min); hedging-phrase check; identity-trait warning; special-tag-misuse flags |
| Compose | per-model mode + order; special-tag prefix (training vs inference split); trigger placement (lead-tag vs embedded vs literal-`[trigger]`) |
| Profile metadata `[meta]` | non-enforced training notes (Full-only, frozen TE, keep_tokens caveat, llm_adapter) shown for context |

These are the per-model **project profiles**: each profile is a row's worth of normalize +
validate + score + compose settings, plus the `[meta]` notes.
