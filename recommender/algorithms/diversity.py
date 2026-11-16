"""Maximal Marginal Relevance reranking for recommendation diversity."""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from recommender.models import CatalogItem

_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def item_features(item: CatalogItem) -> frozenset[str]:
    """Build a lightweight feature set from public catalog metadata."""
    values = (item.title, item.description, *item.topics, *item.tags, *item.industries)
    tokens = {
        token.casefold()
        for value in values
        for token in _TOKEN_RE.findall(value)
        if len(token) > 2
    }
    tokens.add(f"type:{item.item_type.casefold()}")
    tokens.update(f"topic:{value.casefold()}" for value in item.topics)
    tokens.update(f"tag:{value.casefold()}" for value in item.tags)
    tokens.update(f"industry:{value.casefold()}" for value in item.industries)
    return frozenset(tokens)


def item_similarity(left: CatalogItem, right: CatalogItem) -> float:
    """Return Jaccard similarity of metadata features in [0, 1]."""
    left_features = item_features(left)
    right_features = item_features(right)
    if not left_features or not right_features:
        return 0.0
    return len(left_features & right_features) / len(left_features | right_features)


def mmr_rerank(
    items: Sequence[CatalogItem],
    relevance: Callable[[CatalogItem], float],
    *,
    limit: int,
    diversity_weight: float = 0.25,
) -> list[CatalogItem]:
    """Greedily select relevant items while penalizing similarity to selections.

    MMR = (1 - diversity_weight) * relevance
          - diversity_weight * max_similarity_to_selected.
    """
    if not 0.0 <= diversity_weight <= 1.0:
        raise ValueError("diversity_weight must be between 0 and 1")
    if limit <= 0 or not items:
        return []

    remaining = list(items)
    selected: list[CatalogItem] = []
    scores = {item.key: max(0.0, min(1.0, relevance(item))) for item in remaining}

    while remaining and len(selected) < limit:
        def mmr_score(candidate: CatalogItem) -> float:
            redundancy = max(
                (item_similarity(candidate, chosen) for chosen in selected),
                default=0.0,
            )
            return (1.0 - diversity_weight) * scores[candidate.key] - diversity_weight * redundancy

        best = min(remaining, key=lambda item: (-mmr_score(item), item.key))
        selected.append(best)
        remaining.remove(best)

    return selected
