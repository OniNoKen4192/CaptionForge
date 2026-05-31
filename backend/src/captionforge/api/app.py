from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..captions import parse, serialize, CaptionDoc
from . import dataset as ds
from . import storage


class OpenBody(BaseModel):
    path: str


class ParseBody(BaseModel):
    raw: str


def create_app() -> FastAPI:
    app = FastAPI(title="CaptionForge")
    app.state.root = None

    def require_root() -> Path:
        if app.state.root is None:
            raise HTTPException(status_code=409, detail="no dataset open")
        return app.state.root

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

    return app
