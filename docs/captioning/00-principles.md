# Captioning Principles for LoRA Training

Shared fundamentals that apply across every model. The per-model docs lean on
this one instead of repeating it — read this first, then jump to your target
model.

Scope is **local LoRA training** (kohya_ss / sd-scripts, OneTrainer, ai-toolkit,
SimpleTuner). Most of this also applies to full fine-tunes, but the examples
assume LoRA.

> **A note on confidence.** Caption *mechanics* (token limits, what a kohya
> parameter does) are well-established. Caption *strategy* (how much to caption,
> tags vs prose, whether to caption at all) is genuinely contested and moves with
> each model release. Where something is community lore rather than a settled
> result, the docs say so. Treat strategy claims as strong starting heuristics,
> not law — and A/B test on your own dataset when it matters.

---

## What a caption actually does

A caption is not a description for a human. It is a **training signal** that tells
the model which words should become responsible for which parts of the image.

The single most important consequence:

> **Anything you name in the caption gets absorbed by that word. Anything you
> leave unnamed — but that's consistently present — gets baked into your trigger
> (or the LoRA as a whole).**

This is the rule that drives almost every decision below. Internalize it and most
"should I caption X?" questions answer themselves.

### Caption what you want to vary; omit what you want baked in

The canonical worked example:

- Training a **Harley Quinn** LoRA and you want the makeup *every time* → **do not
  caption the makeup.** It fuses into the trigger.
- Training a **Margot Robbie** LoRA where makeup is incidental → **caption "wearing
  face makeup"** so the trigger learns her *likeness*, not her makeup.

For a **character** LoRA: omit invariant identity traits (hair color, eye color,
signature features) so the trigger owns them; caption the variables (pose,
expression, outfit, background, framing, lighting) so they stay promptable and
decoupled.

For a **style** LoRA: invert it. Caption the *content* (subjects, objects,
composition) thoroughly so the model attributes the *non-content* — the look — to
the LoRA. Don't spell out the style itself; let the trigger own it.

The footgun in one sentence: **if you describe a trait every time, you split it off
from the trigger, and it stops appearing reliably without the extra words.**

---

## Trigger words (activation tokens)

A trigger word is a token you put in every caption so the LoRA binds the learned
concept to it. At inference you "summon" the concept by including that token.

- **Use a rare/unique token** so you don't pollute an existing concept. The old
  DreamBooth picks `sks` and `ohwx` are no longer truly rare (overused, and `sks`
  also maps to a firearm) — prefer a genuinely novel string or a unique name.
- **Be consistent.** The trigger's form must be identical in *every* caption file.
  Consistency across the dataset is a bigger lever than almost anything else.
- **Placement is model-dependent.** Tag-based models (SD1.5, SDXL, Pony,
  Illustrious/NoobAI) want the trigger **first**, as a leading tag. Natural-language
  models (Flux, SD3.5) want it **embedded in a phrase** — `"a photo of a woman named
  ohwxwoman"` outperforms a bare leading token, because the grammar lets the model
  bind the token to a class. Chroma does both depending on caption style.
- **Class token** (the category word — `woman`, `dog`, `car`): mainly needed when
  you train with **regularization images** (it must match the reg class). For a
  plain LoRA it's optional.
- **Do you even need a trigger?** For some natural-language models a real camp
  argues you can just describe the concept and prompt it back the same way. It's
  unsettled — see the Flux doc.

---

## Tags vs natural language

The split that drives everything: **what text encoder does the model use?**

| Encoder family | Models | Caption in… |
|---|---|---|
| CLIP only | SD1.5, SDXL, Pony, Illustrious, NoobAI | **Comma tags** (Danbooru/booru style) |
| T5 (+ CLIP) | Flux, SD3.5, Chroma | **Natural-language prose** |

- **CLIP** is a contrastive image-text encoder. It responds to *keyword bags* —
  `1girl, blue eyes, school uniform, classroom`. It does **not** parse long prose
  well; its reliable attention drops off well before its 75-token window fills.
- **T5** is a large language model. It parses *grammar* — clauses, prepositions,
  relationships ("a woman standing **behind** a red car"). That's why these models
  render legible text and follow spatial prompts, and why you caption them in
  sentences.

