"""Прогон тестовых профилей через рекомендатели и сравнение метрик.

Примеры:
    python -m analytics.evaluate
    python -m analytics.evaluate --algo topic_baseline --algo api=http://localhost:8000/api/v1/recommendations
    python -m analytics.evaluate --catalog data/catalog.csv --algo py=recommender.ranking:recommend
"""
import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from analytics import metrics, recommenders
from analytics.catalog import load_catalog
from analytics.config import DEFAULT_K
from analytics.history import build_history

ROOT = Path(__file__).parent
PROFILES = ROOT / "profiles" / "test_profiles.json"
REPORTS = ROOT / "reports"
REAL_CATALOG = Path("data/raw/catalog.csv")

METRIC_COLS = ["precision", "ndcg", "hit", "mrr", "reason_rate", "reason_unique", "next_step_rate",
               "theme_div", "format_div", "paid_share", "checks_passed", "latency_ms"]


def load_profiles(path=PROFILES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_profile(recommend, profile, catalog, k):
    by_id = {it["material_id"]: it for it in catalog}
    history = build_history(profile.get("history_spec"), catalog)
    seen = {h["material_id"] for h in history}
    expected = profile["expected"]

    row = {"profile": profile["id"], "scenario": profile["scenario"], "error": ""}
    start = time.perf_counter()
    try:
        recs = recommend(profile["user"], history, k)
    except Exception as e:  # нам важно увидеть падение в отчёте, а не уронить весь прогон
        recs = []
        row["error"] = f"{type(e).__name__}: {e}"
    row["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)

    ids = [str(r.get("material_id")) for r in recs][:k]
    items = [by_id.get(i) for i in ids]
    grades = [metrics.relevance(it, expected, seen) for it in items]
    ideal = [metrics.relevance(it, expected, seen) for it in catalog]

    row.update({
        "precision": metrics.precision_at_k(grades, k),
        "ndcg": metrics.ndcg_at_k(grades, ideal, k),
        "hit": metrics.hit_rate_at_k(grades, k),
        "mrr": metrics.mrr(grades),
        "reason_rate": metrics.text_rate(recs, "reason"),
        "reason_unique": metrics.uniqueness(recs, "reason"),
        "next_step_rate": metrics.text_rate(recs, "next_step"),
        "theme_div": metrics.diversity(items, "themes"),
        "format_div": metrics.diversity(items, "format"),
        "paid_share": (sum(1 for it in items if it and it["is_paid"]) / len(items)) if items else 0.0,
    })

    checks = {
        "returns_k": len(ids) == min(k, len(catalog)),
        "known_ids": all(it is not None for it in items),
        "has_reason": row["reason_rate"] == 1.0,
        "has_next_step": row["next_step_rate"] == 1.0,
    }
    checks.update(metrics.run_checks(profile.get("checks", []), [it for it in items if it], seen))
    row["checks_passed"] = sum(checks.values()) / len(checks)
    row["failed_checks"] = ",".join(name for name, ok in checks.items() if not ok)
    row["top"] = " | ".join(
        f"{it['title'][:40]} [{','.join(sorted(it['themes']))}/{it['format']}{'/' + it['level'] if it['level'] else ''}{'/paid' if it['is_paid'] else ''}]"
        if it else f"{i}:UNKNOWN" for i, it in zip(ids, items)
    )
    row["ids"] = ids
    return row


def summarize(rows):
    summary = {col: sum(r[col] for r in rows) / len(rows) for col in METRIC_COLS}
    return summary


def write_report(results, catalog, k, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"# Отчёт оценки рекомендаций (K={k}, профилей: {len(next(iter(results.values())))}, "
             f"материалов в каталоге: {len(catalog)})", ""]

    lines += ["## Сводка", "",
              "| Алгоритм | " + " | ".join(METRIC_COLS) + " | coverage |",
              "|---" * (len(METRIC_COLS) + 2) + "|"]
    for algo, rows in results.items():
        s = summarize(rows)
        cov = metrics.coverage([i for r in rows for i in r["ids"]], len(catalog))
        lines.append(f"| {algo} | " + " | ".join(f"{s[c]:.2f}" if c != "latency_ms" else f"{s[c]:.0f}"
                                                for c in METRIC_COLS) + f" | {cov:.2f} |")

    lines += ["", "## По сценариям (nDCG@K)", ""]
    scenarios = sorted({r["scenario"] for rows in results.values() for r in rows})
    lines += ["| Алгоритм | " + " | ".join(scenarios) + " |", "|---" * (len(scenarios) + 1) + "|"]
    for algo, rows in results.items():
        groups = defaultdict(list)
        for r in rows:
            groups[r["scenario"]].append(r["ndcg"])
        lines.append(f"| {algo} | " + " | ".join(f"{sum(groups[s]) / len(groups[s]):.2f}" for s in scenarios) + " |")

    for algo, rows in results.items():
        lines += ["", f"## {algo}: по профилям", "",
                  "| Профиль | P@K | nDCG | Проваленные проверки | Топ выдачи |", "|---|---|---|---|---|"]
        for r in rows:
            fails = r["failed_checks"] or "—"
            if r["error"]:
                fails = f"ОШИБКА: {r['error']}"
            lines.append(f"| {r['profile']} | {r['precision']:.2f} | {r['ndcg']:.2f} | {fails} | {r['top']} |")

    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        cols = ["algo", "profile", "scenario"] + METRIC_COLS + ["failed_checks", "error", "top"]
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for algo, rows in results.items():
            for r in rows:
                writer.writerow({"algo": algo, **r})


def main():
    parser = argparse.ArgumentParser(description="Оценка рекомендаций на тестовых профилях")
    parser.add_argument("--catalog", help="путь к каталогу (json/csv). По умолчанию data/raw/catalog.csv, если его нет — мок")
    parser.add_argument("--profiles", default=str(PROFILES))
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--algo", action="append",
                        help="topic_baseline | popular | random | api=URL | py=module:func (можно несколько)")
    parser.add_argument("--out", default=str(REPORTS))
    args = parser.parse_args()

    catalog_path = args.catalog or (REAL_CATALOG if REAL_CATALOG.exists() else None)
    catalog = load_catalog(catalog_path)
    print(f"Каталог: {catalog_path or 'мок (analytics/fixtures)'}")
    profiles = load_profiles(args.profiles)
    algos = args.algo or ["random", "popular", "topic_baseline"]

    results = {}
    for name in algos:
        recommend = recommenders.build(name, catalog)
        results[name] = [evaluate_profile(recommend, p, catalog, args.k) for p in profiles]

    write_report(results, catalog, args.k, Path(args.out))

    print(f"{'algo':<45}{'P@K':>7}{'nDCG':>7}{'checks':>8}")
    for name, rows in results.items():
        s = summarize(rows)
        print(f"{name:<45}{s['precision']:>7.2f}{s['ndcg']:>7.2f}{s['checks_passed']:>8.2f}")
    print(f"\nОтчёт: {Path(args.out) / 'report.md'}")


if __name__ == "__main__":
    main()
