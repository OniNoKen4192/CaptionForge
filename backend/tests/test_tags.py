from captionforge.captions.tags import tokenize_tags, join_tags


def test_splits_jammed_trigger():
    # Real quirk: "Masami,1girl" has no space after the first comma.
    assert tokenize_tags("Masami,1girl, solo") == ["Masami", "1girl", "solo"]


def test_drops_trailing_comma_phantom():
    assert tokenize_tags("a, b, c,") == ["a", "b", "c"]


def test_strips_and_drops_empties():
    assert tokenize_tags("  a ,, b ") == ["a", "b"]


def test_preserves_duplicates():
    assert tokenize_tags("a, a, b") == ["a", "a", "b"]


def test_join_uses_comma_space():
    assert join_tags(["a", "b", "c"]) == "a, b, c"
