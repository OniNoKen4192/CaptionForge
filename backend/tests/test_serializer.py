from captionforge.captions import parse, serialize, CaptionDoc, Section, TAGS, NL


def test_serializes_canonical_layout():
    doc = CaptionDoc(sections=[
        Section(label="WD14-Tags", kind=TAGS, tags=["Masami", "1girl"]),
        Section(label="Qwen-VL", kind=NL, text="A cat."),
    ])
    assert serialize(doc) == (
        "=== WD14-Tags ===\n"
        "Masami, 1girl\n"
        "\n"
        "=== Qwen-VL ===\n"
        "A cat.\n"
    )


def test_headerless_section_emits_no_header():
    doc = CaptionDoc(sections=[Section(label=None, kind=TAGS, tags=["a", "b"])])
    assert serialize(doc) == "a, b\n"


def test_empty_doc_serializes_to_empty_string():
    assert serialize(CaptionDoc(sections=[])) == ""


def test_roundtrip_idempotent_on_real_sample(sample_caption_text):
    once = parse(sample_caption_text)
    assert parse(serialize(once)) == once


def test_normalize_fixes_spacing_not_content(sample_caption_text):
    out = serialize(parse(sample_caption_text))
    assert "Masami, 1girl, solo" in out  # space added after the trigger
    assert "nude," not in out            # trailing comma gone


def test_serializer_preserves_profile_sensitive_tag_content():
    # Underscores, @artist prefix, and score_X must survive verbatim.
    # Correct normalization of these is profile-dependent and must NOT happen here.
    doc = parse("=== WD14-Tags ===\nlong_hair, @nnn yryr, score_9, looking_at_viewer")
    out = serialize(doc)
    for token in ["long_hair", "@nnn yryr", "score_9", "looking_at_viewer"]:
        assert token in out
    # round-trip stable
    assert parse(serialize(doc)) == doc
