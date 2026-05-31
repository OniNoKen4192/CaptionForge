from pathlib import Path

import pytest

from captionforge.api.dataset import scan_dataset, resolve_within, IMAGE_EXTS


def _touch(p: Path, content: str = "x"):
    p.write_text(content, encoding="utf-8")


def test_scan_pairs_by_stem_and_lists_unpaired(tmp_path: Path):
    _touch(tmp_path / "a.png")
    _touch(tmp_path / "a.txt")
    _touch(tmp_path / "b.jpg")  # unpaired image
    (tmp_path / "sub").mkdir()
    _touch(tmp_path / "sub" / "c.png")  # must NOT be found (non-recursive)

    items = scan_dataset(tmp_path)
    by_id = {it["id"]: it for it in items}

    assert set(by_id) == {"a.png", "b.jpg"}
    assert by_id["a.png"]["has_caption"] is True
    assert by_id["b.jpg"]["has_caption"] is False
    assert by_id["a.png"]["caption_mtime"] is not None
    assert by_id["b.jpg"]["caption_mtime"] is None


def test_scan_is_sorted(tmp_path: Path):
    for name in ["z.png", "m.png", "a.png"]:
        _touch(tmp_path / name)
    assert [it["id"] for it in scan_dataset(tmp_path)] == ["a.png", "m.png", "z.png"]


def test_supported_extensions():
    assert IMAGE_EXTS == {".png", ".jpg", ".jpeg", ".webp"}


def test_resolve_within_allows_direct_child(tmp_path: Path):
    _touch(tmp_path / "a.png")
    assert resolve_within(tmp_path, "a.png") == (tmp_path / "a.png").resolve()


def test_resolve_within_rejects_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        resolve_within(tmp_path, "../secret.txt")
    with pytest.raises(ValueError):
        resolve_within(tmp_path, "sub/c.png")
