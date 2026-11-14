"""Aggregate-only offline evaluation of the metadata recommender."""
from __future__ import annotations

from collections.abc import Iterable

from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem, UserProfile
from recommender.ranking import recommend


def evaluate_content_baseline(
    events: Iterable[UserInteraction],
    catalog: list[CatalogItem],
    *,
    k: int = 10,
    onboarding: UserProfile | None = None,
) -> dict[str, float]:
    """Evaluate per-user temporal holdout and return aggregate metrics only."""
    splits = temporal_holdout(events)
    recommendations: list[list[str]] = []
    relevant_sets: list[set[str]] = []
    for split in splits:
        profile = build_user_profile(split.train_events, catalog, onboarding=onboarding)
        ranked = recommend(profile, catalog, limit=k)
        recommendations.append([row.item.item_id for row in ranked])
        relevant_sets.append(set(split.test_relevant_item_ids))
    return aggregate_ranking_metrics(recommendations, relevant_sets, k=k)
