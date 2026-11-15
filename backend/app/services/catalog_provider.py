"""Single source of truth for the material catalog served by the API.

Primary source is the provided Альфа-Курс PostgreSQL dump, read through the
ML team's loader (`recommender.data_processing.postgres_catalog.load_catalog`),
which the case requires as the basis of recommendations. When no database is
configured or reachable, a small demo catalog keeps the service runnable for
local development and jury checks without the private dataset.
"""
from __future__ import annotations

import logging
import os

from . import ml_adapter
from .sample_catalog import Material, get_catalog

logger = logging.getLogger(__name__)

_cache: list[Material] | None = None
_source = "sample"

def catalog_source() -> str:
    return _source



def get_materials(*, force_reload: bool = False) -> list[Material]:
    """Return the catalog, loading from the database once and caching it."""
    global _cache
    if _cache is not None and not force_reload:
        return _cache
    _cache = _load()
    return _cache


def _load() -> list[Material]:
    global _source
    _source = "sample"
    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith(("postgres://", "postgresql://")):
        try:
            items = _load_from_db(url)
            if items:
                _source = "database"
                logger.info("Catalog loaded from database: %d materials", len(items))
                return items
            logger.warning("Database catalog is empty; falling back to demo catalog")
        except Exception:
            logger.exception("Database catalog load failed; falling back to demo catalog")
    else:
        logger.info("DATABASE_URL not set; using demo catalog")
    return get_catalog()


def _load_from_db(url: str) -> list[Material]:
    import psycopg  # optional dependency, imported lazily

    ml_adapter.ensure_recommender_on_path()
    from recommender.data_processing.postgres_catalog import load_catalog

    with psycopg.connect(url) as connection:
        items = load_catalog(connection)
    return [_to_material(item) for item in items if item.is_available]


def _to_material(item) -> Material:
    """Adapt the ML `CatalogItem` to the backend `Material` used in responses."""
    topics = frozenset(item.topics)
    return Material(
        material_id=item.item_id,
        material_type=item.item_type,
        title=item.title,
        description=item.description,
        topic=sorted(topics)[0] if topics else item.item_type,
        topics=topics,
        tags=frozenset(item.tags),
        industries=frozenset(item.industries),
        is_paid=item.is_paid,
        is_available=item.is_available,
        url=item.url,
    )
