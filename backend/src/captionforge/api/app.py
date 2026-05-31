from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..captions import parse, serialize, CaptionDoc
from . import dataset as ds
from . import storage


class OpenBody(BaseModel):
    path: str


class ParseBody(BaseModel):
    raw: str


class SaveBody(BaseModel):
    sections: list[dict] | None = None
    raw: str | None = None
    base_mtime: float | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="CaptionForge")
    app.state.root = None

    def require_root() -> Path:
        if app.state.root is None:
            raise HTTPException(status_code=409, detail="no dataset open")
        return app.state.root

    def resolve_image(item_id: str) -> Path:
        root = require_root()
        try:
            image_path = ds.resolve_within(root, item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad item id")
        if not image_path.is_file():
            raise HTTPException(status_code=404, detail="no such image")
        return image_path

    @app.post("/api/dataset/open")
    def open_dataset(body: OpenBody):
        root = Path(body.path)
        if not root.is_dir():
            raise HTTPException(status_code=400, detail="not a directory")
        app.state.root = root.resolve()
        return {"root": str(app.state.root), "items": ds.scan_dataset(app.state.root)}

    @app.post("/api/parse")
    def parse_raw(body: ParseBody):
        return parse(body.raw).to_dict()

    @app.get("/api/item/{item_id:path}")
    def get_item(item_id: str):
        image_path = resolve_image(item_id)
        caption_path = image_path.with_suffix(".txt")
        if caption_path.is_file():
            doc = parse(storage.read_text(caption_path))
            mtime = storage.file_mtime(caption_path)
        else:
            doc = CaptionDoc(sections=[])
            mtime = None
        return {
            "image_url": f"/api/image/{quote(item_id)}",
            "sections": doc.to_dict()["sections"],
            "caption_mtime": mtime,
        }

    @app.get("/api/image/{item_id:path}")
    def get_image(item_id: str):
        return FileResponse(resolve_image(item_id))

    @app.put("/api/item/{item_id:path}")
    def save_item(item_id: str, body: SaveBody):
        image_path = resolve_image(item_id)
        has_sections = body.sections is not None
        has_raw = body.raw is not None
        if has_sections == has_raw:  # both or neither
            raise HTTPException(status_code=422, detail="provide exactly one of sections|raw")
        if has_raw:
            doc = parse(body.raw)
        else:
            try:
                doc = CaptionDoc.from_dict({"sections": body.sections})
            except (KeyError, TypeError) as exc:
                raise HTTPException(status_code=422, detail=f"invalid section: {exc}")
        caption_path = image_path.with_suffix(".txt")
        current = storage.file_mtime(caption_path)
        if current is not None and body.base_mtime != current:
            raise HTTPException(status_code=409, detail="file changed externally")
        new_mtime = storage.atomic_write(caption_path, serialize(doc))
        return {"sections": doc.to_dict()["sections"], "caption_mtime": new_mtime}

    return app
