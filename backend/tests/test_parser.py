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
