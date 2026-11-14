"""Build privacy-preserving in-memory preference profiles from past events."""
from __future__ import annotations
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from recommender.data_processing.interactions import UserInteraction
from recommender.models import CatalogItem, ItemKey, UserProfile
def is_positive_event(event: UserInteraction, positive_rating_threshold: int = 4) -> bool:
    if event.event_type == "rating":
        return event.rating_value is not None and event.rating_value >= positive_rating_threshold
    if event.event_type in {"lesson_progress", "course_binding"}:
        return event.is_completed is True
    return False
def _utc_sort_value(value: datetime | None) -> datetime:
    if value is None: return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None: return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
def build_user_profile(events: Iterable[UserInteraction], catalog: Iterable[CatalogItem], *,
                       onboarding: UserProfile | None = None,
                       positive_rating_threshold: int = 4) -> UserProfile:
    base = onboarding or UserProfile()
    by_key: dict[ItemKey, CatalogItem] = {item.key:item for item in catalog}
    positive_items=[]; seen=set(); completed=set(); positive=set(); type_counts=Counter()
    for event in events:
        seen.add(event.item_key)
        if event.is_completed is True: completed.add(event.item_key)
        if is_positive_event(event, positive_rating_threshold):
            positive.add(event.item_key)
            item=by_key.get(event.item_key)
            if item is not None and item.is_available:
                positive_items.append(item); type_counts[item.item_type]+=1
    topics=set(base.topics); tags=set(base.tags); industries=set(base.industries)
    for item in positive_items:
        topics.update(item.topics); tags.update(item.tags); industries.update(item.industries)
    preferred=set(base.preferred_types)
    if type_counts: preferred.update(type_counts.keys())
    return UserProfile(topics=frozenset(topics), tags=frozenset(tags), industries=frozenset(industries),
        current_goal=base.current_goal, preferred_types=frozenset(preferred),
        completed_item_keys=frozenset(set(base.completed_item_keys)|completed),
        seen_item_keys=frozenset(set(base.seen_item_keys)|seen),
        positive_item_keys=frozenset(set(base.positive_item_keys)|positive))
def group_events_by_user(events: Iterable[UserInteraction]) -> dict[str,list[UserInteraction]]:
    grouped={}
    for event in events: grouped.setdefault(event.user_id,[]).append(event)
    for rows in grouped.values(): rows.sort(key=lambda e:_utc_sort_value(e.event_at))
    return grouped
