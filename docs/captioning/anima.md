# Captioning for Anima LoRAs

> Read [00-principles.md](00-principles.md) first. Anima is a **new architecture** (not
> SDXL, not Flux) with an **LLM text encoder** — it's a third caption-style world that
> sits between the tag and prose camps. And it's *new*: base v1.0 landed May 2026, so the
> LoRA craft below is early-days community wisdom. Verified-vs-community is flagged
> throughout.

> ⚠️ **Not Animagine.** `circlestone-labs/Anima` is unrelated to the older SDXL "Animagine"
> model. Also distinct from the various Anima *merges* on Civitai (AnimaYume, WAI-Anima,
> etc.) — this doc is about **Anima-Base**.

## TL;DR

**Hybrid: Danbooru tags + natural-language sentences — and the mix is a real feature.**
Anima's text encoder is a small LLM (Qwen3 0.6B via an adapter), and it was trained on
tags-only, NL-only, *and* mixed captions. So caption with a tag block (Danbooru
vocabulary, **Gelbooru spelling**, **spaces not underscores**) plus 2+ NL sentences for
scene/arrangement. It has an explicit **quality + score + safety + year tag ladder** like
Pony/NoobAI. Anime/illustration only — it deliberately doesn't do realism.

## 1. Model identity (verified, from the model card)

| | |
|---|---|
| Maker / release | **CircleStone Labs** + Comfy Org; **Anima-Base v1.0, May 2026** |
| Architecture | **NVIDIA Cosmos-Predict2-2B**, a **DiT (diffusion transformer), rectified flow** — *not* a U-Net, *not* an SDXL fork, *not* Flux |
| Size | **2B params**, ~7GB VRAM; runs on SDXL/Illustrious-class GPUs |
| **Text encoder** | **Qwen3 0.6B (an LLM)** via an "LLM Adapter" bridging into a T5-compatible cross-attention space. **No CLIP.** |
| VAE | Qwen-Image VAE (16-channel) |
| Training data | Millions of anime images + ~800k non-anime art; photos filtered out; no synthetic data |
| Orientation | **Anime / illustration.** "The model doesn't do realism well. This is intended." |

**The load-bearing fact:** the encoder is an LLM trained on tags *and* prose *and* both
mixed. That's why Anima is natively hybrid — keep it in mind for everything below.

## 2. Caption style — hybrid, by design

- **Tags:** Danbooru vocabulary — and the card says **prefer the Gelbooru spelling** where
  Danbooru/Gelbooru differ. This is the anime-booru space (same family as
  Illustrious/NoobAI), **not e621/furry**.
- **Natural language:** the card actively recommends it — *"More descriptive is better.
  Aim for at least 2 sentences."* NL alongside tags reportedly **raises output
  resolution/detail.**
- **Hybrid is the sweet spot**: a tag block for things that map cleanly to booru tags + NL
  sentences for spatial/relational detail.

> **Verified caveat — NL doesn't escape the tag distribution.** Reviewers found Anima
> "can only output poses that exist as Danbooru tags"; novel NL pose instructions
> ("raising arms and looking left") often fail. So: **tags for pose/anatomy, NL for
> arrangement, lighting, mood, and multi-character disambiguation.**

## 3. Format, ordering & the quality/score/safety ladder (verified)

**Recommended order (from the card):**
```
[quality / meta / year / safety]  1girl/1boy/1other  [character]  [series]  [@artist]  [general tags]
```

- Separator: comma + space. **Tags use spaces, lowercase, NOT underscores** (`long hair`,
  not `long_hair`). **Exception: score tags keep underscores.**
- **Artist tags are prefixed with `@`** — e.g. `@nnn yryr`. Anima-specific.

**Three parallel quality/rating systems:**
1. **Human quality:** `masterpiece, best quality, good quality, normal quality, low quality, worst quality`
2. **Aesthetic score:** `score_9 … score_1` (underscored; reportedly from a PonyV7-based
   scorer — *medium confidence on provenance*, high confidence the tags are real). **Not**
   the same semantics as Pony V6's score chain.
3. **Safety:** `safe, sensitive, nsfw, explicit`

Plus **time tags:** `year 2025`, `newest`, `recent`, `mid`, `early`, `old`.

**Card-canonical positive prefix:** `masterpiece, best quality, score_7, safe,`
**Card-canonical negative:** `worst quality, low quality, score_1, score_2, score_3, artist name`

Prompt-weighting note: Anima needs **stronger weights** than SDXL (e.g. `(chibi:2)`) due to
the DiT/LLM stack.

## 4. Trigger word handling (community — young, contested)

- **Placement:** leading general tag **right after the count tag**, e.g.
  `…, safe, 1girl, solo, kanachan, …` — note it sits *after* the quality/year/safety prefix
  because the recommended order front-loads those.
- **`keep_tokens` is largely ineffective here** — it would pin `masterpiece, best
  quality…`, not your trigger, given the prefix-first layout. Don't rely on it.
- **`shuffle_caption: false`.** You have meaningful NL word order; shuffling shreds it.
  (Disabling shuffle also makes `keep_tokens` moot — fine here.)
- **`caption_dropout`** is supported per-subset. **Gotcha:** changing the dropout rate
  requires **deleting and regenerating the latent/TE cache** (kohya docs).
- **Absorb vs keep:** let the trigger absorb constants (hair/eye color, face, body) — do
  *not* tag them, or Anima's own color priors (it drifts brown→orange) fight your data.
  Keep as separate tags the things you want to vary (hairstyle structure, accessories,
  expression, pose, outfit).

