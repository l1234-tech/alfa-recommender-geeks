"""Ranking metrics for offline recommendation evaluation."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def precision_at_k(recommended: Sequence[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = list(recommended[:k])
    return sum(item in relevant for item in top_k) / k


def recall_at_k(recommended: Sequence[str], relevant: set[str], k: int) -> float:
    if k <= 0 or not relevant:
        return 0.0
    return sum(item in relevant for item in recommended[:k]) / len(relevant)


def ndcg_at_k(recommended: Sequence[str], relevant: set[str], k: int) -> float:
    if k <= 0 or not relevant:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def aggregate_ranking_metrics(
    recommendations: Iterable[Sequence[str]],
    relevant_sets: Iterable[set[str]],
    k: int = 10,
) -> dict[str, float]:
    pairs = list(zip(recommendations, relevant_sets))
    if not pairs:
        return {"users_evaluated": 0.0, f"precision@{k}": 0.0,
                f"recall@{k}": 0.0, f"ndcg@{k}": 0.0}
    return {
        "users_evaluated": float(len(pairs)),
        f"precision@{k}": sum(precision_at_k(r, rel, k) for r, rel in pairs) / len(pairs),
        f"recall@{k}": sum(recall_at_k(r, rel, k) for r, rel in pairs) / len(pairs),
        f"ndcg@{k}": sum(ndcg_at_k(r, rel, k) for r, rel in pairs) / len(pairs),
    }
