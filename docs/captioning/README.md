# Captioning Reference for LoRA Training

Internal reference docs on how image captioning conventions differ across local
image-generation models, for the purpose of **LoRA training**. These inform
CaptionForge's scoring rules, the final-caption composer, and per-model
**project profiles**.

**Audience:** people doing **local** image generation in the **anime or photographic**
space, training LoRAs on their own hardware. No video (that's a later effort), no
cloud-only models.

Scope: local generation/training (kohya_ss / sd-scripts, OneTrainer, ai-toolkit,
SimpleTuner, diffusion-pipe). Practical-reference depth — enough to caption a dataset
correctly, not a research treatise. Depth is revisitable if functionality later demands it.

> **Read [00-principles.md](00-principles.md) first.** It covers the fundamentals every
> model shares (what a caption does, the omit-to-bake-in rule, trigger words, the
> tags-vs-prose split, the 75-token rule, kohya augmentation params). The per-model docs
> assume it.

> **Building the editor?** Go straight to **[curation-rules.md](curation-rules.md)** — the
> actionable spec that distills these docs into what CaptionForge normalizes, validates,
> scores, and composes per model. The per-model docs below are the *why*; that one is the
> *what the tool enforces*.

## Which doc do I need?

The single biggest fork is **text encoder → caption style**:

| Model | Doc | Caption style | Trigger placement |
|---|---|---|---|
| SD 1.5 | [sd15.md](sd15.md) | Booru **tags**, short | Leading tag |
| SDXL (base) | [sdxl.md](sdxl.md) | **Hybrid** (tag-like + light prose) | Leading tag |
| Pony Diffusion V6 | [pony.md](pony.md) | Booru **tags** + score/rating/source | Leading tag |
| Illustrious / NoobAI | [illustrious-noobai.md](illustrious-noobai.md) | **Danbooru-native tags** | Leading tag |
| FLUX.1-dev | [flux.md](flux.md) | **Natural-language prose** | Embedded in phrase |
| SD 3.5 | [sd35.md](sd35.md) | NL prose, **length-bounded** | Embedded in phrase |
| Chroma | [chroma.md](chroma.md) | **Tags, prose, or mixed** | Tag-lead or phrase |
| Anima | [anima.md](anima.md) | **Hybrid tags + NL** (LLM encoder) | Leading tag (after prefix) |
| Qwen-Image | [qwen-image.md](qwen-image.md) | **NL prose** (multimodal LLM encoder) | Leading token |
| HiDream-I1 | [hidream.md](hidream.md) | **NL prose** (4 encoders incl. Llama) | Leading token |
| Lumina 2.0 / Sana | [lumina-sana.md](lumina-sana.md) | NL (Lumina also tags); Gemma encoder | Lead / embedded |

### Decision shortcuts

- **Anime/booru concept, want the new hotness?** → Anima (new architecture, hybrid
  tags+NL, anime-only). Or the established tag-based pair below.
- **Anime/booru concept, want crisp tag control?** → Illustrious/NoobAI (current
  dominant) or Pony. All tag-based; verify tags against Danbooru.
- **Photoreal, want prompt-following and legible text?** → Flux (most mature), Qwen-Image
  (best text rendering), HiDream (both anime+photo), or SD3.5 (keep captions short). All
  natural-language prose.
- **Want one model that takes both tags and prose?** → Chroma or Anima (most flexible;
  pin the checkpoint / mind Anima's newness).
- **Tight on VRAM?** → Sana (4-bit in 8GB) or Lumina 2.0 (~12GB), both Gemma-encoder;
  thinly documented for LoRA — see [lumina-sana.md](lumina-sana.md).
- **Legacy / fast / forgiving?** → SD 1.5. Short tag captions.

## The two worlds, in one picture

```
CLIP-only models  ───────────────►  comma TAGS (booru style)
  SD1.5, SDXL, Pony, Illustrious, NoobAI       trigger = leading tag

T5 (+CLIP) models ───────────────►  natural-language PROSE
  Flux, SD3.5                                   trigger = embedded in a phrase

LLM-encoder models ──────────────►  natural-language PROSE (mostly)
  Qwen-Image (Qwen2.5-VL), HiDream (Llama-3.1), trigger = leading token
  Lumina 2.0 / Sana (Gemma-2)                   or embedded

booru-trained "either/both" ─────►  TAGS or PROSE or MIXED
  Chroma (Flux base, e621/danbooru)            tag-lead or phrase
  Anima (Cosmos DiT + Qwen3, anime)            leading tag, after prefix
```

> **The trend:** newer models (2025–26) increasingly use an **LLM** as the text encoder —
> Qwen2.5-VL, Llama-3.1, Gemma-2, Qwen3 — instead of CLIP/T5. LLM encoders read grammar and
> instructions, so they all lean **natural-language**. The exceptions that also take tags
> (**Chroma**, **Anima**, Lumina via **Neta**) earned it by being *deliberately trained on
> booru data* — tag-ability is a dataset choice, not an encoder default.

## How these map to CaptionForge

The editor produces multi-section captions — **JoyCaption** + **Qwen-VL** (natural
language) and **WD14 Tags** (Danbooru) — and composes a final training caption. The right
composition is model-dependent:

- **Tag models** (SD1.5/SDXL/Pony/Illustrious/NoobAI) → the **WD14 Tags** section is
  primary; drop/condense the prose.
- **Prose / LLM-encoder models** (Flux, SD3.5, Qwen-Image, HiDream, Sana) → the
  **JoyCaption/Qwen-VL** sections are primary; tags optional, and for Qwen-Image/HiDream
  *embed* tag attributes in the prose as plain English rather than appending raw tags.
- **Both / mixed** (Chroma, Anima, Lumina-via-Neta) → tags *and* prose composed together;
  this is where the multi-section design pays off (Anima natively wants both).

Each model doc ends with a **"How it maps to CaptionForge sections"** note — those should
drive the per-model project profiles, the model-aware scoring (e.g. length caps for SD3.5,
artist-tag ineffectiveness on Pony, Danbooru-tag validation for the anime forks, a
minimum-length guard for Sana, no quality-tag injection for the LLM-encoder models), and the
final-caption composer modes. Several models also carry **"don't train X" trainer gotchas**
worth surfacing in profile metadata (HiDream: Full-only; Anima/Qwen/HiDream: frozen text
encoders).

## A standing caveat

Caption *mechanics* are settled; caption *strategy* is contested and moves with every
model release — especially the post-2024 models (Illustrious/NoobAI, Chroma) and anything
involving "should I caption X or bake it in." Every doc flags its contested points in a
**Contested / moving** section. Treat strategy as strong heuristics, A/B test when it
matters, and revisit these docs as the community consensus shifts.

*Compiled from primary model cards (HF/Civitai), trainer docs (kohya, OneTrainer,
SimpleTuner, ai-toolkit), the Illustrious and SDXL papers, and current community guides.
Per-doc sources are listed at the bottom of each file.*
