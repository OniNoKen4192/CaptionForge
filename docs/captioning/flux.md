# Captioning for FLUX.1-dev LoRAs

> Read [00-principles.md](00-principles.md) first. Flux is a T5-based model — this is
> the **natural-language** world, fundamentally different from the SD/SDXL tag world.

## TL;DR

**Natural-language descriptive prose.** Flux uses a T5-XXL encoder (plus CLIP-L) that
parses grammar, so caption in sentences, not tag soup. Embed your trigger inside a
phrase (`"a photo of a woman named ohwxwoman"`), describe everything you want variable,
and write *differentiated* captions — Flux collapses near-identical short prompts to
near-identical images.

## 1. Text encoder & why captioning differs

- **T5-XXL + CLIP-L** (no CLIP-G). T5 carries the semantic load; it understands clauses,
  prepositions, and relationships ("a woman standing **behind** a red car"). That's why
  Flux renders text and follows spatial prompts.
- **Flow-matching model.** SimpleTuner's tell: *"shorter prompts with strong
  similarities result in practically the same image."* So sparse/short captions across a
  set collapse toward sameness — Flux rewards **descriptive, per-image-differentiated**
  captions.
- **Flux.1-dev is guidance-distilled** (you pass a `guidance` scalar instead of real
  CFG). That's a *sampling* property, but it's the root of Flux's "weird to train"
  reputation.

## 2. Caption style

- Natural-language prose — one flowing description or a few sentences.
- Autocaption tools, roughly by Flux popularity:
  - **JoyCaption** (fpgaminer) — built *for* diffusion training, uncensored, long
    descriptive prose; the community default.
  - **Florence-2** — fast, short-to-medium captions; common ComfyUI default.
  - **Qwen-VL / CogVLM** — heavier, richer, slower; when accuracy matters.
- **Mixing tags + prose** (WD14 tags concatenated with LLM prose) is defensible — feeds
  both the CLIP-L and T5 paths. Pure tag soup underuses T5; pure prose is the safe default.

## 3. Trigger word handling

- **Embed the trigger in a grammatical phrase**, not as a leading bare token. Consensus:
  `"a photo of a person named TRIGGER"` beats `"TRIGGER, a photo of…"` — the natural
  framing binds the token to a *class* instead of creating a competing standalone token.
- **ai-toolkit (ostris):** put the literal `[trigger]` placeholder in your `.txt` and set
  `trigger_word` in config; it substitutes automatically. Caption naturally, inject
  consistently.
- **kohya/OneTrainer:** trigger goes in the instance prompt / written into captions.
  OneTrainer requires *some* instance prompt even without a real trigger ("person",
  "style").
- Caption-the-surroundings rule (principles): the trigger **is** whatever you *didn't*
  describe. Caption dropout ~5–10% is optional regularization.

## 4. Length & detail

- **Much longer than SDXL is fine** — full sentences, often 50–150+ words with
  JoyCaption. T5 handles it.
- Omit-to-bake-in still rules (principles §"caption what you want to vary"): Harley Quinn
  → omit the makeup; Margot Robbie → caption "wearing face makeup."
- Style LoRAs: describe content (subjects, composition, framing, angles), **omit style
  descriptors**.
- Over-describing baked-in features is the classic footgun.

## 5. Do / Don't

**Do**
- Write **differentiated, descriptive** captions — Flux collapses near-identical short
  prompts.
- Embed triggers in natural phrasing.
- Vary dataset angles/crops (close-up, ¾, profile, full-body) — matters more than caption
  micro-tuning.

**Don't**
- Don't dump pure Danbooru tag soup — it underuses T5 (Flux *tolerates* tags, doesn't
  thrive on them).
- Don't assume captionless is better just because viral Civitai posts say so (see §7).
- Gotcha: some trainers trim captions over ~75 tokens believing brevity sharpens learning
  — contested, at odds with the "long is fine" camp.
- Gotcha: a minority swap T5-XXL for Flan-T5-XXL claiming gains — unverified, not a default.

## 6. Worked example

Character LoRA, a Margot-Robbie-like actress, token `ohwxwoman` (makeup is incidental →
captioned):

```
A photograph of a woman named ohwxwoman, sitting at an outdoor cafe table in soft
afternoon light. She is wearing a navy blouse and light face makeup, her blonde hair
loose over her shoulders. Three-quarter view, shallow depth of field, warm bokeh
background of a city street.
```

- Trigger embedded as "a woman named ohwxwoman" (class + identity).
- Makeup, clothing, hair, pose, lighting, background **captioned** → stay variable.
- Her facial identity deliberately **not** described → the token absorbs it.

## 7. Contested / moving

- **Captions vs no-captions.** Viral posts claim captionless training is *sharper*; the
  counter-consensus (kohya tips thread) is that captionless LoRAs are **less flexible** —
  they fail the "clown test" (can't take modifier prompts). Likely: captionless can win
  for single-look face LoRAs; captioned wins for flexibility/style. Not settled.
- **Short vs long captions** — "T5 loves long prose" vs "trim over ~75 tokens." No
  controlled consensus.
- **Do triggers even matter on Flux?** A real camp says just describe the concept
  naturally and prompt it back the same way; others insist a rare token helps separation.
  Depends on concept type.

## 8. How it maps to CaptionForge sections

- Primary: **JoyCaption** (or Qwen-VL) natural-language section — that prose *is* the Flux
  caption.
- **WD14 Tags**: optional. Concatenate after the prose if you want to feed the CLIP-L path
  (the hybrid tags+prose approach); otherwise drop.
- The editor's `[trigger]` handling should match the trainer: for ai-toolkit, leave the
  placeholder; for kohya, bake the trigger into the phrase. This is the section where the
  banned-hedging-phrase checks (`appears to`, `seems`) earn their keep — VLM prose is full
  of them and they pollute training.

## Sources

SimpleTuner Flux quickstart (prompt-similarity collapse, instance prompt); kohya
sd-scripts discussion #1497 (trigger-in-NL, clown test, Flan-T5/token-trim anecdotes);
ai-toolkit (`[trigger]` substitution); JoyCaption repo (modes); Civitai 7777 (Flux dataset
prep); pelayoarbues notes (Harley/Margot, WD14+LLM dual feed).
