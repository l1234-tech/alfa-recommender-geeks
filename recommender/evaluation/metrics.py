"""Ranking, catalog-coverage, and recommendation-diversity metrics."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Hashable

from recommender.algorithms.diversity import item_similarity
from recommender.models import CatalogItem

Item = Hashable


def precision_at_k(recommended: Sequence[Item], relevant: set[Item], k: int) -> float:
    if k <= 0:
        return 0.0
    return sum(item in relevant for item in recommended[:k]) / k


def recall_at_k(recommended: Sequence[Item], relevant: set[Item], k: int) -> float:
    if k <= 0 or not relevant:
        return 0.0
    return sum(item in relevant for item in recommended[:k]) / len(relevant)


def ndcg_at_k(recommended: Sequence[Item], relevant: set[Item], k: int) -> float:
    if k <= 0 or not relevant:
        return 0.0
    dcg = sum(
        1 / math.log2(rank + 2)
        for rank, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal = min(len(relevant), k)
    idcg = sum(1 / math.log2(rank + 2) for rank in range(ideal))
    return dcg / idcg if idcg else 0.0


def aggregate_ranking_metrics(
    recommendations: Iterable[Sequence[Item]],
    relevant_sets: Iterable[set[Item]],
    k: int = 10,
) -> dict[str, float]:
    pairs = list(zip(recommendations, relevant_sets))
    if not pairs:
        return {
            "users_evaluated": 0.0,
            f"precision@{k}": 0.0,
            f"recall@{k}": 0.0,
            f"ndcg@{k}": 0.0,
        }
    return {
        "users_evaluated": float(len(pairs)),
        f"precision@{k}": sum(precision_at_k(row, rel, k) for row, rel in pairs) / len(pairs),
        f"recall@{k}": sum(recall_at_k(row, rel, k) for row, rel in pairs) / len(pairs),
        f"ndcg@{k}": sum(ndcg_at_k(row, rel, k) for row, rel in pairs) / len(pairs),
    }


def catalog_coverage(
    recommendations: Iterable[Sequence[Item]],
    available_catalog: Iterable[Item],
) -> dict[str, float]:
    catalog = set(available_catalog)
    recommended = {item for row in recommendations for item in row if item in catalog}
    return {
        "available_items": float(len(catalog)),
        "recommended_unique_items": float(len(recommended)),
        "catalog_coverage": len(recommended) / len(catalog) if catalog else 0.0,
    }


def intra_list_diversity(items: Sequence[CatalogItem]) -> float:
    """Mean pairwise metadata dissimilarity; zero for lists shorter than two."""
    if len(items) < 2:
        return 0.0
    distances = [
        1.0 - item_similarity(items[i], items[j])
        for i in range(len(items))
        for j in range(i + 1, len(items))
    ]
    return sum(distances) / len(distances)


def aggregate_diversity_metrics(
    recommendations: Iterable[Sequence[Item]],
    catalog_by_key: dict[Item, CatalogItem],
) -> dict[str, float]:
    """Aggregate intra-list diversity and topic/type variety over recommendation lists."""
    rows = [
        [catalog_by_key[key] for key in recommendation if key in catalog_by_key]
        for recommendation in recommendations
    ]
    if not rows:
        return {
            "intra_list_diversity": 0.0,
            "avg_unique_topics_per_list": 0.0,
            "avg_unique_types_per_list": 0.0,
        }
    return {
        "intra_list_diversity": sum(intra_list_diversity(row) for row in rows) / len(rows),
        "avg_unique_topics_per_list": sum(
            len({topic.casefold() for item in row for topic in item.topics})
            for row in rows
        ) / len(rows),
        "avg_unique_types_per_list": sum(
            len({item.item_type.casefold() for item in row}) for row in rows
        ) / len(rows),
    }
