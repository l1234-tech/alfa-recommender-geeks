"""Read the public-metadata catalog from PostgreSQL.

Install the pinned optional driver with: pip install "psycopg[binary]==3.2.3"
The SQL deliberately excludes private content and all user-level identifiers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from recommender.data_processing.catalog import normalize_item
from recommender.models import CatalogItem


SQL_PATH = Path(__file__).with_name("catalog.sql")


def load_catalog(connection: Any) -> list[CatalogItem]:
    """Load catalog metadata using an existing psycopg-compatible connection."""
    query = SQL_PATH.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        names = [column.name for column in cursor.description]
    return [normalize_item(dict(zip(names, row))) for row in rows]
