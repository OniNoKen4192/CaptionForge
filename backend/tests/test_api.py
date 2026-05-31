from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from captionforge.api.app import create_app


@pytest.fixture
def dataset_dir(tmp_path: Path) -> Path:
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG-ish bytes
    (tmp_path / "a.txt").write_text(
        "=== WD14-Tags ===\nMasami,1girl, solo,\n\n=== Qwen-VL ===\nA cat.\n",
        encoding="utf-8",
    )
    (tmp_path / "b.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # unpaired
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_open_lists_items(client, dataset_dir):
    r = client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    assert r.status_code == 200
    ids = {it["id"]: it for it in r.json()["items"]}
    assert set(ids) == {"a.png", "b.png"}
    assert ids["a.png"]["has_caption"] is True
    assert ids["b.png"]["has_caption"] is False


def test_open_rejects_missing_dir(client, tmp_path):
    r = client.post("/api/dataset/open", json={"path": str(tmp_path / "ghost")})
    assert r.status_code == 400


def test_parse_endpoint(client):
    r = client.post("/api/parse", json={"raw": "=== Misc ===\na, b, c"})
    assert r.status_code == 200
    secs = r.json()["sections"]
    assert secs[0]["kind"] == "tags"
    assert secs[0]["tags"] == ["a", "b", "c"]


def test_get_item_returns_parsed_sections(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/item/a.png")
    assert r.status_code == 200
    data = r.json()
    assert data["sections"][0]["tags"][:2] == ["Masami", "1girl"]
    assert data["caption_mtime"] is not None
    assert data["image_url"].endswith("/api/image/a.png")


def test_get_unpaired_item_has_empty_sections(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/item/b.png")
    assert r.status_code == 200
    assert r.json()["sections"] == []
    assert r.json()["caption_mtime"] is None


def test_get_image_returns_bytes(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    r = client.get("/api/image/a.png")
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")


def test_item_rejects_traversal(client, dataset_dir):
    client.post("/api/dataset/open", json={"path": str(dataset_dir)})
    assert client.get("/api/item/..%2Fsecret.txt").status_code == 400
