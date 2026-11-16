"""Оценка на реальном поведении: leave-one-out по записям на курсы.

Берём пользователей, у которых 2+ курса. Один курс прячем, остальные отдаём
алгоритму как историю и смотрим, окажется ли спрятанный курс в топ-K.
Даты есть только у ~26% записей, поэтому прячем не «последний» курс,
а случайный (с фиксированным seed).

    python -m analytics.offline_eval --catalog data/raw/catalog.csv --interactions data/raw/interactions.csv
    python -m analytics.offline_eval ... --algo api=http://localhost:8000/api/v1/recommendations --max-users 300
"""
import argparse
import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from analytics import recommenders
from analytics.catalog import load_catalog
from analytics.config import DEFAULT_K


def load_interactions(path):
    users = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            event = "complete" if row["is_completed"].lower() in ("true", "t", "1") else "view"
            users[row["user_id"]][row["material_id"]] = event
    return users


def split(users, course_ids, seed=42, max_users=None):
    rng = random.Random(seed)
    cases = []
    for uid in sorted(users):
        courses = {m: e for m, e in users[uid].items() if m in course_ids}
        if len(courses) < 2:
            continue
        target = rng.choice(sorted(courses))
        history = [{"material_id": m, "event": e} for m, e in sorted(courses.items()) if m != target]
        cases.append((uid, target, history))
    rng.shuffle(cases)
    return cases[:max_users] if max_users else cases


def train_popularity(catalog, users, cases):
    """Популярность без спрятанных курсов, чтобы не подглядывать в ответ."""
    counts = Counter(m for u in users.values() for m in u)
    for _, target, _ in cases:
        counts[target] -= 1
    top = max(math.log1p(max(c, 0)) for c in counts.values()) or 1
    result = []
    for it in catalog:
        it = dict(it)
        if it["format"] == "course":
            it["popularity"] = math.log1p(max(counts.get(it["material_id"], 0), 0)) / top
        result.append(it)
    return result


def make_cooccurrence(catalog, users, cases):
    """«Те, кто проходил ваши курсы, проходили ещё…» — простой бейзлайн по истории."""
    held = {(uid, target) for uid, target, _ in cases}
    pairs = defaultdict(Counter)
    for uid, items in users.items():
        ids = [m for m in items if (uid, m) not in held]
        for a in ids:
            for b in ids:
                if a != b:
                    pairs[a][b] += 1
    fallback = recommenders.make_popular(catalog)

    def recommend(user, history, k):
        seen = {h["material_id"] for h in history}
        score = Counter()
        for h in history:
            score.update(pairs.get(h["material_id"], {}))
        ranked = [m for m, _ in score.most_common() if m not in seen]
        for r in fallback(user, history, k + len(seen)):
            if r["material_id"] not in seen and r["material_id"] not in ranked:
                ranked.append(r["material_id"])
        return [{"material_id": m, "reason": "Его проходили вместе с вашими курсами", "next_step": "Записаться"}
                for m in ranked[:k]]
    return recommend


def evaluate(recommend, cases, course_ids, k):
    hits = hits_courses = rr = 0.0
    for _, target, history in cases:
        recs = recommend({}, history, k * 5)
        ids = [str(r.get("material_id")) for r in recs]
        top = ids[:k]
        top_courses = [i for i in ids if i in course_ids][:k]
        if target in top:
            hits += 1
            rr += 1 / (top.index(target) + 1)
        if target in top_courses:
            hits_courses += 1
    n = len(cases) or 1
    return {"hit": hits / n, "mrr": rr / n, "hit_courses": hits_courses / n}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/raw/catalog.csv")
    parser.add_argument("--interactions", default="data/raw/interactions.csv")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--algo", action="append")
    parser.add_argument("--max-users", type=int)
    parser.add_argument("--out", default=str(Path(__file__).parent / "reports" / "offline_eval.md"))
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    course_ids = {it["material_id"] for it in catalog if it["format"] == "course"}
    users = load_interactions(args.interactions)
    cases = split(users, course_ids, max_users=args.max_users)
    train_catalog = train_popularity(catalog, users, cases)

    algos = {"random": recommenders.make_random(train_catalog),
             "popular": recommenders.make_popular(train_catalog),
             "topic_baseline": recommenders.make_topic_baseline(train_catalog),
             "cooccurrence": make_cooccurrence(train_catalog, users, cases)}
    for name in args.algo or []:
        algos[name] = recommenders.build(name, catalog)

    lines = [f"# Leave-one-out на записях на курсы (K={args.k})", "",
             f"Пользователей с 2+ курсами: {len(cases)}, курсов в каталоге: {len(course_ids)}. "
             "Один курс пользователя спрятан, остальные переданы как история.", "",
             "| Алгоритм | HitRate@K | MRR@K | HitRate@K только среди курсов |", "|---|---|---|---|"]
    print(f"{'algo':<45}{'Hit':>7}{'MRR':>7}{'HitC':>7}")
    for name, rec in algos.items():
        m = evaluate(rec, cases, course_ids, args.k)
        lines.append(f"| {name} | {m['hit']:.3f} | {m['mrr']:.3f} | {m['hit_courses']:.3f} |")
        print(f"{name:<45}{m['hit']:>7.3f}{m['mrr']:>7.3f}{m['hit_courses']:>7.3f}")

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nОтчёт: {args.out}")


if __name__ == "__main__":
    main()
