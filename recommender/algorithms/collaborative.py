"""Privacy-conscious item-item collaborative filtering.

The index stores item co-occurrence statistics only; raw user identifiers are
used transiently while fitting and are never retained in the fitted model.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from math import sqrt

from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import is_positive_event
from recommender.models import CatalogItem, UserProfile


class ItemItemIndex:
    """Cosine item-item similarity from users' positive interaction history."""

    def __init__(
        self,
        similarities: dict[str, dict[str, float]],
        support: dict[str, int],
    ) -> None:
        self._similarities = similarities
        self._support = support

    @classmethod
    def fit(
        cls,
        events: Iterable[UserInteraction],
        catalog: Iterable[CatalogItem],
        *,
        positive_rating_threshold: int = 4,
        min_cooccurrence: int = 2,
        shrinkage: float = 5.0,
    ) -> "ItemItemIndex":
        if min_cooccurrence < 1:
            raise ValueError("min_cooccurrence must be at least 1")
        if shrinkage < 0:
            raise ValueError("shrinkage must be non-negative")

        valid_items = {
            item.item_id for item in catalog if item.is_available
        }
        user_items: dict[str, set[str]] = defaultdict(set)
        for event in events:
            if (
                event.item_id in valid_items
                and is_positive_event(event, positive_rating_threshold)
            ):
                user_items[event.user_id].add(event.item_id)

        item_users: dict[str, set[str]] = defaultdict(set)
        for user_id, item_ids in user_items.items():
            for item_id in item_ids:
                item_users[item_id].add(user_id)

        support = {item_id: len(users) for item_id, users in item_users.items()}
        co_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for item_ids in user_items.values():
            ordered = sorted(item_ids)
            for index, left in enumerate(ordered):
                for right in ordered[index + 1:]:
                    co_counts[left][right] += 1
                    co_counts[right][left] += 1

        similarities: dict[str, dict[str, float]] = defaultdict(dict)
        for left, neighbors in co_counts.items():
            for right, count in neighbors.items():
                if count < min_cooccurrence:
                    continue
                denominator = sqrt(support[left] * support[right])
                cosine = count / denominator if denominator else 0.0
                # Significance weighting reduces noisy similarities from tiny samples.
                similarities[left][right] = cosine * count / (count + shrinkage)
        return cls(dict(similarities), support)

    def score(self, profile: UserProfile, candidate_item_id: str) -> float:
        """Score a candidate from the user's known positive items."""
        history = profile.positive_item_ids
        if not history:
            return 0.0
        values = [
            self._similarities.get(source, {}).get(candidate_item_id, 0.0)
            for source in history
            if source != candidate_item_id
        ]
        # Normalize by history size so long histories do not dominate.
        return sum(values) / len(history)

    def has_neighbors(self, item_id: str) -> bool:
        return bool(self._similarities.get(item_id))

    @property
    def item_count(self) -> int:
        return len(self._support)
