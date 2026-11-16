"""Aggregate-only diagnosis of temporal recommendation misses.

No user identifiers or item identifiers are returned. The module separates
catalog/data coverage failures from ranking failures.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend

_ALLOWED = {"baseline", "hybrid", "collaborative", "content_cf_hybrid"}
_CATEGORIES = (
    "recommended_in_top_k",
    "missing_from_catalog",
    "unavailable",
    "filtered_by_history",
    "ranked_below_k",
    "not_ranked",
)


def analyze_recommendation_errors(
    events: Iterable[UserInteraction],
    catalog: list[CatalogItem],
    *,
    k: int = 10,
    strategies: tuple[str, ...] = ("baseline", "hybrid"),
) -> dict[str, dict[str, float]]:
    """Classify held-out positive items and aggregate counts/rates per strategy.

    A relevant item is classified exactly once. Ranking is computed over the
    full eligible catalog so 'ranked_below_k' is distinguishable from a
    candidate that could not be ranked. Results contain aggregate numbers only.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if not strategies or any(name not in _ALLOWED for name in strategies):
        raise ValueError(f"strategies must be selected from: {', '.join(sorted(_ALLOWED))}")

    items = list(catalog)
    by_key = {item.key: item for item in items}
    if len(by_key) != len(items):
        raise ValueError("catalog contains duplicate typed item keys")
    splits = temporal_holdout(list(events))
    tfidf = TfidfIndex.fit(items)
    results: dict[str, dict[str, float]] = {}

    for strategy in strategies:
        counts: Counter[str] = Counter()
        total = 0
        for split in splits:
            profile = build_user_profile(split.train_events, items)
            cf_index = None
            if strategy in {"collaborative", "content_cf_hybrid"}:
                cf_index = ItemItemIndex.fit(split.collaborative_train_events, items)
            ranked = recommend(
                profile,
                items,
                limit=max(1, len(items)),
                strategy=strategy,
                tfidf_index=tfidf,
                collaborative_index=cf_index,
            )
            positions = {row.item.key: index for index, row in enumerate(ranked, start=1)}

            for key in split.test_relevant_item_keys:
                total += 1
                item = by_key.get(key)
                if item is None:
                    counts["missing_from_catalog"] += 1
                elif not item.is_available:
                    counts["unavailable"] += 1
                elif key in profile.seen_item_keys or key in profile.completed_item_keys:
                    counts["filtered_by_history"] += 1
                elif key in positions and positions[key] <= k:
                    counts["recommended_in_top_k"] += 1
                elif key in positions:
                    counts["ranked_below_k"] += 1
                else:
                    counts["not_ranked"] += 1

        row: dict[str, float] = {"relevant_items": float(total)}
        for category in _CATEGORIES:
            count = counts[category]
            row[category] = float(count)
            row[f"{category}_rate"] = count / total if total else 0.0
        row[f"hit_rate@{k}"] = counts["recommended_in_top_k"] / total if total else 0.0
        row[f"miss_rate@{k}"] = 1.0 - row[f"hit_rate@{k}"] if total else 0.0
        results[strategy] = row

    return results
