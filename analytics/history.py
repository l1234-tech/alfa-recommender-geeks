"""Синтетическая история действий для тестовых профилей.

В профиле история описана правилом (группа тем/уровень/формат/сколько),
а конкретные material_id подбираются из каталога. Так профили работают
и на мок-каталоге, и на реальной выгрузке.
"""
import random
from datetime import datetime, timedelta


def build_history(spec, catalog, seed=42):
    if not spec:
        return []

    candidates = [
        item for item in catalog
        if spec.get("theme") in item["themes"]
        and (not spec.get("level") or item["level"] == spec["level"])
        and (not spec.get("format") or item["format"] == spec["format"])
    ]
    candidates.sort(key=lambda x: x["material_id"])
    rng = random.Random(seed)
    picked = rng.sample(candidates, min(spec.get("n", 1), len(candidates)))

    start = datetime(2026, 11, 1, 12, 0)
    history = []
    for i, item in enumerate(picked):
        history.append({
            "material_id": item["material_id"],
            "event": spec.get("event", "view"),
            "ts": (start + timedelta(days=i)).isoformat(),
        })
    return history


def random_events(catalog, n_users=200, events_per_user=(1, 8), seed=0):
    """Генератор журнала событий для тех, кому нужны синтетические данные целиком."""
    rng = random.Random(seed)
    weights = [max(item["popularity"], 0.01) for item in catalog]
    events = []
    for u in range(n_users):
        favorite = rng.choice(sorted(rng.choice(catalog)["themes"]) or ["?"])
        for _ in range(rng.randint(*events_per_user)):
            if rng.random() < 0.6:
                same = [it for it in catalog if favorite in it["themes"]] or catalog
                item = rng.choice(same)
            else:
                item = rng.choices(catalog, weights=weights)[0]
            event = "view"
            if item["is_paid"] and rng.random() < 0.1:
                event = "purchase"
            elif rng.random() < 0.3:
                event = "complete"
            events.append({"user_id": f"u{u:04d}", "material_id": item["material_id"], "event": event})
    return events
