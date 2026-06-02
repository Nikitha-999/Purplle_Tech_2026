"""Store ID resolution and layout metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import StoreRow


@lru_cache
def _layout_payload() -> dict | None:
    path = get_settings().layout_path
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_store_id(store_id: str) -> str:
    """Map API aliases (e.g. STORE_BLR_002) to canonical store_id (ST1008)."""
    layout = _layout_payload()
    if layout is None:
        return store_id
    canonical = layout.get("store_id")
    aliases = layout.get("aliases") or []
    if store_id == canonical or store_id in aliases:
        return canonical or store_id
    return store_id


def ensure_store_exists(db: Session, store_id: str) -> str:
    canonical = resolve_store_id(store_id)
    row = db.get(StoreRow, canonical)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Store not found: {store_id}")
    return canonical


def list_known_store_ids() -> list[str]:
    layout = _layout_payload()
    if not layout:
        return []
    ids = [layout["store_id"]]
    ids.extend(layout.get("aliases") or [])
    return ids
