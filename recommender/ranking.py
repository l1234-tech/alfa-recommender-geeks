"""Candidate filtering and ranking for content and collaborative strategies."""
from __future__ import annotations

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.content_baseline import score_item
from recommender.algorithms.hybrid import score_hybrid
from recommender.algorithms.tfidf import TfidfIndex
from recommender.explanations import explain
from recommender.models import CatalogItem, Recommendation, UserProfile


def recommend(
    profile: UserProfile,
    catalog: list[CatalogItem],
    limit: int = 10,
    *,
    strategy: str = "baseline",
    tfidf_index: TfidfIndex | None = None,
    collaborative_index: ItemItemIndex | None = None,
) -> list[Recommendation]:
    """Rank available unseen items using content and/or item-item CF."""
    strategies = {"baseline", "hybrid", "collaborative", "content_cf_hybrid"}
    if limit < 1:
        return []
    if strategy not in strategies:
        raise ValueError(f"strategy must be one of: {', '.join(sorted(strategies))}")
    if strategy in {"hybrid", "content_cf_hybrid"} and tfidf_index is None:
        tfidf_index = TfidfIndex.fit(catalog)
    if strategy in {"collaborative", "content_cf_hybrid"} and collaborative_index is None:
        raise ValueError("collaborative_index is required for collaborative strategies")

    def score(item: CatalogItem) -> float:
        if strategy == "baseline":
            return score_item(profile, item)
        if strategy == "hybrid":
            assert tfidf_index is not None
            return score_hybrid(profile, item, tfidf_index)
        assert collaborative_index is not None
        cf_score = collaborative_index.score(profile, item.item_id)
        if strategy == "collaborative":
            return cf_score
        assert tfidf_index is not None
        content_score = score_hybrid(profile, item, tfidf_index)
        # Cold-start fallback: if CF has no signal, retain content ranking.
        if cf_score <= 0:
            return content_score
        return 0.5 * content_score + 0.5 * cf_score

    candidates = [
        item for item in catalog
        if item.is_available
        and item.item_id not in profile.completed_item_ids
        and item.item_id not in profile.seen_item_ids
    ]
    ranked = sorted(candidates, key=lambda item: (-score(item), item.item_id))
    result: list[Recommendation] = []
    for item in ranked[:limit]:
        reason, next_step = explain(profile, item)
        result.append(Recommendation(
            item=item,
            score=round(score(item), 6),
            reason=reason,
            next_step=next_step,
        ))
    return result
