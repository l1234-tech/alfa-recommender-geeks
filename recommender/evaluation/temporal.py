"""Per-user temporal holdout without exposing user identifiers in reports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import is_positive_event


@dataclass(frozen=True)
class UserTemporalSplit:
    train_events: tuple[UserInteraction, ...]
    test_relevant_item_ids: frozenset[str]
    collaborative_train_events: tuple[UserInteraction, ...] = ()


def _utc_sort_value(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def temporal_holdout(
    events: Iterable[UserInteraction],
    *,
    positive_rating_threshold: int = 4,
    holdout_fraction: float = 0.2,
    min_train_events: int = 1,
) -> list[UserTemporalSplit]:
    """Hold out each user's latest events and expose a leakage-safe CF train set.

    The target user's profile uses only their own train_events. The CF index may
    use events from all users strictly earlier than that user's test boundary.
    """
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between 0 and 1")
    all_events = list(events)
    grouped: dict[str, list[UserInteraction]] = {}
    for event in all_events:
        grouped.setdefault(event.user_id, []).append(event)

    splits: list[UserTemporalSplit] = []
    for user_events in grouped.values():
        ordered = sorted(user_events, key=lambda event: _utc_sort_value(event.event_at))
        if len(ordered) <= min_train_events:
            continue
        holdout_size = max(1, math_ceil(len(ordered) * holdout_fraction))
        holdout_size = min(holdout_size, len(ordered) - min_train_events)
        train = ordered[:-holdout_size]
        test = ordered[-holdout_size:]
        train_item_ids = {event.item_id for event in train}
        relevant = frozenset(
            event.item_id for event in test
            if is_positive_event(event, positive_rating_threshold)
            and event.item_id not in train_item_ids
        )
        if not relevant:
            continue
        test_boundary = min(_utc_sort_value(event.event_at) for event in test)
        collaborative_train = tuple(
            event for event in all_events
            if _utc_sort_value(event.event_at) < test_boundary
        )
        splits.append(UserTemporalSplit(
            tuple(train), relevant, collaborative_train
        ))
    return splits


def math_ceil(value: float) -> int:
    integer = int(value)
    return integer if integer == value else integer + 1
