# Captioning for Pony Diffusion V6 XL LoRAs

> Read [00-principles.md](00-principles.md) first. Pony is SDXL-based but its
> score/rating/source tag dialect is unique — don't reuse vanilla SDXL or
> Illustrious recipes here.

## TL;DR

**Danbooru-style tags, plus Pony's special vocabulary: the `score_*` chain,
`rating_*`, and `source_*` tags.** Caption in comma tags. The famous score chain is
mainly a *prompting* convention; whether to put it in *training* captions is
genuinely contested (see §8). Artist-name tags **don't work** — Pony stripped them.

## 1. The score-tag system

- Tags: `score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up`.
  `score_9` = top tier; each `_up` means "this threshold and above."
- **What they actually are:** machine-applied aesthetic labels. AstraliteHeart trained
  an aesthetic-ranking model on ~20,000 human-rated images, then auto-labeled all
  ~2.6M training images. They are **not** Danbooru/e621 upvote scores — that common
  claim is imprecise.
- **Why the verbose `_up` chain exists:** it's an acknowledged **training artifact**.
  The model card says the longer form "is a training issue that was too late to correct
  during training." Consequence: **bare `score_9` is weak** — you need the stacked
  chain to get the quality signal.
- **Recommended prompting prefix (from the card):**
  `score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up, <your prompt>`.
  Community shorthand uses just the top three: `score_9, score_8_up, score_7_up`.
- Weak as negatives — the scale floors at 4 (little training below it).

## 2. Rating & source tags

- **Rating:** `rating_safe`, `rating_questionable`, `rating_explicit`. Dataset was
  balanced ~1:1:1, so these are strong steering levers.
- **Source:** `source_pony`, `source_furry`, `source_cartoon`, `source_anime`
  (~1:1:1:1). `source_anime` → 2D anime aesthetic, etc.
- In training: include a `rating_*` (and a `source_*` if your set is domain-uniform)
  **only if it's a real, consistent property** you want to keep controllable. If you
  omit them, the base model's behavior still applies at inference — they're far less
  load-bearing than the trigger.

## 3. Caption style

- Comma-separated **Danbooru tags** is the dominant LoRA practice. Pony *does*
  understand natural language (~50% of its data was NL-captioned), but tags give
  crisper control for character/style LoRAs.
- Separator: comma + space. Underscores vs spaces both tolerated — pick one, be
  consistent.
- **Ordering, front to back:**
  1. *(optional)* score chain
  2. **trigger word**
  3. *(optional)* `rating_*` / `source_*`
  4. structural tags (`1girl`, `anthro`, `solo`)
  5. variable content tags (pose, expression, background, clothing, lighting)

  Rule: anything you want pinned goes up front and is protected by `keep_tokens`.

## 4. Trigger word handling

- Unique/rare token at the front. If you front-load the 3-tag score chain *before* the
  trigger and want it all kept, your protected region is 4 tokens → `keep_tokens = 4`.
  Trigger-only front → `keep_tokens = 1`. **Decide where the score tags live and set
  `keep_tokens` to cover everything before the shufflable content.**
- `shuffle_caption = on` is standard. Keep the front-token *count* identical across the
  dataset or `keep_tokens` breaks.

## 5. Length & detail

Omit-to-bake-in (principles). Character: caption background/expression/pose/clothing/
framing; omit invariant identity traits. Style: don't over-tag — and this is where
*excluding* the score chain is most often recommended (see §8).

## 6. Do / Don't

**Do**
- Use the **stacked** score chain, not bare `score_9`, when you use it at all.
- Trigger first, protected by `keep_tokens`.
- Pick rating/source deliberately if your dataset is uniform.

**Don't**
- **Don't rely on artist-name tags** — Pony stripped them from training. (This is *why*
  artist-style LoRAs are so popular for Pony.)
- **Don't label a low-quality image `score_9`** — it destabilizes the LoRA. If you
  caption scores, they must honestly reflect quality.
- Don't forget the score chain at *inference* even if you trained without it — without
  it Pony assumes you want low-quality output.

## 7. Worked example

OC "Aurelia" — blue-haired anthro fox girl. Image: sitting in a cafe, smiling, hoodie.

```
score_9, score_8_up, score_7_up, aurelia_fox, source_furry, rating_safe, anthro, solo, sitting, smile, hoodie, cafe background, looking at viewer, indoors
```

- Score chain: **optional** (the contested part). If kept on a clean set, it's in the
  protected front → `keep_tokens = 4`. Without it, trigger is first → `keep_tokens = 1`.
- `aurelia_fox` = trigger. `source_furry, rating_safe` = optional steering.
- Variables (`sitting, smile, hoodie, cafe background, ...`) captioned.
- **Omitted:** `blue hair, fox ears, fox tail, orange fur` — Aurelia's invariant
  features, baked into the trigger.

## 8. Contested / moving — score tags in *training*

The central disagreement, with both documented camps:

- **Include** (e.g. Apatero guide): score tags teach the LoRA which quality level to
  target; without them quality is "unpredictable."
- **Exclude** (e.g. DCAI character guide): score tags carry the source images' *style
  bias* into the LoRA — *"the image style of the original becomes too strong."* Add them
  only at generation time.
- **The author's own hedge** leans cautious: the score tags "have some bias… for
  style/artist LoRAs it sometimes makes sense to exclude the tags."

**Defensible synthesis:** style/artist LoRAs → lean *omit* (bias contamination is the
bigger risk). Character LoRAs on a clean set → a flat high chain is fine and gives a
quality handle, but it's optional — A/B test. Universal: **never tag a bad image
`score_9`.**

Other unsettled points: top-3 vs full-6 chain; natural language vs tags for Pony LoRAs.

## 9. How it maps to CaptionForge sections

- Primary: **WD14 Tags**. The Pony composer prepends an *optional* score chain +
  trigger + optional rating/source, then the cleaned tags.
- This screams **project profile**: a "Pony" profile should let you toggle the score
  chain on/off (default off for style, optional for character), set the rating/source,
  and own the `keep_tokens` math for the chosen prefix length.
- The editor's banned-tag/scoring checks should flag artist-name tags as **ineffective
  on Pony**, not just generic.

## Sources

Pony V6 XL model card (Civitai 257749; CivArchive + LyliaEngine HF mirrors agree);
Civitai 4248 (score_9 derivation, ~20k ratings); DCAI character LoRA guide
(omit camp); Apatero training guide (include camp); Diamond on-site settings guide
(keep_tokens/shuffle, low-quality warning).
