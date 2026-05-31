from captionforge.captions.kind import classify_label, infer_kind
from captionforge.captions.model import TAGS, NL


def test_label_match_tags():
    assert classify_label("WD14-Tags") == TAGS
    assert classify_label("danbooru tags") == TAGS


def test_label_match_nl():
    assert classify_label("Qwen-VL") == NL
    assert classify_label("JoyCaption2") == NL


def test_label_unknown_returns_none():
    assert classify_label("Notes") is None


def test_infer_tags_from_short_comma_fragments():
    body = "1girl, solo, long hair, blue eyes, simple background"
    assert infer_kind(body) == TAGS


def test_infer_nl_from_prose_with_commas():
    body = "A cat lies on a bed, facing the viewer. The lighting is soft."
    assert infer_kind(body) == NL


def test_infer_nl_from_empty():
    assert infer_kind("   ") == NL
