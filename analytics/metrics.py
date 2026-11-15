"""Метрики качества рекомендаций.

Релевантность считается по ожиданиям, которые записаны в тестовом профиле
(какие темы/уровни/форматы ему подходят). Это экспертная разметка, а не
реальные клики — для хакатона другого способа нет, в docs/experiments.md
это оговорено.
"""
import math

from analytics.config import SHORT_DURATION_MIN, SHORT_FORMATS


def _fits(value, allowed):
    return not allowed or value in allowed


def _fits_or_unknown(value, allowed):
    # у большинства материалов уровень и стадия не размечены — незнание не штрафуем
    return not allowed or not value or value in allowed


def relevance(item, expected, seen_ids=()):
    """0 — не подходит, 1 — подходит по теме и уровню, 2 — ещё и по формату/стадии."""
    if item is None or item["material_id"] in seen_ids:
        return 0
    themes = expected.get("themes")
    if themes and not set(item["themes"]) & set(themes):
        return 0
    if not _fits_or_unknown(item["level"], expected.get("levels")):
        return 0
    if _fits(item["format"], expected.get("formats")) and _fits_or_unknown(item["stage"], expected.get("stages")):
        return 2
    return 1


def precision_at_k(grades, k):
    top = grades[:k]
    if not top:
        return 0.0
    return sum(1 for g in top if g > 0) / k


def hit_rate_at_k(grades, k):
    return 1.0 if any(g > 0 for g in grades[:k]) else 0.0


def mrr(grades):
    for i, g in enumerate(grades, 1):
        if g > 0:
            return 1 / i
    return 0.0


def dcg(grades):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(grades))


def ndcg_at_k(grades, ideal_grades, k):
    ideal = dcg(sorted(ideal_grades, reverse=True)[:k])
    if ideal == 0:
        return 0.0
    return dcg(grades[:k]) / ideal


def diversity(items, field):
    """Доля уникальных значений поля в выдаче (1.0 — все разные)."""
    items = [it for it in items if it]
    if not items:
        return 0.0
    values = [frozenset(it[field]) if isinstance(it[field], (set, list)) else it[field] for it in items]
    return len(set(values)) / len(items)


def text_rate(recs, field):
    """Доля рекомендаций с непустым полем (reason / next_step)."""
    if not recs:
        return 0.0
    return sum(1 for r in recs if str(r.get(field) or "").strip()) / len(recs)


def uniqueness(recs, field):
    """Насколько объяснения разные. Если у всех один и тот же текст — это шаблон, а не объяснение."""
    texts = [str(r.get(field) or "").strip() for r in recs]
    texts = [t for t in texts if t]
    if not texts:
        return 0.0
    return len(set(texts)) / len(texts)


def coverage(all_recommended_ids, catalog_size):
    if not catalog_size:
        return 0.0
    return len(set(all_recommended_ids)) / catalog_size


def run_checks(check_names, items, seen_ids):
    """Точечные проверки из профиля. Возвращает {имя: True/False}."""
    first = items[0] if items else None
    result = {}
    for name in check_names:
        if name == "first_is_free":
            result[name] = bool(first) and not first["is_paid"]
        elif name == "not_advanced_first":
            result[name] = bool(first) and first["level"] != "experienced"
        elif name == "short_first":
            result[name] = bool(first) and (
                first["format"] in SHORT_FORMATS
                or (first["duration_min"] or 999) <= SHORT_DURATION_MIN
            )
        elif name == "no_seen":
            result[name] = not any(it and it["material_id"] in seen_ids for it in items)
        else:
            raise ValueError(f"неизвестная проверка: {name}")
    return result
