"""Orchestration: turn an API request into a validated recommendation response."""
from __future__ import annotations

from ..core.config import settings
from ..schemas.recommendation import (
    RecommendationItem,
    RecommendationMeta,
    RecommendationRequest,
    RecommendationResponse,
)
from . import ml_adapter
from .catalog_provider import get_materials, catalog_source
import re
from urllib.parse import quote, urlsplit


PUBLIC_ORIGIN = "https://kurs.alfabank.ru"
PUBLIC_PATHS = {
    "article": "/articles/", "course": "/courses/", "document": "/documents/",
    "webinar": "/webinars/", "podcast": "/podcasts/", "calculator": "/calculators/",
    "glossary": "/vocabulary/",
}
_SLUG_RE = re.compile(r"^[\w-]+$", re.UNICODE)


def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    limit = request.limit or settings.default_limit
    limit = max(1, min(limit, settings.max_limit))

    cold_start = request.user_profile.is_empty() and not request.history

    fields = ml_adapter.build_profile_fields(request.user_profile, request.history)
    ranked = ml_adapter.rank(
        get_materials(),
        fields,
        limit=limit,
        strategy=settings.strategy,
        force_builtin=settings.force_builtin,
    )

    items = [
        RecommendationItem(
            material_id=r.material.material_id,
            title=r.material.title,
            description=(r.material.description or None) if r.material.is_paid is not True else None,
            url=public_url(r.material.url, r.material.material_type) if catalog_source() == "database" else None,
            material_type=r.material.material_type,
            topic=r.material.topic,
            is_paid=r.material.is_paid,
            score=r.score,
            reasons=r.reasons,
            next_step=r.next_step,
        )
        for r in ranked
    ]

    return RecommendationResponse(
        recommendations=items,
        metadata=RecommendationMeta(
            cold_start=cold_start,
            strategy=settings.strategy,
            limit=limit,
            returned=len(items),
            catalog_source=catalog_source(),
        ),
    )


def public_url(value: str | None, material_type: str | None = None) -> str | None:
    """Resolve catalog slugs to known public Альфа-Курс routes safely."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = urlsplit(raw)
        if parsed.scheme:
            if (parsed.scheme.lower() == "https" and parsed.hostname == "kurs.alfabank.ru"
                    and not parsed.username and not parsed.password):
                return raw
            return None
    except ValueError:
        return None
    path = PUBLIC_PATHS.get((material_type or "").strip().casefold())
    slug = raw.strip("/")
    if path is None or not _SLUG_RE.fullmatch(slug) or slug in {".", ".."}:
        return None
    return f"{PUBLIC_ORIGIN}{path}{quote(slug, safe='-_')}/"
