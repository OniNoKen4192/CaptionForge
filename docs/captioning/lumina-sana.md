# Captioning for Lumina-Image 2.0 & Sana LoRAs

> Read [00-principles.md](00-principles.md) first. These two recent lightweight DiT models
> are grouped because they share the same defining trait: a **decoder-only Gemma-2-2B LLM**
> as text encoder (no CLIP, no T5). Both reward natural-language captions — but they diverge
> hard in practice, and **Sana's LoRA-captioning guidance is essentially nonexistent.**

## TL;DR

- **Lumina-Image 2.0** (2.6B, Gemma-2-2B encoder): has a real **anime ecosystem** via the
  **Neta Lumina** community fine-tune, which understands **Danbooru tags AND natural
  language** — but you pick *one* per caption. Uses a literal **`<Prompt Start>` system-prompt
  token**. Runs on 12GB.
- **Sana** (0.6B/1.6B/4.8B, Gemma-2-2B encoder): **natural-language only, long & detailed**
  (short captions look actively bad), **no anime ecosystem, no booru-tag heritage**, and
  thin/rough tooling. The lightest model here (4-bit inference in 8GB), but LoRA captioning
  for it is largely undocumented — treat this section as extrapolation.

The shared lesson: a Gemma LLM encoder reads grammar and instructions, so caption in
sentences. The divergence: Lumina was *deliberately* given booru-tag ability (via Neta);
Sana was not.

---

## LUMINA-IMAGE 2.0

### 1. Identity (verified)
- Alpha-VLLM; early 2025 (paper arXiv 2503.21758). "Unified Next-DiT," flow-based, **2.6B**.
  VAE = FLUX 16-channel. Encoder = **Gemma-2-2B** (decoder-only LLM, multilingual).
- Very accessible: rank-16 LoRA ~12–14GB; trainable on a 3060 12GB / 4060 Ti 16GB.
- **For anime, use the Neta Lumina fine-tune** — that's where the anime LoRA scene lives.

### 2. Caption style — pick a lane
- **Hybrid-capable, but choose ONE primary mode per caption.** Neta trained tags and natural
  language as co-equal first-class inputs, so the model understands both — but official
  guidance is **tags OR natural language, not blended** (mixing is "experimental").
- **It takes booru tags** (unusual for a Gemma-encoder DiT) — a deliberate consequence of
  Neta's Danbooru training. This is the big differentiator from Sana.
- Two community camps: tag-based Danbooru style (anime/Neta crowd) or natural-language via
  **JoyCaption** descriptive mode (style LoRAs).

### 3. Format & ordering — the system prompt is the sharp edge
- **Lumina prepends a system prompt during training**, and `<Prompt Start>` is a **real
  structural token** — your caption goes *after* it:
  - General: `You are an assistant designed to generate high-quality images based on user
    prompts. <Prompt Start> …`
  - Neta anime: `You are an assistant designed to generate anime images based on textual
    prompts. <Prompt Start> …`
- **Trainer gotcha:** ai-toolkit's Lumina config injects the prefix for you; if your trainer
  doesn't, **bake the full `…<Prompt Start>` prefix into every `.txt`.** Match training and
  inference prefixes or alignment degrades.
- **Neta tag order (when using tags):** subject (`1girl`, char) → `@artist` → appearance →
  costume → expression/action → camera → effects → scene → quality tags. Special syntax:
  **`@artist_name`** for style, **`#character_name`** for character; escape parens
  `@artist_\(name\)`. Quality tags (`masterpiece`, `best quality`) work — because Neta
  trained on them.

### 4. Trigger / 5. length
- Trigger leads, right after `<Prompt Start>`. shuffle/keep_tokens are SD carry-over
  heuristics, **unverified** for this architecture. Gemma takes long prompts, so detailed
  captions are fine and generally better; apply caption-what-you-want-to-vary (omit invariant
  identity traits to bake into the trigger).

### 6. Do / Don't
- **Do** keep the system prefix consistent training↔inference. **Do** start LoRA LR at
  **5e-5** (default 1e-4 runs hot); bf16, rank 8–32, ~500–2000 steps.
- **Don't** blend tags + NL haphazardly in one caption — pick a lane. **Don't** assume
  SD1.5 quality-tag magic works on *raw* Lumina 2.0 (it works on *Neta* because Neta trained
  it). **Verify your trainer actually works** — early LoRA support was flaky; SimpleTuner's
  Lumina2 quickstart is the more reliable current path.

### 7. Worked example (Neta, tag mode, anime)
OC "Mika," silver twin-tails, red jacket, cafe:
```
You are an assistant designed to generate anime images based on textual prompts. <Prompt Start> 1girl, mika_oc, silver hair, twintails, red eyes, red jacket, white shirt, sitting, cafe, window seat, soft afternoon light, looking at viewer, masterpiece, best quality
```
- `mika_oc` = trigger (pinned leading). Identity traits captioned here so they bind to both
  her name token *and* appearance tags (override flexibility). Jacket/cafe/light = variables.

Natural-language variant (style LoRA):
```
You are an assistant designed to generate high-quality images based on user prompts. <Prompt Start> A digital anime illustration of a young woman with silver twin-tails and red eyes, wearing a red jacket, sitting by a cafe window in soft afternoon light.
```