## 5. Length & detail / what to omit

- Caption the variables; let constants fold into the trigger (principles). Tooling like
  `neme-anima` automates this with **core-tag pruning** — drop any tag present in >35% of a
  character's frames so it bakes into the trigger.
- **Do include 2+ NL sentences** for scene/positioning — Anima rewards it and it lifts
  resolution.
- **Omit `year` tags from training** (community) — they tie the character to an era-style
  and cut flexibility. Add at inference only if you want a style nudge.
- **Use only real Danbooru/Gelbooru tags.** Invented tags (`left side ponytail` — not real;
  only `side ponytail` exists) become noise. Put directional detail in NL instead.

## 6. Do / Don't (Anima-specific sharp edges)

**Do**
- **Set `llm_adapter_lr = 0` — don't train the LLM adapter.** The single most important
  Anima knob, stated by the dev. diffusion-pipe defaults to off; **other trainers may not —
  check.** *(Verified, HF discussion #60.)*
- Use **low LR** — card says **2e-5–5e-5** (rank 32); community settled near **5e-5** (vs a
  typical SDXL `1e-4`). Lower if style bleeds.
- Train **step-based, not epoch-based** — community: usable ~1,800 steps, overfit after
  ~2,400.
- `shuffle_caption: false`. Spaces not underscores (except `score_X`). `@` on artist tags.

**Don't**
- **Don't train the text encoder casually.** The CLIP-less LLM-adapter stack is prone to
  **catastrophic forgetting** — style/TE LoRAs can "nuke" latent artist knowledge even at
  low weight. *(Verified, HF #60.)* Mitigations people use: dim/alpha 32/32 + ultra-low LR;
  pad the dataset with ~600 unrelated images; or the experimental
  `diff_output_preservation` with regularization images. The dev says the full release is
  being made more finetune-robust, so this advice may ease.
- Don't reuse SDXL prompt weights 1:1 — Anima needs stronger weights.
- Don't expect NL to produce off-distribution poses.

## 7. Worked example

Character "kanachan" — brown hair/eyes (identity → absorbed), a side ponytail + blue
scrunchie that should stay *optional* at inference. Image: front portrait, smiling, white bg.

```
masterpiece, best quality, score_7, safe, 1girl, solo, kanachan, A young anime girl smiles warmly at the viewer in a head-and-shoulders portrait. Her side ponytail falls to the right side of the image. side ponytail, ahoge, blue scrunchie, smile, looking at viewer, white background, simple background
```

- **Quality/score/safety prefix** leads (card-standard); this is also *why* `keep_tokens` is
  moot here — by design.
- `kanachan` placed early as the trigger; **no `brown hair`/`brown eyes`** → trigger owns
  the true color, dodging the orange-drift prior.
- **NL sentences** carry mood + the directional detail (`right side`) that has no clean booru
  tag.
- Hairstyle/accessory tags **kept separate** so `kanachan, hair down` works later.
- **No `year` tag** in training.

## 8. Contested / moving (this model is brand new)

Be honest: **Anima-Base v1.0 is ~weeks old.** Solid vs in-flux:

- **Verified (card):** architecture (Cosmos-Predict2 DiT + Qwen3 + Qwen VAE), hybrid
  tag+NL training, the quality/score/safety/year ladder, `@artist`, Gelbooru-spelling,
  no-underscores, "don't train the LLM adapter / low LR."
- **Contested (community):** optimal NL-vs-tag ratio for a *LoRA* (card says NL helps;
  some go near tag-only and report fine results); the **catastrophic-forgetting problem is
  open** with competing workarounds and a promised base-model fix; `score_X` provenance
  ("PonyV7-based") is medium-confidence; keep_tokens/shuffle norms are one author's setup,
  not yet standard.
- **Tooling is fragmenting fast** — official kohya `anima_train_network.py`,
  Anima-TrainFlow, neme-anima, AnimaLoraToolkit, a ComfyUI Anima LoRA Trainer node, and
  more. No single blessed pipeline yet.

**Expect this doc to need a revisit as the full release lands.**

## 9. How it maps to CaptionForge sections

- **Anima is the second model (with Chroma) where your multi-section design directly pays
  off** — it natively wants **WD14 Tags + JoyCaption/Qwen-VL prose composed together**, not
  one or the other.
- Project profile needs Anima-specific handling the others don't:
  - **Spaces not underscores** in tags (except `score_X`) — a normalization rule.
  - **`@` prefix** on artist tags.
  - The **quality/score/safety/year ladder** injected as a prefix (training vs inference
    handled separately, like the anime forks).
  - **Gelbooru-spelling preference** when the tag DB has both — worth a validation note.
  - The composer should emit `prefix → trigger → NL sentences → variable tags` in that
    order; warn that `keep_tokens` won't protect the trigger here.
- Banned-hedging-phrase checks apply to the NL portion; Danbooru-tag validation to the tag
  portion.

## Sources

Anima model card (HF `circlestone-labs/Anima` — architecture, encoder, prompting + tag
ladder); Civitai 2458426 (release, settings, score provenance, LR); kohya
`anima_train_network.md` (LLM adapter, cache gotchas); HF discussion #60 (don't-train-adapter,
forgetting, low LR); GIGAZINE release coverage; lilting.ch technical + caption-rework
analyses; neme-anima (core-tag pruning).
