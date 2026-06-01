# Captioning for SDXL (base) LoRAs

> Read [00-principles.md](00-principles.md) first. This covers **vanilla SDXL base**.
> The anime forks have their own docs: [pony.md](pony.md),
> [illustrious-noobai.md](illustrious-noobai.md).

## TL;DR

**Hybrid: tag-like, with light natural phrasing.** SDXL has *two* text encoders —
the weak CLIP-L (same as SD1.5) plus the much stronger OpenCLIP-G. They both see the
**same caption string**, so your caption has to serve a prose-loving encoder and a
tag-loving one at once. The safe answer: comma-segmented captions with natural-ish
phrasing and composition cues, not flowery paragraphs and not pure tag soup.

## 1. Caption style — and why it's contested

- **Dual encoders: CLIP-L + OpenCLIP-G (ViT-bigG/14)**, penultimate outputs
  concatenated. CLIP-G is meaningfully better at full sentences; CLIP-L still prefers
  tags.
- **The tension:** standard kohya/OneTrainer training feeds *one* caption string to
  *both* encoders — you can't natively send different text to each (open feature
  request, kohya-ss/sd-scripts #781, #938). So one caption must satisfy both.
- **Practical consensus: hybrid.** Natural-ish phrasing for scene/composition, still
  comma-delimited and tag-like. Civitai's trainer still lists *tag-based* as preferred
  (a natural-language warning there is informational — ignore it). Add framing cues
  SDXL handles well: `portrait`, `full body shot`, `close-up`, `from above`.

## 2. Caption format & ordering

- Separator: comma + space. Order matters (earlier = more weight).
- Trigger **first**, in every file. Then variable attributes → clothing →
  pose/expression → background → **framing/composition** → style.
- **Token mechanics matter more here** because people write longer SDXL captions.
  Each encoder gets 75 usable tokens; modern trainers chunk (75/150/225) and keep
  weight-groups intact. Going slightly over 75 is fine on OneTrainer/recent kohya —
  one report had longer *untruncated* captions training better than truncated on a
  1,400-image set. Don't rely on it.

## 3. Trigger word handling

- Rare/unique token at the front; `keep_tokens = 1`. Class token only with
  regularization images.
- **SDXL augmentation gotcha:** historically kohya's SDXL pipeline did **not** support
  `shuffle_caption`, `caption_dropout_rate`, `caption_tag_dropout_rate`, or
  `token_warmup` (tied to text-encoder output caching). This has been changing —
  **verify on your installed build** before relying on shuffle/dropout for SDXL. If
  you cache TE outputs, per-step shuffle/dropout is logically incompatible.

## 4. Length & detail

Apply omit-to-bake-in (principles). Character: short, trigger + variables. Style:
caption the content densely, never the style. Stay near 75 tokens unless your trainer
chunks and you have a reason to go longer.

## 5. Do / Don't

**Do**
- Hybrid captions — comma-segmented, natural-ish, with composition tags
  (`full body`, `close-up`, `from above`).
- Trigger first, identical form everywhere; `keep_tokens = 1`.
- Caption the variables; omit identity traits.

**Don't**
- Don't write pure prose paragraphs — CLIP-L still sees the same string and prefers
  tags; prose-only is contested and can hurt.
- Don't dump bare tag soup either — you waste CLIP-G's strength.
- Don't enable shuffle/dropout for SDXL and assume it ran — check your build.

## 6. Worked example

Same "Mara" character (silver hair + scar = identity), token `m4ra`. Image: full-body,
neon alley at night, arms crossed, smirking, leather jacket.

```
m4ra, a full body shot of a woman standing in a neon-lit alley at night, arms crossed, smirking, wearing a black leather jacket
```

- `m4ra` first; `full body shot` is a framing cue CLIP-G/SDXL handle well.
- Silver hair + scar **omitted** → baked into the trigger.
- Jacket, pose, expression, setting **captioned** → controllable.
- Light prose, but comma-segmented so CLIP-L still parses it and chunking keeps groups
  intact.

## 7. How it maps to CaptionForge sections

- Primary: **WD14 Tags**, lightly fused with a short phrase from **JoyCaption/Qwen-VL**
  for composition — this is the hybrid sweet spot.
- A good SDXL composer: trigger + a one-line natural framing phrase + the cleaned WD14
  tags. Don't paste a full JoyCaption paragraph in.
- This is the cleanest place in the editor to offer a "hybrid" final-caption mode that
  draws from *both* the tag and NL sections.

## Contested / moving

- **Tags vs natural language for SDXL is the live debate** — no settled winner;
  depends on concept and how you'll prompt.
- Whether to caption a person set heavily at all.
- Which augmentation params your SDXL trainer build actually supports.

## Sources

SDXL paper (arxiv 2307.01952, dual encoder); kohya-ss/sd-scripts #781/#938 (separate
TE captions); OneTrainer #740 (75+ token support); Civitai education (on-site trainer);
Civitai article 7203 (captions vs no-captions); kohya_ss wiki.
