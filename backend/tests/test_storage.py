from pathlib import Path

from captionforge.api.storage import read_text, file_mtime, atomic_write


def test_file_mtime_none_when_missing(tmp_path: Path):
    assert file_mtime(tmp_path / "nope.txt") is None


def test_atomic_write_creates_file_lf_utf8(tmp_path: Path):
    target = tmp_path / "out.txt"
    mtime = atomic_write(target, "line1\nline2\n")
    raw = target.read_bytes()
    assert raw == b"line1\nline2\n"  # LF preserved, no CRLF, no BOM
    assert isinstance(mtime, float)
    assert file_mtime(target) == mtime


def test_atomic_write_overwrites(tmp_path: Path):
    target = tmp_path / "out.txt"
    atomic_write(target, "old")
    atomic_write(target, "new")
    assert read_text(target) == "new"


def test_atomic_write_leaves_no_tmp_files(tmp_path: Path):
    target = tmp_path / "out.txt"
    atomic_write(target, "data")
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "out.txt"]
    assert leftovers == []
