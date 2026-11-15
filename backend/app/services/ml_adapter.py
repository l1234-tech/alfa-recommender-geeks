"""Adapter between the API layer and the recommender engine.

Primary path calls the team's `recommender.ranking.recommend` over an in-memory
catalog (no database needed). If the recommender package cannot be imported, a
small built-in overlap scorer with equivalent behaviour keeps the API working.
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from ..schemas.recommendation import HistoryEvent, UserProfileIn
from .sample_catalog import Material

_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def ensure_recommender_on_path() -> None:
    """Add the repo root (which contains the `recommender` package) to sys.path.

    Works both in the mounted dev layout and when `recommender` is mounted at
    `/recommender` in Docker.
    """
    here = Path(__file__).resolve()
    candidates = [here.parents[3], Path("/"), Path("/app")]
    for root in candidates:
        if (root / "recommender").is_dir() and str(root) not in sys.path:
            sys.path.insert(0, str(root))


try:
    ensure_recommender_on_path()
    from recommender.models import CatalogItem, UserProfile
    from recommender.ranking import recommend as _engine_recommend

    RECOMMENDER_AVAILABLE = True
except Exception:  # pragma: no cover - fallback path exercised via env flag
    RECOMMENDER_AVAILABLE = False


@dataclass(frozen=True)
class Ranked:
    material: Material
    score: float
    reasons: list[str]
    next_step: str


def _tokens(value: str) -> set[str]:
    return {t.casefold() for t in _TOKEN_RE.findall(value) if len(t) > 2}


def build_profile_fields(profile: UserProfileIn, history: list[HistoryEvent]) -> dict:
    """Map the API profile onto the engine's source-independent profile fields."""
    topics: set[str] = set()
    tags: set[str] = set()
    industries: set[str] = set()

    if profile.current_goal:
        topics.add(profile.current_goal.strip().casefold())
    if profile.industry:
        industries.add(profile.industry.strip().casefold())
    if profile.business_stage:
        tags.add(profile.business_stage.strip().casefold())
    if profile.experience_level:
        tags.add(profile.experience_level.strip().casefold())

    seen = {e.material_id for e in history}
    return {
        "topics": topics,
        "tags": tags,
        "industries": industries,
        "current_goal": (profile.current_goal or "").strip(),
        "preferred_types": {f.strip().casefold() for f in profile.preferred_formats},
        "seen_item_ids": seen,
    }


def rank(
    materials: list[Material],
    fields: dict,
    limit: int,
    strategy: str,
    *,
    force_builtin: bool = False,
) -> list[Ranked]:
    if RECOMMENDER_AVAILABLE and not force_builtin:
        try:
            return _rank_with_engine(materials, fields, limit, strategy)
        except Exception:
            # Never fail the request on an engine runtime error: degrade to the
            # transparent built-in scorer with the same response shape.
            logging.getLogger(__name__).exception("ML engine failed; using built-in scorer")
    return _rank_builtin(materials, fields, limit)


def _rank_with_engine(materials, fields, limit, strategy) -> list[Ranked]:
    by_id = {m.material_id: m for m in materials}
    catalog = [
        CatalogItem(
            item_id=m.material_id,
            item_type=m.material_type,
            title=m.title,
            description=m.description,
            topics=m.topics,
            tags=m.tags,
            industries=m.industries,
            is_available=m.is_available,
            url=m.url,
        )
        for m in materials
    ]
    # The engine suppresses items by typed (item_type, item_id) keys, so map the
    # history ids to keys using the catalog; ids absent from the catalog cannot
    # match any item and are skipped.
    seen_keys = frozenset(
        (by_id[mid].material_type.casefold(), mid)
        for mid in fields["seen_item_ids"]
        if mid in by_id
    )
    profile = UserProfile(
        topics=frozenset(fields["topics"]),
        tags=frozenset(fields["tags"]),
        industries=frozenset(fields["industries"]),
        current_goal=fields["current_goal"],
        preferred_types=frozenset(fields["preferred_types"]),
        seen_item_keys=seen_keys,
    )
    # We do not build a collaborative index here, so only content strategies are
    # passed to the engine; anything else degrades to the transparent baseline.
    engine_strategy = strategy if strategy in {"baseline", "hybrid"} else "baseline"
    results = _engine_recommend(profile, catalog, limit=limit, strategy=engine_strategy)
    return [
        Ranked(
            material=by_id[r.item.item_id],
            score=r.score,
            reasons=[part.strip() for part in r.reason.split(";") if part.strip()] or [r.reason],
            next_step=r.next_step,
        )
        for r in results
    ]


def _overlap(left: set[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _rank_builtin(materials, fields, limit) -> list[Ranked]:
    """Transparent metadata-overlap scorer mirroring the engine baseline."""
    goal_tokens = _tokens(fields["current_goal"])
    scored: list[Ranked] = []
    for m in materials:
        if m.material_id in fields["seen_item_ids"] or not m.is_available:
            continue
        parts = [
            _overlap(fields["topics"], m.topics),
            _overlap(fields["tags"], m.tags),
            _overlap(fields["industries"], m.industries),
        ]
        if fields["preferred_types"]:
            parts.append(float(m.material_type.casefold() in fields["preferred_types"]))
        if goal_tokens:
            text = _tokens(m.title + " " + m.description)
            parts.append(len(goal_tokens & text) / len(goal_tokens))
        score = sum(parts) / len(parts) if parts else 0.0

        reasons = _builtin_reasons(fields, goal_tokens, m)
        scored.append(Ranked(
            material=m,
            score=round(score, 6),
            reasons=reasons,
            next_step=_builtin_next_step(m),
        ))
    scored.sort(key=lambda r: (-r.score, r.material.material_id))
    return scored[:limit]


def _builtin_reasons(fields, goal_tokens, m: Material) -> list[str]:
    reasons: list[str] = []
    if fields["topics"] & m.topics:
        reasons.append("совпадают выбранные темы")
    if fields["industries"] & m.industries:
        reasons.append("материал связан с вашей отраслью")
    if fields["tags"] & m.tags:
        reasons.append("подходит под вашу стадию и опыт")
    if goal_tokens & _tokens(m.title + " " + m.description):
        reasons.append("связан с вашей текущей задачей")
    if fields["preferred_types"] and m.material_type.casefold() in fields["preferred_types"]:
        reasons.append("подходит предпочитаемый формат")
    return reasons[:2] or ["материал доступен и расширит подборку по выбранному направлению"]


def _builtin_next_step(m: Material) -> str:
    if m.material_type == "webinar":
        return "Проверить дату вебинара и зарегистрироваться, если время подходит."
    if m.material_type == "course":
        return "Посмотреть программу курса и оценить требуемое время на обучение."
    return "Открыть описание и проверить, подходит ли материал для вашей задачи."
