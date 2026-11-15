"""Compare the HTTP API and the topic baseline on the same PostgreSQL catalog."""

import os

import psycopg

from analytics.catalog import normalize_item
from analytics.evaluate import evaluate_profile, load_profiles, summarize
from analytics.recommenders import make_api, make_topic_baseline
from recommender.data_processing.postgres_catalog import load_catalog


def load_open_catalog(database_url):
    with psycopg.connect(database_url) as connection:
        connection.read_only = True
        items = load_catalog(connection)
        enrollments = dict(connection.execute(
            'SELECT "CourseId"::text, count(*) FROM public."CourseUserBindings" '
            'WHERE NOT COALESCE("IsDeleted", false) GROUP BY 1'
        ))
        references = dict(connection.execute(
            'SELECT "ItemId"::text, count(*) FROM public."RecommendedItems" GROUP BY 1'
        ))

    return [
        normalize_item({
            "material_id": item.item_id,
            "title": item.title,
            "format": item.item_type,
            "topics": sorted(item.topics),
            "tags": sorted(item.tags),
            "industries": sorted(item.industries),
            "level": "beginner" if "Без опыта" in item.industries else (
                "experienced" if "С опытом" in item.industries else ""
            ),
            "is_paid": item.is_paid,
            "popularity": (enrollments if item.item_type == "course" else references).get(item.item_id, 0),
        })
        for item in items if item.is_available
    ]


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must point to the restored catalog used by the API")
    api_url = os.environ.get("RECO_API_URL", "http://127.0.0.1:8000").rstrip("/")
    catalog = load_open_catalog(database_url)
    if not catalog or len(catalog) != len({row["material_id"] for row in catalog}):
        raise SystemExit("Catalog must be nonempty and have unique material IDs")

    profiles = load_profiles()
    algorithms = {
        "Подбор по теме": make_topic_baseline(catalog),
        "API": make_api(api_url + "/api/v1/recommendations"),
    }
    print(f"Каталог PostgreSQL: {len(catalog)} материалов, {len(profiles)} профилей, K=5")
    print("Алгоритм | Precision@5 | nDCG@5 | nDCG@5 с историей | Объяснения | Следующий шаг")
    for name, recommend in algorithms.items():
        rows = [evaluate_profile(recommend, profile, catalog, 5) for profile in profiles]
        invalid = [
            row["profile"] for row in rows
            if row["error"] or "known_ids" in row["failed_checks"] or "returns_k" in row["failed_checks"]
        ]
        if invalid:
            raise SystemExit(f"{name}: API errors, incomplete results or catalog mismatch for {', '.join(invalid)}")
        total = summarize(rows)
        history = summarize([row for row in rows if row["scenario"] == "with_history"])
        print(
            f"{name} | {total['precision']:.2f} | {total['ndcg']:.2f} | {history['ndcg']:.2f} | "
            f"{total['reason_rate']:.0%} | {total['next_step_rate']:.0%}"
        )


if __name__ == "__main__":
    main()
