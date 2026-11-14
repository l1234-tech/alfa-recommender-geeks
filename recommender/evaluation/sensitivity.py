"""Validation-only sensitivity analysis for positive-event and item-item CF settings.

The returned rows contain aggregate metrics only; user identifiers never leave
this module. Use this sweep to select candidate settings, then evaluate the
chosen configuration once on a separate untouched test period.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics, catalog_coverage
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend


def evaluate_cf_sensitivity(
    events: Iterable[UserInteraction],
    catalog: Sequence[CatalogItem],
    *,
    rating_thresholds: Sequence[int] = (3, 4, 5),
    min_cooccurrences: Sequence[int] = (1, 2, 3),
    shrinkages: Sequence[float] = (0.0, 5.0, 10.0),
    k: int = 10,
) -> list[dict[str, float]]:
    """Evaluate a parameter grid on per-user temporal validation splits.

    Each configuration is trained only on events preceding each user's
    validation period. These metrics are for model selection, not final
    unbiased reporting. The final configuration must be evaluated on a
    separate later holdout.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    if not rating_thresholds or not min_cooccurrences or not shrinkages:
        raise ValueError("parameter grids must not be empty")
    if any(value < 1 for value in rating_thresholds):
        raise ValueError("rating thresholds must be positive")
    if any(value < 1 for value in min_cooccurrences):
        raise ValueError("min_cooccurrences must be at least 1")
    if any(value < 0 for value in shrinkages):
        raise ValueError("shrinkages must be non-negative")

    rows = list(events)
    items = list(catalog)
    tfidf = TfidfIndex.fit(items)
    available = {item.key for item in items if item.is_available}
    results: list[dict[str, float]] = []

    for threshold in rating_thresholds:
        splits = temporal_holdout(rows, positive_rating_threshold=threshold)
        if not splits:
            continue
        relevant = [set(split.test_relevant_item_keys) for split in splits]
        for min_cooccurrence in min_cooccurrences:
            for shrinkage in shrinkages:
                predictions_cf = []
                predictions_hybrid = []
                for split in splits:
                    profile = build_user_profile(
                        split.train_events,
                        items,
                        positive_rating_threshold=threshold,
                    )
                    cf_index = ItemItemIndex.fit(
                        split.collaborative_train_events,
                        items,
                        positive_rating_threshold=threshold,
                        min_cooccurrence=min_cooccurrence,
                        shrinkage=shrinkage,
                    )
                    predictions_cf.append([
                        rec.item.key for rec in recommend(
                            profile, items, limit=k, strategy="collaborative",
                            collaborative_index=cf_index,
                        )
                    ])
                    predictions_hybrid.append([
                        rec.item.key for rec in recommend(
                            profile, items, limit=k, strategy="content_cf_hybrid",
                            tfidf_index=tfidf, collaborative_index=cf_index,
                        )
                    ])

                for strategy, predictions in (
                    ("item_item_cf", predictions_cf),
                    ("content_cf_hybrid", predictions_hybrid),
                ):
                    metrics = aggregate_ranking_metrics(predictions, relevant, k)
                    metrics.update(catalog_coverage(predictions, available))
                    results.append({
                        "rating_threshold": float(threshold),
                        "min_cooccurrence": float(min_cooccurrence),
                        "shrinkage": float(shrinkage),
                        "strategy_code": 1.0 if strategy == "item_item_cf" else 2.0,
                        **metrics,
                    })

    return sorted(
        results,
        key=lambda row: (
            -row.get(f"ndcg@{k}", 0.0),
            -row.get(f"recall@{k}", 0.0),
            row["rating_threshold"],
            row["min_cooccurrence"],
            row["shrinkage"],
            row["strategy_code"],
        ),
    )