---

## SANA

### 1. Identity (verified)
- NVIDIA + MIT HAN Lab. Sana 1.0 (arXiv 2410.10629, Oct 2024); Sana 1.5 4.8B (arXiv
  2501.18427). **Linear-attention DiT** (O(N)) + **Deep Compression Autoencoder (32× vs 8×)**
  — the efficiency story. **0.6B / 1.6B / 4.8B.** Encoder = **Gemma-2-2B** (decoder LLM).
- Lightest model in these docs: 0.6B on a 16GB laptop GPU, **4-bit in 8GB**, up to 4096px.
- **Photo/general first. No anime-specialized Sana ecosystem** exists (the practical
  dealbreaker for anime work) and no booru-tag culture.

### 2. Caption style — natural language, hard
- **Natural language, full sentences, NOT tags** — no booru heritage.
- **CHI ("Complex Human Instruction"):** Sana's signature. At *inference* the pipeline wraps
  your prompt in an instruction telling Gemma to expand it into a detailed visual description.
- **Encoder gotcha (verified):** "Sana uses an odd text encoder configuration that means
  shorter prompts will possibly look very bad." So **short captions are actively harmful —
  lean long and descriptive** (color, shape, texture, spatial detail).
- **Community LoRA captioning practice: effectively none.** Say so.

### 3–6. Format / trigger / length / do-don't
- Plain descriptive prose; **no quality-tag system**. Whether to wrap *training* captions in
  the CHI template is undocumented — safest is to caption in the same rich style CHI
  *produces*, so training and inference distributions match.
- Trigger embedded DreamBooth-style in the sentence ("A photo of `sks_mika`, a woman
  with…"). shuffle/keep_tokens don't apply (no tags).
- **Trainer gotchas (verified, SimpleTuner):** plain **LoRA is "not supported" → use LoKr
  (LyCORIS)** (diffusers' own Sana DreamBooth-LoRA script does support LoRA, so pick your
  trainer accordingly); **training hits NaNs**; originally fp16-only (bf16 weights now exist
  — verify); high loss values are normal.
- **Do** use a **much lower LR (~1e-5)**. **Do** curate clean images — "Sana absorbs
  artifacts *first*, then learns the concept," so image quality matters more than elsewhere.
  **Don't** feed short captions. **Don't** use booru tags.

### 7. Worked example (natural language)
```
A photograph of sks_mika, a young woman with long silver twin-tailed hair and red eyes, wearing a red zip-up jacket over a white shirt. She sits at a wooden table by a large cafe window, a white coffee cup in front of her, looking toward the camera. Warm afternoon sunlight, soft shadows, shallow depth of field, detailed and realistic.
```
- `sks_mika` = trigger, embedded (no tag slot to lead with). **Deliberately long** to satisfy
  the encoder. No quality tags — they do nothing on Sana.

---

## Quick comparison

| | **Lumina-Image 2.0** | **Sana** |
|---|---|---|
| Encoder | Gemma-2-2B | Gemma-2-2B |
| Params | 2.6B | 0.6B / 1.6B / 4.8B |
| Booru tags? | **Yes** (via Neta) | **No** |
| Caption style | Tags **or** NL (pick one) | NL only, long & detailed |
| System prompt | **`…<Prompt Start>`** token | None (CHI is inference-side) |
| Quality tags | Yes (Neta) | None |
| Anime ecosystem | **Yes** (Neta Lumina) | No |
| LoRA LR start | ~5e-5 | ~1e-5 (much lower) |
| Trainer notes | ai-toolkit (was flaky), SimpleTuner | SimpleTuner = **LoKr not LoRA**, NaNs, fp16 |

## Contested / moving

- **Both are thinly documented for LoRA;** the strongest guidance is *inference* prompting
  transplanted to training on the reasonable assumption distributions should match.
- **Sana specifically is the least-documented model in these docs** — its LoRA captioning is
  extrapolated from the encoder design + SimpleTuner warnings. Battle-tested Sana caption
  recipes don't really exist yet. Be honest about that.
- Lumina tags-vs-NL ("pick one") is consensus but not unanimous; system-prefix handling
  varies by trainer.

## How it maps to CaptionForge sections

- **Lumina (Neta):** can use **WD14 Tags** *or* **JoyCaption/Qwen-VL** prose — a **mode
  switch**, like Chroma, plus a Lumina-only need to **prepend the `<Prompt Start>` system
  prefix** and support `@artist` / `#character` syntax. Quality tags valid (Neta).
- **Sana:** **JoyCaption/Qwen-VL** prose only, with a **minimum-length guard** (short
  captions hurt). Drop the tag section entirely. No quality tags.
- Given how thin these are, a single shared "Gemma-encoder" profile with the two toggles
  (Lumina-prefix on/off, Sana min-length) is probably enough until the ecosystems mature.

## Sources

Lumina-Image 2.0 paper (arxiv 2503.21758) + HF card; Neta Lumina prompt guide (Civitai
16274); SimpleTuner Lumina2 quickstart; Sana papers (arxiv 2410.10629, 2501.18427);
diffusers SanaPipeline docs (CHI template); NVlabs/Sana repo; SimpleTuner SANA quickstart
(LoKr-not-LoRA, NaNs, short-prompt warning, image-quality warning).
