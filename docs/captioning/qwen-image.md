# Captioning for Qwen-Image LoRAs

> Read [00-principles.md](00-principles.md) first. Qwen-Image's text encoder is a
> **multimodal LLM (Qwen2.5-VL)** — so this is firmly the natural-language world, with
> no CLIP token limit and no booru-tag heritage. Released Aug 2025; conventions are <1yr
> old and unsettled.

## TL;DR

**Natural-language prose, trigger word first.** Qwen-Image is a 20B MMDiT whose encoder
is an actual vision-language LLM. Caption the way you'd describe a photo to a person —
full sentences, literal, no fluff. It has **no quality/score/rating tag system** (don't
port Pony/NoobAI/Anima tags). Photo/general-strong; anime-capable but weaker than the
purpose-built anime models, and pure booru tags cause "tag bleed."

## 1. Model identity (verified from card)

| | |
|---|---|
| Maker / release | Alibaba Qwen Team; **base Aug 2025**, Qwen-Image-Edit Aug 2025, refreshes late Dec 2025 |
| Architecture | **20B MMDiT** with MSRoPE joint text-image positional encoding |
| License | **Apache 2.0** |
| **Text encoder** | **Qwen2.5-VL** — a frozen multimodal (vision-language) LLM |
| Standout | **Best-in-class text rendering** (long/multi-line, Chinese script) |
| Style | Photoreal + anime, but **photo/general-strong, anime-weaker** than NoobAI/Illustrious |
| Local | Inference to ~4GB via offload; **training needs ~24GB comfortably** (FP8/INT8) |

**Why the encoder is the whole game:** Qwen2.5-VL is an instruction-tuned LLM that *also
sees images*. It parses grammar and relationships ("the red cup **to the left of** the
laptop"), not weighted token bags. There's effectively no 77-token limit; long prose is
the intended interface. Caption the way you'd describe the image to a person — literally
what the VL model was trained on.

## 2. Caption style — natural language, not tags

- **Consensus: natural-language full-scene descriptions.** Write "like you'd describe a
  real photograph," not a tag list. Direct consequence of the VL encoder.
- **Booru tags work poorly.** The base model is **not natively trained on the Danbooru
  vocabulary** — anime LoRAs on pure-tag datasets show **tag bleed** (features persist
  even when not prompted). *(One secondary source claimed Qwen was Danbooru-trained; the
  primary community deep-dive says the opposite. Treat "Qwen knows booru tags" as
  unverified and probably false — flagged in §8.)*
- **Anime workaround:** a hybrid — natural-language sentence that folds salient
  descriptors in **plain English** (`twin tails`, `school uniform`), not raw booru
  underscores (`twintails`, `looking_at_viewer`).

## 3. Caption format & ordering

- Normal English prose; sentences and commas, no underscore-joined tokens.
- Structure: `<trigger>, <one or two sentences: subject, clothing, pose, setting,
  lighting, framing>`.
- **No quality/rating/score system.** No `score_9`, `masterpiece`, `rating_safe`,
  `source_anime`. Porting those just dilutes the caption with meaningless tokens.

## 4. Trigger word handling

- **Leading token**, first in every caption and every inference prompt. Rare/unique token.
- **Two schools (the live debate, §8):** "trigger-only / minimal caption" (detailed
  captions reportedly *hurt* character LoRAs on small sets) vs "trigger + full
  description" (needed for style LoRAs and to separate subject from variables).
- **shuffle/keep_tokens/dropout** are tag-shuffling idioms — largely **N/A for prose**.
  Just keep the trigger pinned at the front.
- **Trainer gotchas (verified):**
  - **Text encoder is frozen.** ai-toolkit Qwen LoRA training is transformer-only by
    default — don't hunt for a text-encoder LR; it does nothing. (Qwen's "don't train X.")
  - **`[trigger]` substitution breaks with cached text embeddings.** On a 24GB config
    that caches embeddings, **bake the literal trigger into each caption file** instead of
    relying on `[trigger]`.

## 5. Length & detail

Caption-what-you-want-to-vary (principles): omit fixed identity traits (don't caption
"blonde hair" if she's always blonde — let the trigger own it); caption the variables
(pose, outfit, background, lighting, angle). Length: moderate, ~1–2 sentences / 15–40
words, **literal, no fluff**. Always omit watermarks/logos/signatures.

## 6. Do / Don't

**Do**
- Natural-language captions, literal, trigger first.
- For anime, caption *more aggressively* (more plain-English descriptors) to combat tag
  bleed.
- **FP8 / INT8 quantize** the base for local training (makes <24GB feasible) + block swap.
- Bake the literal trigger into captions if caching embeddings.

**Don't**
- Don't dump raw booru tags (tag bleed, wastes the LLM encoder).
- Don't import Pony/NoobAI/Anima quality/score tags — no such system here.
- Don't caption fixed identity traits you want baked in.
- Don't expect text-encoder training to do anything (frozen).
- **Edit variants** reportedly don't quantize like base, and need control/reference images
  in the dataset — different pipeline.

LR: community anchor ~**5e-5** (pushable to 8–9e-5); single numbers are unverified — A/B
it. 24GB (3090/4090/5090) is the comfortable practical floor at 768–1024px.

## 7. Worked example

**Photo character LoRA**, trigger `ohwx woman`:
```
ohwx woman, sitting on a wooden bench in a sunlit park, wearing a red cheongsam dress, three-quarter view, soft afternoon light, shallow depth of field
```
- Trigger absorbs the fixed identity (face/body) — don't caption hair color or facial
  structure. Dress/pose/view/light are **variables**, written as a sentence not tags.

**Anime character LoRA**, trigger `hoshino_ai`, hybrid prose:
```
hoshino_ai, an anime girl with long pink hair in twin tails, wearing a white school uniform, standing in a classroom, smiling, looking at the viewer, full body shot
```
- Deliberate hybrid: a sentence that folds readable descriptors (`twin tails`, `school
  uniform`) in **plain English** rather than booru underscores — what Qwen2.5-VL can parse.

## 8. Contested / moving

- **Trigger-only vs full natural-language captions** — sharpest disagreement; likely
  trigger-only suits tight single-subject sets, description-rich suits style/varied sets.
- **Was Qwen trained on booru tags?** Unresolved; lean *not natively booru-aware*.
- **Anime viability of base Qwen** — officially yes, community view is anime-mediocre vs
  NoobAI/Illustrious; some say anime needs a fine-tune not a LoRA.
- LR not converged; Edit-model training specifics still stabilizing.

## 9. How it maps to CaptionForge sections

- Primary: **JoyCaption / Qwen-VL** NL section — that prose *is* the Qwen-Image caption
  (fittingly, you may already be captioning with a Qwen model).
- **WD14 Tags**: mostly drop. For anime, optionally mine them for a missing descriptor,
  but **convert underscores to spaces / plain English** before they enter the caption —
  raw booru tags cause tag bleed here.
- Project profile: NL-primary, **no quality-tag injection**, trigger baked literally
  (not `[trigger]`) when the trainer caches embeddings. Hedging-phrase checks apply.

## Sources

Qwen-Image model card (HF Qwen/Qwen-Image), repo, blog, tech report (arxiv 2508.02324);
kombitz ai-toolkit walkthrough (trigger × cache gotcha); SECourses training tutorial;
Koin AI strengths/weaknesses (tag bleed, anime); ai-toolkit issue #406 (frozen encoder).
