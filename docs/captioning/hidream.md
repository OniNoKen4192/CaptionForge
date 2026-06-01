# Captioning for HiDream-I1 LoRAs

> Read [00-principles.md](00-principles.md) first. HiDream uses **four** text encoders
> — including a Llama-3.1-8B LLM — so it's a natural-language model. Released 2025;
> conventions are <1yr old. **The load-bearing rule: train the LoRA on Full only.**

## TL;DR

**Natural-language prose; train on HiDream-I1-Full only.** HiDream-I1 is a ~17B sparse-MoE
DiT with four frozen text encoders (CLIP-L + CLIP-G + T5-XXL + Llama-3.1-8B-Instruct). The
LLM/T5 pair want sentences, not tag soup. It does **both anime and photo** well when you
*name* the style. No native quality-tag system. The Dev/Fast variants are distilled and
**will break if you train on them**.

## 1. Model identity (verified from card/paper)

| | |
|---|---|
| Maker / release | HiDream-ai (Vivago.ai); 2025; tech report arXiv 2505.22705 |
| Architecture | **Sparse Mixture-of-Experts (MoE) DiT**, dual-stream → single-stream with dynamic routing |
| Parameters | **~17B** total |
| Variants | **Full** (50+ steps), **Dev** (~28, distilled), **Fast** (~14–16, distilled) |
| License | MIT weights; T5 Apache-2.0; Llama-3.1 under Meta's license (matters if you redistribute) |
| Style | **Both** anime and photo — strong at anime when the style is named (better than Flux OOTB) |

**The four text encoders — the defining feature:**
1. **CLIP-L/14** + **2. CLIP-G/14** (long-context) → pooled vector for global "vibe/style"
   conditioning (adaptive layernorm).
3. **T5-XXL** → token sequence; syntax, spatial relations, fine linguistic detail.
4. **Llama-3.1-8B-Instruct** (decoder-only LLM) → embeddings from *multiple intermediate
   layers*; deep semantic/instruction understanding for long, nuanced prose.

T5 + Llama sequences are projected and concatenated into the DiT conditioning. Three of the
four encoders consume *sentences*, not fragments — and the Llama-Instruct lineage rewards
conversational, instruction-like phrasing. That's why HiDream is a "describe it in prose"
model.

## 2. Caption style — natural language, not tags

- **Write natural-language prose.** Official guidance: it "often prefers coherent,
  descriptive sentences over fragmented tags." Conversational phrasing works (Llama-Instruct
  lineage).
- **Booru tags** are accepted but under-use the encoders. Community lean: photoreal/style →
  natural language (strong consensus); anime character → **hybrid is fine** (pure tags work
  but waste the Llama/T5 advantage). Practical hybrid: a sentence that *embeds* the booru
  attributes ("...a girl with long blue hair and red eyes, looking at the viewer...").
- Community captioner of choice: **JoyCaption (Batch)**, ~128-token cap.

## 3. Caption format & ordering

- One `.txt` per image. Sentences/clauses with connective words ("holding," "sitting on,"
  "beside") — spatial relations are a T5/Llama strength.
- Trigger first (leading tokens carry more weight).
- **No native quality-tag vocabulary** — no `masterpiece`/`best quality` score scheme.
  SD-style `(keyword:1.3)` weighting still *functions* at inference, but don't build
  captions around it; **describe quality, don't tag it.**
- Length: ~50–75 tokens of relevant description at inference; training captions cap near
  **128 tokens** (longer gets truncated by trainers).

## 4. Trigger word handling

- **Leading token.** ai-toolkit auto-inserts the trigger if absent and supports a
  `[trigger]` placeholder. Put the trigger in *every* caption for style LoRAs.
- **shuffle/keep_tokens: don't** — those are kohya tag-shuffle idioms; shuffling clauses
  breaks the grammar the LLM encoders rely on. Caption dropout ~5% (ai-toolkit) / ~0.1%
  (SimpleTuner) is fine.
