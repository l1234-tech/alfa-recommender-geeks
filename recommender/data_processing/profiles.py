"""Build privacy-preserving in-memory preference profiles from past events."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone

from recommender.data_processing.interactions import UserInteraction
from recommender.models import CatalogItem, UserProfile


def is_positive_event(event: UserInteraction, positive_rating_threshold: int = 4) -> bool:
    """Only explicit high ratings and confirmed completion count as positive."""
    if event.event_type == "rating":
        return event.rating_value is not None and event.rating_value >= positive_rating_threshold
    if event.event_type == "lesson_progress":
        return event.is_completed is True
    if event.event_type == "course_binding":
        return event.is_completed is True
    return False


def _utc_sort_value(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_user_profile(
    events: Iterable[UserInteraction],
    catalog: Iterable[CatalogItem],
    *,
    onboarding: UserProfile | None = None,
    positive_rating_threshold: int = 4,
) -> UserProfile:
    """Aggregate only positive historical events; IDs remain in memory only."""
    base = onboarding or UserProfile()
    by_key: dict[tuple[str, str], CatalogItem] = {
        (item.item_type, item.item_id): item for item in catalog
    }
    positive_items: list[CatalogItem] = []
    seen_ids: set[str] = set()
    completed_ids: set[str] = set()
    positive_ids: set[str] = set()
    type_counts: Counter[str] = Counter()

    for event in events:
        seen_ids.add(event.item_id)
        if event.is_completed is True:
            completed_ids.add(event.item_id)
        if is_positive_event(event, positive_rating_threshold):
            positive_ids.add(event.item_id)
            item = by_key.get((event.item_type, event.item_id))
            if item is not None and item.is_available:
                positive_items.append(item)
                type_counts[item.item_type] += 1

    topics = set(base.topics)
    tags = set(base.tags)
    industries = set(base.industries)
    for item in positive_items:
        topics.update(item.topics)
        tags.update(item.tags)
        industries.update(item.industries)

    preferred_types = set(base.preferred_types)
    if type_counts:
        preferred_types.update(type_counts.keys())

    return UserProfile(
        topics=frozenset(topics),
        tags=frozenset(tags),
        industries=frozenset(industries),
        current_goal=base.current_goal,
        preferred_types=frozenset(preferred_types),
        completed_item_ids=frozenset(set(base.completed_item_ids) | completed_ids),
        seen_item_ids=frozenset(set(base.seen_item_ids) | seen_ids),
        positive_item_ids=frozenset(set(base.positive_item_ids) | positive_ids),
    )


def group_events_by_user(events: Iterable[UserInteraction]) -> dict[str, list[UserInteraction]]:
    """Group events for internal processing; never serialize raw user keys."""
    grouped: dict[str, list[UserInteraction]] = {}
    for event in events:
        grouped.setdefault(event.user_id, []).append(event)
    for user_events in grouped.values():
        user_events.sort(key=lambda event: _utc_sort_value(event.event_at))
    return grouped