The anime SDXL forks (Pony, Illustrious, NoobAI) are CLIP models trained *directly*
on Danbooru/e621 tags, so for them "captioning" literally means **matching the
Danbooru tag vocabulary** — a tag the model never saw is dead weight.

**Caption the way you intend to prompt.** Your training captions become the phrasing
that reliably triggers your concept at inference. This is the unifying principle
behind both camps.

---

## The 75-token rule (CLIP models)

CLIP's context is **77 tokens, 2 reserved → 75 usable** per chunk, per text encoder.

- **Tokens are not words.** `purple` may be one token; an odd name several. Roughly
  ~60 comma-tags or a few sentences fills 75.
- Modern trainers (OneTrainer, recent kohya) **chunk** long captions (75/150/225)
  and concatenate embeddings rather than truncating — so going moderately over is
  fine, and they try to keep weight-groups like `black pants` intact within a chunk.
  Don't *rely* on it; keep semantic units together.
- T5 models have far larger budgets (Flux: long captions fine; SD3.5: keep under
  ~256 T5 tokens — see its doc for the artifact warning).

---

## Caption augmentation parameters (kohya / sd-scripts)

The knobs that interact with captioning. Verify against *your* trainer build —
SDXL support for several of these has shifted across versions (see the SDXL doc).

- **`shuffle_caption`** — randomly reorders comma-tags each step so the model
  doesn't over-learn tag position. Enable for comma-tag captions; pointless for
  prose. Requires `keep_tokens ≥ 1` to protect the trigger.
- **`keep_tokens` (N)** — pins the first N comma-groups so shuffle can't move them.
  A "token" here = one comma-group (`black cat` counts as one). **Set N = the number
  of leading tokens you front-loaded and want protected** — usually `1` for a single
  trigger, more if you front-load a fixed prefix (e.g. Pony's score chain).
- **`caption_dropout_rate` (0–1)** — chance per image of dropping the *entire*
  caption (trains that image caption-less), pushing some concept into the
  unconditional base so it fires even without the trigger. ~`0.1` is a common
  starting point, not a proven optimum.
- **`caption_tag_dropout_rate`** — drops *individual* tags at random; adds phrasing
  robustness.
- **`caption_dropout_every_n_epochs`** — drop all captions every N epochs.
- **`token_warmup`** — ramps the number of tags fed in over early steps.

> **Caching gotcha:** if your trainer caches text-encoder outputs, per-step caption
> shuffling/dropout is logically incompatible (cached = fixed). Historically kohya's
> SDXL pipeline disabled shuffle/dropout/token_warmup for this reason. This has been
> changing — check your build before assuming they work.

---

## Dataset hygiene (matters more than caption micro-tuning)

- **Auto-taggers hallucinate.** WD14 / wd-tagger (SmilingWolf) is the standard first
  pass for tag captions; VLMs (JoyCaption, Florence-2, Qwen-VL, CogVLM) for prose.
  **Always review and correct** — a wrong tag becomes a model error. The rentry
  proverb: *"tag a bunch of apples as oranges and it'll start generating oranges."*
- **Never describe what's absent.** No "no hat," no negative concepts in a positive
  caption — it poisons training.
- **Consistency beats cleverness.** One trigger form, one underscore/space
  convention, one separator (`, `), across the whole set.
- **Dataset variety** (angles, crops, lighting) usually matters more than caption
  wording. Fix the images before agonizing over captions.

---

## How this connects to CaptionForge

The editor produces multi-section caption files — JoyCaption and Qwen-VL
(natural-language) plus WD14 Tags (Danbooru tags) — and composes a **final training
caption** from them. The "right" composition depends entirely on the target model:

- **CLIP / tag models** (SD1.5, SDXL, Pony, Illustrious, NoobAI) → the **WD14 Tags**
  section is the primary source; the NL sections are reference material or get
  condensed/dropped.
- **T5 / prose models** (Flux, SD3.5) → the **JoyCaption / Qwen-VL** sections are
  primary; WD14 tags are optional and only feed the CLIP-L side.
- **Chroma** → most flexible; can take tags, prose, or a JoyCaption-style mix.

Each model doc ends with a **"How it maps to CaptionForge sections"** note spelling
this out — that's what should drive the per-model *project profiles* and the final
caption composer.
