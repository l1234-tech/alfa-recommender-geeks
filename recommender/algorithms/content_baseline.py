"""Transparent metadata-overlap baseline with missing-field-aware scoring."""
from __future__ import annotations

import re

from recommender.models import CatalogItem, UserProfile

TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _tokens(value: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(value) if len(token) > 2}


def _overlap(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union)


def score_item(profile: UserProfile, item: CatalogItem) -> float:
    """Average only comparable fields; absent metadata is not a mismatch.

    The result remains in [0, 1]. A profile field contributes only when both
    the profile and candidate have values for that field.
    """
    components: list[float] = []
    for profile_values, item_values in (
        (profile.topics, item.topics),
        (profile.tags, item.tags),
        (profile.industries, item.industries),
    ):
        if profile_values and item_values:
            components.append(_overlap(profile_values, item_values))

    if profile.preferred_types:
        components.append(float(item.item_type.casefold() in {
            value.casefold() for value in profile.preferred_types
        }))

    if profile.current_goal.strip():
        goal_tokens = _tokens(profile.current_goal)
        text_tokens = _tokens(item.title + " " + item.description)
        if goal_tokens and text_tokens:
            components.append(len(goal_tokens & text_tokens) / len(goal_tokens))

    return sum(components) / len(components) if components else 0.0
