"""Typed, source-independent contracts for the recommendation MVP."""
from __future__ import annotations
from dataclasses import dataclass, field

ItemKey = tuple[str, str]


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
    is_paid: bool | None = None

    @property
    def key(self) -> ItemKey:
        return (self.item_type.casefold(), self.item_id)


@dataclass(frozen=True)
class UserProfile:
    topics: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    industries: frozenset[str] = field(default_factory=frozenset)
    current_goal: str = ""
    preferred_types: frozenset[str] = field(default_factory=frozenset)
    completed_item_keys: frozenset[ItemKey] = field(default_factory=frozenset)
    seen_item_keys: frozenset[ItemKey] = field(default_factory=frozenset)
    positive_item_keys: frozenset[ItemKey] = field(default_factory=frozenset)
    # Explicit feedback strength per typed item key; omitted keys default to 1.0.
    positive_item_weights: tuple[tuple[ItemKey, float], ...] = ()


@dataclass(frozen=True)
class Recommendation:
    item: CatalogItem
    score: float
    reason: str
    next_step: str
