"""Typed, source-independent contracts for the recommendation MVP."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CatalogItem:
    item_id: str
    item_type: str
    title: str
    description: str = ""
    topics: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    industries: frozenset[str] = field(default_factory=frozenset)
    is_available: bool = True
    url: str | None = None


@dataclass(frozen=True)
class UserProfile:
    topics: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    industries: frozenset[str] = field(default_factory=frozenset)
    current_goal: str = ""
    preferred_types: frozenset[str] = field(default_factory=frozenset)
    completed_item_ids: frozenset[str] = field(default_factory=frozenset)
    seen_item_ids: frozenset[str] = field(default_factory=frozenset)
    positive_item_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Recommendation:
    item: CatalogItem
    score: float
    reason: str
    next_step: str
