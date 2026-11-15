"""Compare recommendation strategies and MMR weights on shared temporal splits."""
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


def compare_content_models(
    events: Iterable[UserInteraction],
    catalog: list[CatalogItem],
    *,
    k: int = 10,
    diversity_weights: Sequence[float] = (0.15, 0.25, 0.35),
) -> dict[str, dict[str, float]]:
    """Compare four base strategies and content+CF MMR variants.

    Every variant uses identical per-user temporal validation splits.
    MMR weights are evaluation candidates, not preselected best values.
    """
    if any(not 0.0 <= weight <= 1.0 for weight in diversity_weights):
        raise ValueError("all diversity_weights must be between 0 and 1")

    rows = list(events)
    splits = temporal_holdout(rows)
    tfidf = TfidfIndex.fit(catalog)
    base_names = ("metadata_baseline", "tfidf_hybrid", "item_item_cf", "content_cf_hybrid")
    mmr_names = tuple(f"content_cf_hybrid_mmr_{weight:.2f}" for weight in diversity_weights)
    names = base_names + mmr_names
    outputs: dict[str, list[list[tuple[str, str]]]] = {name: [] for name in names}
    relevant: list[set[tuple[str, str]]] = []

    event_types = sorted({
        event.event_type
        for split in splits
        for event in split.test_positive_events
    })
    type_relevant = {event_type: [] for event_type in event_types}

    for split in splits:
        profile = build_user_profile(split.train_events, catalog)
        cf = ItemItemIndex.fit(split.collaborative_train_events, catalog)

        strategies = {
            "metadata_baseline": ("baseline", 0.0),
            "tfidf_hybrid": ("hybrid", 0.0),
            "item_item_cf": ("collaborative", 0.0),
            "content_cf_hybrid": ("content_cf_hybrid", 0.0),
        }
        for weight, name in zip(diversity_weights, mmr_names):
            strategies[name] = ("content_cf_hybrid", weight)

        for name, (strategy, diversity_weight) in strategies.items():
            recs = recommend(
                profile,
                catalog,
                limit=k,
                strategy=strategy,
                tfidf_index=tfidf,
                collaborative_index=cf,
                diversity_weight=diversity_weight,
            )
            outputs[name].append([rec.item.key for rec in recs])

        relevant.append(set(split.test_relevant_item_keys))
        for event_type in event_types:
            type_relevant[event_type].append({
                event.item_key
                for event in split.test_positive_events
                if event.event_type == event_type
            })

    available = {item.key for item in catalog if item.is_available}
    catalog_by_key = {item.key: item for item in catalog}
    result: dict[str, dict[str, float]] = {}

    for strategy, predictions in outputs.items():
        metrics = aggregate_ranking_metrics(predictions, relevant, k)
        metrics.update(catalog_coverage(predictions, available))
        metrics.update(aggregate_diversity_metrics(predictions, catalog_by_key))
        for event_type, sets in type_relevant.items():
            paired = [(pred, rel) for pred, rel in zip(predictions, sets) if rel]
            if paired:
                sliced = aggregate_ranking_metrics(
                    [prediction for prediction, _ in paired],
                    [relevance for _, relevance in paired],
                    k,
                )
                metrics.update({
                    f"{event_type}_{name}": value
                    for name, value in sliced.items()
                })
            else:
                metrics[f"{event_type}_users_evaluated"] = 0.0
        result[strategy] = metrics
    return result
