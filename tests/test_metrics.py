from pathlib import Path

import pytest

from analytics.config import THEMES

from analytics import metrics
from analytics.catalog import fix_homoglyphs, load_catalog, normalize_item
from analytics.evaluate import evaluate_profile, load_profiles
from analytics.history import build_history
from analytics.recommenders import goal_to_themes, make_topic_baseline


def item(mid, themes=("marketing",), level="", fmt="article", stage="", paid=False, dur=10):
    return {"material_id": mid, "themes": set(themes), "level": level, "format": fmt, "stage": stage,
            "is_paid": paid, "duration_min": dur, "popularity": 1.0}


def test_relevance_grades():
    expected = {"themes": ["marketing"], "levels": ["beginner"], "formats": ["article"], "stages": ["start"]}
    assert metrics.relevance(item("a", stage="start"), expected) == 2
    assert metrics.relevance(item("a", fmt="course"), expected) == 1
    assert metrics.relevance(item("a", stage="growth"), expected) == 1
    assert metrics.relevance(item("a", themes=["team"]), expected) == 0
    assert metrics.relevance(item("a", themes=["team", "marketing"]), expected) == 2
    assert metrics.relevance(item("a", level="experienced"), expected) == 0
    assert metrics.relevance(item("a"), expected, seen_ids={"a"}) == 0
    assert metrics.relevance(None, expected) == 0


def test_unknown_level_is_not_penalized():
    assert metrics.relevance(item("a", level=""), {"levels": ["experienced"]}) == 2


def test_empty_expectations_accept_everything():
    assert metrics.relevance(item("a", themes=["taxes_law"], level="experienced"), {}) == 2


def test_precision_hit_mrr():
    grades = [0, 2, 0, 1, 0]
    assert metrics.precision_at_k(grades, 5) == pytest.approx(0.4)
    assert metrics.hit_rate_at_k(grades, 1) == 0.0
    assert metrics.hit_rate_at_k(grades, 2) == 1.0
    assert metrics.mrr(grades) == pytest.approx(0.5)
    assert metrics.mrr([0, 0]) == 0.0


def test_precision_short_list_is_penalized():
    # вернули 2 материала вместо 5 — это хуже, чем 5 хороших
    assert metrics.precision_at_k([1, 1], 5) == pytest.approx(0.4)


def test_ndcg():
    assert metrics.ndcg_at_k([2, 1, 0], [2, 1, 0], 3) == pytest.approx(1.0)
    assert metrics.ndcg_at_k([0, 1, 2], [2, 1, 0], 3) < 1.0
    assert metrics.ndcg_at_k([0, 0], [0, 0], 2) == 0.0


def test_text_metrics():
    recs = [{"reason": "a", "next_step": ""}, {"reason": "a", "next_step": "go"}, {"reason": "b"}]
    assert metrics.text_rate(recs, "reason") == 1.0
    assert metrics.text_rate(recs, "next_step") == pytest.approx(1 / 3)
    assert metrics.uniqueness(recs, "reason") == pytest.approx(2 / 3)
    assert metrics.text_rate([], "reason") == 0.0


def test_diversity_and_coverage():
    items = [item("a"), item("b", themes=["team"]), item("c", themes=["team"])]
    assert metrics.diversity(items, "themes") == pytest.approx(2 / 3)
    assert metrics.coverage(["a", "a", "b"], 10) == pytest.approx(0.2)


def test_checks():
    items = [item("a", paid=True, level="experienced", fmt="course", dur=300), item("b")]
    res = metrics.run_checks(["first_is_free", "not_advanced_first", "short_first", "no_seen"], items, {"b"})
    assert res == {"first_is_free": False, "not_advanced_first": False, "short_first": False, "no_seen": False}
    with pytest.raises(ValueError):
        metrics.run_checks(["unknown"], items, set())


def test_goal_parsing():
    assert "marketing" in goal_to_themes("продвижение бизнеса")
    assert "sales" in goal_to_themes("как найти клиентов")
    assert "taxes_law" in goal_to_themes("налоги ип скока платить")
    assert "marketplaces" in goal_to_themes("продажи на маркетплейсах")
    assert goal_to_themes(None) == []


def test_homoglyphs():
    assert fix_homoglyphs("Маркeтплейсы") == "Маркетплейсы"
    assert fix_homoglyphs("HoReСa") == "HoReCa"
    assert fix_homoglyphs("115-ФЗ ok") == "115-ФЗ ok"


def test_catalog_normalization():
    it = normalize_item({"material_id": 1, "topics": "Финансы|Маркeтплейсы", "tags": "Развитие бизнеса",
                         "is_paid": "True", "duration_min": ""})
    assert it["themes"] == {"finance", "marketplaces"}
    assert it["stage"] == "growth"
    assert it["is_paid"] is True and it["duration_min"] is None


# --- целостность тестовых профилей ---

CATALOG = load_catalog()
PROFILES = load_profiles()
REAL_CATALOG = Path("data/raw/catalog.csv")
ALLOWED_CHECKS = {"first_is_free", "not_advanced_first", "short_first", "no_seen"}


def test_profile_ids_unique():
    ids = [p["id"] for p in PROFILES]
    assert len(ids) == len(set(ids))


def test_all_scenarios_from_spec_covered():
    scenarios = {p["scenario"] for p in PROFILES}
    assert {"cold_start", "partial_profile", "full_profile", "with_history", "no_match"} <= scenarios


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p["id"])
def test_profile_is_valid(profile):
    assert set(profile["expected"]) <= {"themes", "levels", "stages", "formats"}
    assert set(profile["expected"].get("themes", [])) <= set(THEMES)
    assert set(profile.get("checks", [])) <= ALLOWED_CHECKS
    # в каталоге должно быть достаточно подходящих материалов, иначе метрики бессмысленны
    seen = {h["material_id"] for h in build_history(profile.get("history_spec"), CATALOG)}
    relevant = [it for it in CATALOG if metrics.relevance(it, profile["expected"], seen) > 0]
    assert len(relevant) >= 3, f"мало релевантных материалов: {len(relevant)}"
    if profile.get("history_spec"):
        assert seen, "история не собралась из каталога"


def test_baseline_end_to_end():
    rec = make_topic_baseline(CATALOG)
    for p in PROFILES:
        row = evaluate_profile(rec, p, CATALOG, 5)
        assert row["error"] == ""
        assert len(row["ids"]) == 5


@pytest.mark.skipif(not REAL_CATALOG.exists(), reason="нет data/raw/catalog.csv (см. analytics/export_catalog.py)")
@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p["id"])
def test_profile_fits_real_catalog(profile):
    real = load_catalog(REAL_CATALOG)
    seen = {h["material_id"] for h in build_history(profile.get("history_spec"), real)}
    relevant = [it for it in real if metrics.relevance(it, profile["expected"], seen) > 0]
    assert len(relevant) >= 3
    if profile.get("history_spec"):
        assert seen
