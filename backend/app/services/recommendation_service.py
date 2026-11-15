"""Orchestration: turn an API request into a validated recommendation response."""
from __future__ import annotations

from app.core.config import settings
from app.schemas.recommendation import (
    RecommendationItem,
    RecommendationMeta,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services import ml_adapter
from app.services.catalog_provider import get_materials


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
        ),
    )
