"""Transparent metadata-overlap baseline; intentionally no learned weights."""
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
    """Return a [0, 1] score from explicit profile-to-metadata overlap.

    Equal weights are a deliberately simple starting baseline, not tuned
    production parameters. Missing profile fields contribute zero.
    """
    components = [
        _overlap(profile.topics, item.topics),
        _overlap(profile.tags, item.tags),
        _overlap(profile.industries, item.industries),
    ]
    if profile.preferred_types:
        components.append(float(item.item_type.casefold() in {
            value.casefold() for value in profile.preferred_types
        }))
    if profile.current_goal.strip():
        goal_tokens = _tokens(profile.current_goal)
        text_tokens = _tokens(item.title + " " + item.description)
        components.append(len(goal_tokens & text_tokens) / len(goal_tokens) if goal_tokens else 0.0)
    return sum(components) / len(components) if components else 0.0
