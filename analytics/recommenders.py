"""Рекомендатели, которые умеет сравнивать evaluate.py.

Все приводятся к одному виду: f(user, history, k) -> list[dict]
где dict содержит хотя бы material_id (+ reason, next_step, score если есть).

- topic_baseline — бейзлайн из ТЗ: совпадение темы, дальше по популярности
- popular        — просто самые популярные (нижняя планка)
- api            — наш бэкенд по HTTP (POST /api/v1/recommendations)
- python         — функция из кода напрямую, например recommender.ranking:recommend
"""
import importlib
import inspect
import json
import random
import urllib.request

from analytics.config import GOAL_KEYWORDS


def goal_to_themes(goal):
    if not goal:
        return []
    text = f" {str(goal).lower()} "
    return [theme for theme, words in GOAL_KEYWORDS.items() if any(w in text for w in words)]


def make_topic_baseline(catalog):
    def recommend(user, history, k):
        seen = {h["material_id"] for h in history}
        themes = set(goal_to_themes(user.get("current_goal")))
        pool = [it for it in catalog if it["material_id"] not in seen]
        by_pop = sorted(pool, key=lambda it: (-it["popularity"], it["material_id"]))
        matched = [it for it in by_pop if it["themes"] & themes]
        rest = [it for it in by_pop if not it["themes"] & themes]
        result = []
        for it in (matched + rest)[:k]:
            reason = "Совпадает с темой вашей задачи" if it["themes"] & themes else "Популярный материал"
            result.append({"material_id": it["material_id"], "reason": reason, "next_step": "Открыть материал"})
        return result
    return recommend


def make_popular(catalog):
    def recommend(user, history, k):
        top = sorted(catalog, key=lambda it: (-it["popularity"], it["material_id"]))[:k]
        return [{"material_id": it["material_id"], "reason": "Популярный материал", "next_step": "Открыть материал"} for it in top]
    return recommend


def make_random(catalog, seed=1):
    def recommend(user, history, k):
        rng = random.Random(f"{seed}{sorted(user.items())}{len(history)}")
        return [{"material_id": it["material_id"]} for it in rng.sample(catalog, min(k, len(catalog)))]
    return recommend


def api_payload(user, history, k):
    """Translate analytics' internal profile/event fixtures to the current HTTP contract."""
    fields = {"stage": "business_stage", "experience": "experience_level"}
    profile = {fields.get(key, key): value for key, value in user.items()
               if key in {"stage", "experience", "business_stage", "experience_level", "industry", "current_goal", "preferred_formats"}}
    if user.get("preferred_format"):
        profile["preferred_formats"] = [user["preferred_format"]]
    events = [{"material_id": h["material_id"], "event_type": h.get("event_type", h.get("event", "view"))} for h in history]
    return {"user_profile": profile, "history": events, "limit": k}


def make_api(url, timeout=10):
    def recommend(user, history, k):
        body = json.dumps(api_payload(user, history, k)).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [{**r, "reason": "; ".join(r.get("reasons", []))} for r in data.get("recommendations", [])]
    return recommend


def make_python(target, catalog):
    """target вида 'module.path:function'."""
    module_name, func_name = target.split(":")
    func = getattr(importlib.import_module(module_name), func_name)
    params = inspect.signature(func).parameters

    def recommend(user, history, k):
        kwargs = {}
        if "catalog" in params:
            kwargs["catalog"] = catalog
        if "k" in params:
            kwargs["k"] = k
        elif "limit" in params:
            kwargs["limit"] = k
        result = func(user, history, **kwargs)
        if isinstance(result, dict):
            result = result.get("recommendations", [])
        return [r if isinstance(r, dict) else r.__dict__ for r in result]
    return recommend


def build(name, catalog):
    if name == "topic_baseline":
        return make_topic_baseline(catalog)
    if name == "popular":
        return make_popular(catalog)
    if name == "random":
        return make_random(catalog)
    if name.startswith("api="):
        return make_api(name[4:])
    if name.startswith("py="):
        return make_python(name[3:], catalog)
    raise ValueError(f"не знаю рекомендатель {name}")
