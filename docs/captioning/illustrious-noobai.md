# Captioning for Illustrious XL & NoobAI XL LoRAs

> Read [00-principles.md](00-principles.md) first. Illustrious XL (OnomaAI) and
> NoobAI-XL (Laxhar Lab — an Illustrious-0.1 fork further trained on full
> Danbooru + e621) share near-identical conventions; differences are flagged inline.
> These are the current dominant anime SDXL models, and the conventions are **still
> settling** — see §9.

## TL;DR

**Danbooru-native comma tags — this is the whole game.** Both models were trained
*directly* on raw Danbooru (NoobAI also e621) tags, so captioning = **matching the
Danbooru tag vocabulary.** A tag that doesn't exist on Danbooru is dead weight.
Quality/aesthetic/year tags are real learned tokens with a published scheme.

## 1. Caption style

- **Comma-separated Danbooru tags.** `1girl, solo, long hair, blue eyes, school
  uniform, looking at viewer, classroom`. The model has a single learned concept for
  `blue_eyes`; prose like "her eyes are a deep violet" is weaker and bleeds color.
- **Verify tags exist on Danbooru** (`danbooru.donmai.us/tags`). Invented tags do
  nothing until *you* train them.
- Illustrious v1.1+/v2.0 added some NL capability; NoobAI is more purely tag-native.
  Tags remain the reliable, high-signal path for both.

**Underscores vs spaces:** practically interchangeable for these models — pick one,
be consistent, don't mix within a dataset. Danbooru/WD14 use underscores
(`long_hair`); kohya's tagger has `--remove_underscore` to convert to spaces, which
many enable so captions read like prompts. Note: literal parens in tags
(`ganyu_(genshin_impact)`) need escaping `\(\)` only when **prompting** in A1111/Forge
— **not** in training `.txt` files.

## 2. Quality / aesthetic / year tags

Real learned tokens — images were bucketed by measured percentile and labeled.

**NoobAI quality ladder (authoritative, Laxhar card):**

| Percentile | Tag |
|---|---|
| > 95th | `masterpiece` |
| 85–95th | `best quality` |
| 60–85th | `good quality` |
| 30–60th | `normal quality` |
| ≤ 30th | `worst quality` |

**Aesthetic axis (separate):** top 5% = `very awa` (NoobAI's distinctive token — *not*
the same as `very aesthetic`); bottom 5% = `worst aesthetic`.

**Year/era tags (style signal, not content):** `old` (2005–10), `early` (2011–14),
`mid` (2014–17), `recent` (2018–20), `newest` (2021–24); plus literal `year 2023` etc.
`newest` pushes toward the current anime aesthetic.

**Laxhar recommended prompt prefix:** `masterpiece, best quality, newest, absurdres,
highres, safe,`

**Illustrious** uses the same *family* of percentile quality buckets and year
modifiers (oldest ~2017 → newest ~2023); its exact aesthetic-token names are less
standardized than NoobAI's published scheme.

**TRAINING vs PROMPTING (key nuance):**
- **Training:** include a quality tag **only if it honestly varies across your
  dataset.** If every image is high quality, `masterpiece` on all of them teaches
  nothing and mildly binds your concept to that word. Many trainers **omit quality
  tags from character/concept captions** and rely on the base model.
- **Prompting:** *do* add `masterpiece, best quality, newest` — there they steer the
  frozen base toward its high-quality manifold.

## 3. Artist tags

Both models know thousands of Danbooru artist names as style tokens (e.g. `wlop`,
`as109`). Use the **bare** artist tag — no `artist:` prefix in prompts/captions.

- **Style LoRA:** to isolate a style, train with **no artist tag** (style binds to your
  trigger), or use the one artist tag if reproducing a known artist. For multi-source
  style LoRAs, keep general tags but **omit artist tags** so the style averages in.
- **Character LoRA:** **tag each image's artist** so the model factors style *out* of
  your character trigger (the cleaner method), or deliberately mix sources so no style
  dominates.
- Gotcha: a low-volume artist tag is weakly learned — verify it has real Danbooru
  volume before relying on it.

## 4. Caption format & ordering

Canonical order (Laxhar's published NoobAI structure; Illustrious is essentially the
same):

```
<count: 1girl/1boy/1other> , <character> , <series/copyright> , <artist> , <meta> , <general tags> , <other>
```

