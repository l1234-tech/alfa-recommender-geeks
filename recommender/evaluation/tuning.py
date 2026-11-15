"""Validation-only grid search for hybrid recommendation weights."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import (
    aggregate_diversity_metrics,
    aggregate_ranking_metrics,
    catalog_coverage,
)
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend


def tune_hybrid_weights(
    events: Iterable[UserInteraction],
    catalog: Sequence[CatalogItem],
    *,
    tfidf_weights: Sequence[float] = (0.4, 0.55, 0.65, 0.8),
    content_weights: Sequence[float] = (0.25, 0.4, 0.5, 0.6, 0.75),
    k: int = 10,
    positive_rating_threshold: int = 4,
) -> list[dict[str, float | str]]:
    """Evaluate weight combinations on identical per-user temporal validation splits.

    The returned aggregate rows are suitable for validation-time model selection.
    They are not an unbiased test estimate. TF-IDF uses the current catalog
    snapshot, so historical catalog leakage remains a known limitation.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    if not tfidf_weights or not content_weights:
        raise ValueError("weight grids must not be empty")
    if any(not 0.0 <= value <= 1.0 for value in (*tfidf_weights, *content_weights)):
        raise ValueError("all weights must be between 0 and 1")

    rows = list(events)
    items = list(catalog)
    splits = temporal_holdout(rows, positive_rating_threshold=positive_rating_threshold)
    if not splits:
        return []

    tfidf = TfidfIndex.fit(items)
    available = {item.key for item in items if item.is_available}
    catalog_by_key = {item.key: item for item in items}
    relevant = [set(split.test_relevant_item_keys) for split in splits]
    results: list[dict[str, float | str]] = []

    # Fit each user's CF index once; only weights change inside the grid.
    prepared = []
    for split in splits:
        profile = build_user_profile(
            split.train_events, items,
            positive_rating_threshold=positive_rating_threshold,
        )
        cf = ItemItemIndex.fit(
            split.collaborative_train_events, items,
            positive_rating_threshold=positive_rating_threshold,
        )
        prepared.append((profile, cf))

    for tfidf_weight in tfidf_weights:
        predictions = []
        for profile, _ in prepared:
            ranked = recommend(
                profile, items, limit=k, strategy="hybrid",
                tfidf_index=tfidf, tfidf_weight=tfidf_weight,
            )
            predictions.append([rec.item.key for rec in ranked])
        metrics = aggregate_ranking_metrics(predictions, relevant, k)
        metrics.update(catalog_coverage(predictions, available))
        metrics.update(aggregate_diversity_metrics(predictions, catalog_by_key))
        results.append({
            "strategy": "content_hybrid",
            "tfidf_weight": float(tfidf_weight),
            "metadata_weight": float(1.0 - tfidf_weight),
            **metrics,
        })

    for tfidf_weight in tfidf_weights:
        for content_weight in content_weights:
            predictions = []
            for profile, cf in prepared:
                ranked = recommend(
                    profile, items, limit=k, strategy="content_cf_hybrid",
                    tfidf_index=tfidf, collaborative_index=cf,
                    tfidf_weight=tfidf_weight, content_weight=content_weight,
                )
                predictions.append([rec.item.key for rec in ranked])
            metrics = aggregate_ranking_metrics(predictions, relevant, k)
            metrics.update(catalog_coverage(predictions, available))
            metrics.update(aggregate_diversity_metrics(predictions, catalog_by_key))
            results.append({
                "strategy": "content_cf_hybrid",
                "tfidf_weight": float(tfidf_weight),
                "metadata_weight": float(1.0 - tfidf_weight),
                "content_weight": float(content_weight),
                "cf_weight": float(1.0 - content_weight),
                **metrics,
            })

    return sorted(
        results,
        key=lambda row: (
            -float(row.get(f"ndcg@{k}", 0.0)),
            -float(row.get(f"recall@{k}", 0.0)),
            -float(row.get(f"precision@{k}", 0.0)),
            -float(row.get("catalog_coverage", 0.0)),
        ),
    )
