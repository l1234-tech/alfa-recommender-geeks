"""Compare metadata, TF-IDF hybrid and collaborative ranking on shared splits."""
from __future__ import annotations

from collections.abc import Iterable

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend


def compare_content_models(
    events: Iterable[UserInteraction],
    catalog: list[CatalogItem],
    *,
    k: int = 10,
) -> dict[str, dict[str, float]]:
    """Compare strategies on identical per-user temporal splits.

    Each split gets its own CF index fitted only on that split's training events,
    preventing future interactions from leaking into collaborative similarities.
    """
    event_rows = list(events)
    splits = temporal_holdout(event_rows)
    tfidf_index = TfidfIndex.fit(catalog)
    recommendations: dict[str, list[list[str]]] = {
        "metadata_baseline": [],
        "tfidf_hybrid": [],
        "item_item_cf": [],
        "content_cf_hybrid": [],
    }
    relevant_sets: list[set[str]] = []

    for split in splits:
        profile = build_user_profile(split.train_events, catalog)
        collaborative_index = ItemItemIndex.fit(split.collaborative_train_events, catalog)
        for strategy in recommendations:
            rows = recommend(
                profile,
                catalog,
                limit=k,
                strategy=strategy,
                tfidf_index=tfidf_index,
                collaborative_index=collaborative_index,
            )
            recommendations[strategy].append([row.item.item_id for row in rows])
        relevant_sets.append(set(split.test_relevant_item_ids))

    return {
        name: aggregate_ranking_metrics(rows, relevant_sets, k)
        for name, rows in recommendations.items()
    }
