# Captioning for Chroma LoRAs

> Read [00-principles.md](00-principles.md) first. Chroma (lodestones / Lodestone Rock)
> is a Flux-Schnell-derived, de-distilled community model — and the **most flexible
> captioning target** of any model in these docs, because it accepts tags *and* prose.

## TL;DR

**Tags, prose, or a mix — match the caption to the concept's domain.** Chroma inherits
Flux's T5-XXL + CLIP-L, but it was trained on a broad, deliberately uncensored dataset
drawn heavily from **Danbooru/e621** sources. So unlike Flux/SD3.5, **booru tags actually
work well.** Anime/furry concept → lean tags; photoreal → lean prose; mix when unsure.
Note: Chroma is a **moving target** — pin your checkpoint.

## 1. Text encoder & what Chroma changed

- **Base: FLUX.1-schnell, de-distilled.** Schnell was timestep-distilled (few-step);
  Chroma removed that so it trains/samples like a normal CFG model. Also pruned 12B → 8.9B
  params.
- **Inherits Flux's T5-XXL + CLIP-L.**
- **Fixed Flux's T5 padding bug:** BFL forgot to mask padding tokens, so the model
  over-attended to `<pad>`. Chroma masks padding except one token → **tighter, cleaner
  prompt adherence than base Flux.** Captions are "heard" more faithfully.
- **Apache-2.0, fully uncensored**, reintroduces anatomical concepts BFL stripped.

## 2. Caption style — the big differentiator

Trained on ~5M images curated from 20M, deliberately broad (anime, furry, artistic,
photographic) and drawing heavily on **Danbooru/e621-style sources**. Consequence —
community consensus: *"Chroma (and by proxy Noob) are trained on e621/danbooru, so using
tags from those sites yields the best results when training with caption tags."*

Workable strategies:
- **Pure booru tags** — great for anime/furry concepts and character LoRAs in that domain.
- **Pure natural-language prose** — great for photoreal concepts; leans on T5.
- **Mixed tags + prose** — increasingly the sweet spot, and exactly what **JoyCaption's
  "Stable Diffusion Prompt" mode** produces ("a mixture of natural language and
  booru-like tags"). JoyCaption also has dedicated danbooru/e621/rule34 tag modes — making
  it the natural captioner for Chroma.

**Match captions to the concept's domain.** No hard length ceiling like SD3.5's 256.

## 3. Trigger word handling

- **Tag caption:** trigger as the **first tag** (booru convention) — Chroma's booru
  training makes leading-tag triggers behave like they do in the SDXL/Pony/NoobAI world.
- **Prose caption:** embed the trigger in a phrase, like Flux.
- ai-toolkit (`[trigger]`), kohya, SimpleTuner, OneTrainer all train Chroma as a
  Flux-family model; trigger handling carries over from Flux.

## 4. Length & detail

Omit-to-bake-in (principles). Style LoRAs in the booru idiom: **tag everything** (style is
the residual). Character/concept: tag only the variables. Length is flexible — terse tag
lists and long prose both work.

## 5. Do / Don't

**Do**
- Use **tags** when your concept lives in the anime/furry/booru domain — this is Chroma's
  standout advantage; don't force prose where tags fit.
- Consider **mixed** tag+prose (JoyCaption SD-prompt mode) for broad coverage.
- Expect cleaner prompt adherence than base Flux (padding fix) — captions matter more, in
  a good way.

**Don't**
- Don't assume a Flux-dev captioning recipe is optimal — Chroma's distribution is broader
  and tag-friendly.
- **Pin your checkpoint.** Chroma trained continuously and forked into **Chroma1-Base /
  Chroma1-HD / Chroma1-Flash**; the original `lodestones/Chroma` repo is deprecated in
  favor of those. Recipes drift between snapshots.
- Note: the official card gives **no captioning guidance** — everything here is
  community-derived, strong but not official.

## 6. Worked example

Anime character LoRA, token `chrname`, tag-leaning (character traits kept promptable here):

```
chrname, 1girl, solo, silver hair, long hair, red eyes, school uniform, standing, outdoors, cherry blossoms, looking at viewer, day, full body
```

- Trigger as **leading tag** (booru convention Chroma understands).
- Identity traits (`silver hair`, `red eyes`) **captioned** because this LoRA wants them
  prompt-able. Omit them only if invariant and you want them auto-baked.
- Outfit/pose/setting tagged → flexible.

Same image, **prose-leaning** (if photoreal or you prefer T5):

```
An illustration of chrname, a girl with silver hair and red eyes wearing a school
uniform, standing outdoors among cherry blossom trees, looking toward the viewer in
bright daylight, full-body framing.
```

## 7. Contested / moving

- **Tag vs prose vs mixed** — strong signal that tags work, but the *optimal* blend is
  unsettled and domain-dependent. No official guidance.
- **Checkpoint drift** — original repo deprecated for Chroma1-Base/HD/Flash; mid-2025
  recipes may not transfer cleanly.
- Inherits the Flux-family "do triggers matter / how long" debates.

## 8. How it maps to CaptionForge sections

- **Chroma is the one model where the editor's multi-section design shines** — it can
  consume the **WD14 Tags** section, the **JoyCaption/Qwen-VL** prose, *or* a composed
  blend, depending on the concept's domain.
- Project profile should offer a **mode switch**: tags / prose / mixed (JoyCaption
  SD-prompt style = prose then booru tags). Default by dataset domain — anime/furry → tags,
  photoreal → prose.
- Validate booru tags against the Danbooru/e621 tag DB just like the anime SDXL forks; the
  prose path still wants the hedging-phrase checks.

## Sources

Chroma model card (HF lodestones/Chroma — Schnell base, 8.9B, 5M/20M dataset incl.
anime+furry, T5 padding fix, pruning, uncensored, deprecation note); JoyCaption repo (SD
Prompt + booru tag modes); Mohsin Akram 2026 tagging guide (Chroma/Noob e621/danbooru →
tags best); community training threads.