- **All four text encoders are frozen** — verified across ai-toolkit
  (`train_text_encoder: false`), SimpleTuner, diffusion-pipe. You steer the DiT, not the
  encoders; the model won't "learn" vocabulary the encoders don't already understand.

## 5. Length & detail

Caption-what-you-want-to-vary (principles), cleaner in prose: character → describe the
variable stuff (pose, outfit, background, expression, lighting) so the constant identity
binds to the trigger; don't exhaustively describe the unchanging face. Style → trigger every
caption, describe content so the style generalizes off the trigger. Clarity over volume —
piling synonyms dilutes.

## 6. Do / Don't

**Do**
- **Train on HiDream-I1-Full, always** (infer on Dev/Fast afterward is fine).
- Natural-language captions; embed booru attributes inside sentences for anime.
- **Quantize for local training: NF4 transformer + 4-bit Llama** is the proven 24GB recipe
  (diffusion-pipe on a 3090). Block swap + activation checkpointing + Flash-Attn2 to fit.
- Name the style explicitly for anime ("cel-shaded, bold linework, flat colors").

**Don't**
- **Don't train on Dev/Fast** — distilled, will break (highest-impact rule here).
- Don't train the text encoders (unsupported; stack stays frozen).
- Don't rely on a quality-tag system — none natively.
- Don't shuffle/keep_tokens prose captions.
- Don't assume FP8 "just works" — multiple OOM/load failures reported; **NF4 is the
  reliable training quant.**

LR varies an order of magnitude by trainer (2e-5 diffusion-pipe → 5e-5 SimpleTuner → 2e-4
ai-toolkit) — **start where your trainer's example config does.** ~3000 steps, ~3h on a 4090
is a common photoreal recipe.

## 7. Worked example

**Photo character LoRA**, trigger `ohwx woman`:
```
ohwx woman, a candid DSLR photograph of a woman standing on a rain-soaked city street at night, wearing a red trench coat, looking over her shoulder, neon signs reflected in the wet pavement, shallow depth of field, 85mm lens
```
- Trigger anchors the identity (first-token weight + frozen encoders = your only subject
  handle). Camera terms (`85mm`, `shallow depth of field`) land on T5/CLIP. Coat/pose/street
  are **variables** — don't describe her face in detail.

**Anime style LoRA**, trigger `myanime style`, hybrid:
```
myanime style, anime illustration of a young woman with long blue hair and red eyes, wearing a school uniform, sitting beside a window in soft afternoon light, cel-shaded with bold linework and clean flat colors
```
- Trigger every image; **name the style explicitly** (HiDream needs it named to render it);
  booru attributes embedded in the sentence keep T5/Llama grammar intact.

## 8. Contested / moving

- **VRAM floor:** early "48GB only" messaging is stale — **24GB is achievable** via
  diffusion-pipe NF4 + 4-bit Llama + block swap; framework-dependent, check your trainer.
- **LR:** 2e-5 vs 5e-5 vs 2e-4 across trainers — unsettled.
- **Tags vs prose for anime:** consensus is prose, but a minority reports pure-tag anime
  LoRAs train fine.
- Caption token cap (128 vs 256) is a trainer setting, not a hard model limit. Conventions
  <1yr old — treat numbers as starting points.

## 9. How it maps to CaptionForge sections

- Primary: **JoyCaption / Qwen-VL** NL section. For anime, embed the **WD14 Tags** content
  *inside* the prose (as plain attributes), don't append raw tags.
- Project profile: NL-primary; **warn/lock to "Full" as the training target** in any
  HiDream profile metadata; no quality-tag injection; ~128-token cap on the composed
  caption. Hedging-phrase checks on the prose; Danbooru validation only if you keep an
  anime tag block.

## Sources

HiDream-I1 tech report (arxiv 2505.22705) + HF model card (HiDream-ai/HiDream-I1-Full);
ai-toolkit train_lora_hidream config (Full-only, frozen TE, LR, dropout); SimpleTuner HiDream
example; diffusion-pipe issue #268 (NF4, block-swap, 3090); Civitai HiDream prompt-engineering
guide; renderartist LoRAs (JoyCaption 128-token).