- Separator: comma + space. `1girl`/`1boy`/`2girls`/`1other` **first** (highest weight).
- Custom trigger goes first or right after the count tag, protected by `keep_tokens`.
- Quality/year prefix is a *prompting* convention; in training it's optional (§2).
- Illustrious's report puts artist/score/year near the *end*; the difference is minor
  in practice because shuffle reorders the non-kept region anyway.

## 5. Trigger word handling

- **Character:** if the character already has a Danbooru tag the model knows, you can
  reinforce it; for an OC or to avoid base bias, use a **unique uncommon trigger** (not
  a generic word that collides). Trigger first, `keep_tokens = 1` (more if multi-tag).
- **Style:** trigger optional — many style LoRAs are "always on." If you want a toggle,
  add a unique trigger and **caption everything** so the residual (the style) binds to it.
- `shuffle_caption = on` (needs `keep_tokens ≥ 1`). Protect the trigger from dropout;
  allow modest dropout on descriptive tags.

## 6. Length & detail

Omit-to-bake-in (principles). Character: omit invariant traits (`red eyes`, `silver
hair`) if you want them fused into the trigger; caption everything that varies. WD14 at
~0.35–0.5 confidence then **manual cleanup** is standard. Usually keep harmless anchors
like `1girl`/`solo`.

## 7. Do / Don't

**Do**
- Use tags that **actually exist on Danbooru** — verify on the site.
- One consistent underscore/space style across the set.
- Tag honestly; quality tags only where genuinely variable.
- WD14/wd-tagger first pass, then **review and correct**.

**Don't**
- Don't invent tags and expect them to work without training.
- Don't stuff `masterpiece, best quality` into every caption of a uniform-quality set.
- Don't write prose instead of tags (especially NoobAI).
- Don't escape parens in training `.txt` files (that's only for live prompts).
- **Don't confuse v-pred with captioning.** NoobAI ships **v-prediction** and
  **epsilon** checkpoints — that affects sampler/trainer math (v-pred: avoid Karras,
  prefer Euler/DDIM, CFG ~5–6), **not** caption text. But **train against the same
  prediction type you'll deploy on** — a LoRA can misbehave across types.

## 8. Worked example

OC "Mira" (silver-haired, red-eyed swordswoman). Image: full body, sitting, forest, day.

```
1girl, mira_oc, solo, red eyes, sword, sitting, forest, day, outdoors, looking at viewer, knee boots, smile, holding sword
```

- `1girl` first (structural anchor). `mira_oc` = trigger, `keep_tokens = 1`.
- `red eyes` **kept** here (you want it promptable). *Omit it instead* if you want it
  hard-baked into the trigger.
- **Silver hair deliberately not tagged** → baked into `mira_oc`.
- Outfit/pose/expression/scene captioned → separable.
- **No `masterpiece`/`newest`** (uniform clean set), **no artist tag** (sources mixed).
- At inference: `masterpiece, best quality, newest, absurdres, 1girl, mira_oc, ...`.

## 9. Contested / moving

- **Underscores vs spaces** — genuinely debated; consistency matters more than choice.
- **Quality tags in training** — omit-entirely vs include-for-varied-datasets; both
  defensible.
- **Caption invariant traits or not** — the omit-to-bake-in rule is widely repeated but
  not universal; some tag everything and report fine fidelity with enough images.
- **Illustrious v2.0's NL shift** — how much to lean on NL vs pure tags is still
  settling; NoobAI stays tag-centric.
- NoobAI aesthetic ladder beyond `very awa`/`worst aesthetic` is less firmly documented.

## 10. How it maps to CaptionForge sections

- Primary: **WD14 Tags** — this is the closest match between your existing pipeline and a
  model's native format. Drop the NL sections from the final caption.
- The editor's **Danbooru tag database is most valuable here** — validate every tag
  against it, flag non-Danbooru tags as ineffective, surface aliases/deprecated tags.
- Project profile: toggle quality-tag injection (default off for uniform sets), set the
  prompt-time prefix separately from training, handle artist-tag inclusion per LoRA type.

## Sources

Laxhar NoobAI-XL 1.1 card (quality/year tables, prefix); Illustrious technical report
(arxiv 2409.19946, caption schema); kohya WD14 tagger docs (`--remove_underscore`);
Civitai Illustrious/SDXL training-parameter guides; booru tagging guides.
