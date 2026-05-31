from captionforge.captions.parser import parse
from captionforge.captions.model import TAGS, NL


def test_parses_three_real_sections(sample_caption_text):
    doc = parse(sample_caption_text)
    labels = [s.label for s in doc.sections]
    kinds = [s.kind for s in doc.sections]
    assert labels == ["WD14-Tags", "Qwen-VL", "JoyCaption2"]
    assert kinds == [TAGS, NL, NL]


def test_tag_section_tokenized_with_quirks(sample_caption_text):
    doc = parse(sample_caption_text)
    tags = doc.sections[0].tags
    assert tags[:3] == ["Masami", "1girl", "solo"]
    assert "" not in tags  # trailing comma produced no phantom


def test_nl_section_text_is_stripped(sample_caption_text):
    doc = parse(sample_caption_text)
    assert doc.sections[1].text.startswith("The image depicts")
    assert not doc.sections[1].text.endswith("\n")


def test_label_order_is_preserved_not_assumed():
    text = "=== JoyCaption2 ===\nprose here.\n\n=== WD14-Tags ===\na, b, c"
    doc = parse(text)
    assert [s.label for s in doc.sections] == ["JoyCaption2", "WD14-Tags"]
    assert doc.sections[1].kind == TAGS


def test_headerless_tag_blob_is_single_tag_section():
    doc = parse("1girl, solo, long hair, blue eyes")
    assert len(doc.sections) == 1
    assert doc.sections[0].label is None
    assert doc.sections[0].kind == TAGS
    assert doc.sections[0].tags == ["1girl", "solo", "long hair", "blue eyes"]


def test_headerless_prose_is_single_nl_section():
    doc = parse("A cat sits on a mat. It is calm.")
    assert len(doc.sections) == 1
    assert doc.sections[0].kind == NL
    assert doc.sections[0].label is None


def test_empty_file_yields_no_sections():
    assert parse("").sections == []
    assert parse("   \n  ").sections == []


def test_unknown_label_defaults_to_nl():
    doc = parse("=== Notes ===\nremember to recheck lighting")
    assert doc.sections[0].label == "Notes"
    assert doc.sections[0].kind == NL


def test_unknown_label_with_taglike_body_infers_tags():
    doc = parse("=== Misc ===\nred, blue, green, yellow, black")
    assert doc.sections[0].kind == TAGS


def test_preamble_before_first_header_is_preserved():
    doc = parse("loose note\n\n=== WD14-Tags ===\na, b")
    assert doc.sections[0].label is None
    assert doc.sections[0].kind == NL
    assert "loose note" in doc.sections[0].text
    assert [s.label for s in doc.sections][1] == "WD14-Tags"
    assert doc.sections[1].tags == ["a", "b"]
