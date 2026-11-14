"""Dependency-free TF-IDF retrieval over public catalog metadata."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from recommender.models import CatalogItem, UserProfile


TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
STOP_WORDS = frozenset({
    "для", "это", "как", "что", "или", "при", "над", "под", "без",
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
})


def tokenize(text: str) -> list[str]:
    return [
        token.casefold()
        for token in TOKEN_RE.findall(text)
        if len(token) > 2 and token.casefold() not in STOP_WORDS
    ]


def profile_query(profile: UserProfile) -> str:
    """Convert explicit profile preferences to a query; no raw user IDs."""
    values = [
        *sorted(profile.topics),
        *sorted(profile.tags),
        *sorted(profile.industries),
        *sorted(profile.preferred_types),
        profile.current_goal,
    ]
    return " ".join(value for value in values if value)


@dataclass(frozen=True)
class TfidfIndex:
    item_ids: tuple[str, ...]
    vectors: dict[str, dict[str, float]]
    norms: dict[str, float]
    idf: dict[str, float]

    @classmethod
    def fit(cls, catalog: Iterable[CatalogItem]) -> "TfidfIndex":
        items = list(catalog)
        document_frequencies: Counter[str] = Counter()
        tokenized: dict[str, Counter[str]] = {}
        for item in items:
            text = " ".join((item.title, item.description, *item.topics, *item.tags, *item.industries))
            counts = Counter(tokenize(text))
            tokenized[item.item_id] = counts
            document_frequencies.update(counts.keys())

        total = max(len(items), 1)
        idf = {
            token: math.log((total + 1) / (frequency + 1)) + 1.0
            for token, frequency in document_frequencies.items()
        }
        vectors: dict[str, dict[str, float]] = {}
        norms: dict[str, float] = {}
        for item_id, counts in tokenized.items():
            vector = {token: (1.0 + math.log(count)) * idf[token] for token, count in counts.items()}
            norm = math.sqrt(sum(value * value for value in vector.values()))
            vectors[item_id] = vector
            norms[item_id] = norm
        return cls(
            item_ids=tuple(item.item_id for item in items),
            vectors=vectors,
            norms=norms,
            idf=idf,
        )

    def score(self, profile: UserProfile, item_id: str) -> float:
        query_counts = Counter(tokenize(profile_query(profile)))
        if not query_counts:
            return 0.0
        query = {
            token: (1.0 + math.log(count)) * self.idf[token]
            for token, count in query_counts.items()
            if token in self.idf
        }
        item_vector = self.vectors.get(item_id, {})
        query_norm = math.sqrt(sum(value * value for value in query.values()))
        item_norm = self.norms.get(item_id, 0.0)
        if not query_norm or not item_norm:
            return 0.0
        dot = sum(value * item_vector.get(token, 0.0) for token, value in query.items())
        return max(0.0, min(1.0, dot / (query_norm * item_norm)))
