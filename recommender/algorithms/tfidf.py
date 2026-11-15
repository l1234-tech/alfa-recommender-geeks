"""Field-aware, dependency-free TF-IDF over public catalog metadata."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from recommender.models import CatalogItem, ItemKey, UserProfile

TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
STOP_WORDS = frozenset({
    "для", "это", "как", "что", "или", "при", "над", "под", "без",
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
})


def tokenize(text: str) -> list[str]:
    """Normalize tokens consistently for Russian/English text."""
    return [
        token.casefold()
        for token in TOKEN_RE.findall(text)
        if len(token) > 2 and token.casefold() not in STOP_WORDS
    ]


def profile_query(profile: UserProfile) -> str:
    # Structured onboarding fields are explicit interests; repeat them once
    # to give them more influence than the free-text goal.
    structured = [
        *sorted(profile.topics), *sorted(profile.topics),
        *sorted(profile.tags), *sorted(profile.tags),
        *sorted(profile.industries), *sorted(profile.industries),
        *sorted(profile.preferred_types),
    ]
    return " ".join(value for value in (*structured, profile.current_goal) if value)


def _item_text(item: CatalogItem) -> str:
    # Title is the most concise editorial signal, so it receives a modest
    # 2x term-frequency boost. No closed body/content fields are used.
    return " ".join((
        item.title, item.title, item.description,
        *sorted(item.topics), *sorted(item.tags), *sorted(item.industries),
        item.item_type,
    ))


@dataclass(frozen=True)
class TfidfIndex:
    item_keys: tuple[ItemKey, ...]
    vectors: dict[ItemKey, dict[str, float]]
    norms: dict[ItemKey, float]
    idf: dict[str, float]

    @classmethod
    def fit(cls, catalog: Iterable[CatalogItem]) -> "TfidfIndex":
        items = list(catalog)
        keys = [item.key for item in items]
        if len(keys) != len(set(keys)):
            raise ValueError("catalog contains duplicate typed item keys")

        document_frequencies: Counter[str] = Counter()
        tokenized: dict[ItemKey, Counter[str]] = {}
        for item in items:
            counts = Counter(tokenize(_item_text(item)))
            tokenized[item.key] = counts
            document_frequencies.update(counts.keys())

        total = len(items)
        idf = {
            token: math.log((total + 1) / (frequency + 1)) + 1
            for token, frequency in document_frequencies.items()
        }
        vectors: dict[ItemKey, dict[str, float]] = {}
        norms: dict[ItemKey, float] = {}
        for key, counts in tokenized.items():
            vector = {
                token: (1 + math.log(count)) * idf[token]
                for token, count in counts.items()
            }
            vectors[key] = vector
            norms[key] = math.sqrt(sum(value * value for value in vector.values()))
        return cls(tuple(keys), vectors, norms, idf)

    def score(self, profile: UserProfile, item: CatalogItem | ItemKey) -> float:
        key = item.key if isinstance(item, CatalogItem) else item
        counts = Counter(tokenize(profile_query(profile)))
        if not counts:
            return 0.0
        query = {
            token: (1 + math.log(count)) * self.idf[token]
            for token, count in counts.items()
            if token in self.idf
        }
        vector = self.vectors.get(key, {})
        query_norm = math.sqrt(sum(value * value for value in query.values()))
        item_norm = self.norms.get(key, 0.0)
        if not query_norm or not item_norm:
            return 0.0
        dot = sum(value * vector.get(token, 0.0) for token, value in query.items())
        return max(0.0, min(1.0, dot / (query_norm * item_norm)))
