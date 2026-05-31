from captionforge.captions.model import Section, CaptionDoc, TAGS, NL


def test_tag_section_roundtrips_through_dict():
    s = Section(label="WD14-Tags", kind=TAGS, tags=["Masami", "1girl"])
    assert Section.from_dict(s.to_dict()) == s


def test_nl_section_roundtrips_through_dict():
    s = Section(label="Qwen-VL", kind=NL, text="A cat.")
    assert Section.from_dict(s.to_dict()) == s


def test_tag_dict_omits_text_and_vice_versa():
    assert "text" not in Section(label="t", kind=TAGS, tags=["a"]).to_dict()
    assert "tags" not in Section(label="n", kind=NL, text="x").to_dict()


def test_doc_roundtrips():
    doc = CaptionDoc(sections=[
        Section(label="WD14-Tags", kind=TAGS, tags=["a", "b"]),
        Section(label=None, kind=NL, text="hi"),
    ])
    assert CaptionDoc.from_dict(doc.to_dict()) == doc
