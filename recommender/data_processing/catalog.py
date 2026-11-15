"""Normalize trusted, extracted catalog rows into the recommender contract."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from recommender.models import CatalogItem


def _as_set(value: object) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Sequence):
        values = value
    else:
        return frozenset()
    return frozenset(str(part).strip() for part in values if str(part).strip())


def _as_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "t", "1", "yes", "y"}:
            return True
        if normalized in {"false", "f", "0", "no", "n", ""}:
            return False
    raise ValueError(f"Unsupported boolean value: {value!r}")


def normalize_item(row: Mapping[str, object]) -> CatalogItem:
    required = ("item_id", "item_type", "title")
    missing = [key for key in required if not str(row.get(key) or "").strip()]
    if missing:
        raise ValueError(f"Missing required catalog fields: {', '.join(missing)}")

    return CatalogItem(
        item_id=str(row["item_id"]).strip(),
        item_type=str(row["item_type"]).strip(),
        title=str(row["title"]).strip(),
        description=str(row.get("description") or "").strip(),
        topics=_as_set(row.get("topics")),
        tags=_as_set(row.get("tags")),
        industries=_as_set(row.get("industries")),
        is_available=_as_bool(row.get("is_available"), default=True),
        url=str(row["url"]).strip() if row.get("url") else None,
        is_paid=_as_bool(row["is_paid"]) if row.get("is_paid") is not None else None,
    )
