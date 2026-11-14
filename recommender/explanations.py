"""Human-readable explanations grounded in actual profile-item matches."""
from __future__ import annotations

import re

from recommender.models import CatalogItem, UserProfile


TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in TOKEN_RE.findall(value)
        if len(token) > 2
    }


def explain(profile: UserProfile, item: CatalogItem) -> tuple[str, str]:
    matches: list[str] = []
    if profile.topics & item.topics:
        matches.append("совпадают выбранные темы")
    if profile.tags & item.tags:
        matches.append("совпадают интересующие теги")
    if profile.industries & item.industries:
        matches.append("материал связан с вашей отраслью")

    goal_tokens = _tokens(profile.current_goal)
    item_tokens = _tokens(item.title + " " + item.description)
    if goal_tokens & item_tokens:
        matches.append("название или описание связано с вашей текущей задачей")

    if profile.preferred_types and item.item_type.casefold() in {
        value.casefold() for value in profile.preferred_types
    }:
        matches.append("подходит предпочитаемый тип материала")

    reason = "; ".join(matches[:2]) if matches else (
        "материал доступен и может расширить подборку по выбранному направлению"
    )
    next_step = "Открыть описание и проверить, подходит ли материал для вашей задачи."
    if item.item_type.casefold() == "webinar":
        next_step = "Проверить дату вебинара и зарегистрироваться, если время подходит."
    elif item.item_type.casefold() == "course":
        next_step = "Посмотреть программу курса и оценить требуемое время на обучение."
    return reason, next_step
