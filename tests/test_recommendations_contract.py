"""Контрактные тесты эндпоинта рекомендаций (docs/api.md).

Пока эндпоинта нет — тесты пропускаются (skip), а не падают.
Можно гонять против запущенного сервера:
    RECO_API_URL=http://localhost:8000 pytest tests/test_recommendations_contract.py
"""
import json
import os
import time
import urllib.error
import urllib.request

import pytest

from analytics.evaluate import load_profiles

ENDPOINT = "/api/v1/recommendations"
LIMIT = 5
PROFILES = load_profiles()
BASE_URL = os.getenv("RECO_API_URL")


class Resp:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data


def _post_live(payload):
    req = urllib.request.Request(BASE_URL.rstrip("/") + ENDPOINT, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return Resp(r.status, json.loads(r.read().decode()))
    except urllib.error.HTTPError as e:
        return Resp(e.code, None)


@pytest.fixture(scope="module")
def post():
    if BASE_URL:
        func = _post_live
    else:
        from fastapi.testclient import TestClient
        from backend.app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        func = lambda payload: client.post(ENDPOINT, json=payload)

    probe = func({"user": {}, "history": [], "limit": LIMIT})
    if probe.status_code in (404, 405):
        pytest.skip("эндпоинт рекомендаций ещё не реализован")
    return func


def payload(user, history=None):
    return {"user": user, "history": history or [], "limit": LIMIT}


def recs_of(resp):
    assert resp.status_code == 200, f"статус {resp.status_code}"
    data = resp.json()
    assert isinstance(data.get("recommendations"), list)
    return data["recommendations"]


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p["id"])
def test_response_shape(post, profile):
    recs = recs_of(post(payload(profile["user"])))
    assert 0 < len(recs) <= LIMIT, "пустая выдача — холодный старт не работает"
    ids = [r["material_id"] for r in recs]
    assert len(ids) == len(set(ids)), "дубликаты в выдаче"
    for r in recs:
        assert r.get("material_id")
        assert str(r.get("title") or "").strip(), "нет названия"
        assert str(r.get("reason") or "").strip(), "нет объяснения"
        assert str(r.get("next_step") or "").strip(), "нет следующего шага"
        if "score" in r:
            assert isinstance(r["score"], (int, float))


def test_cold_start_returns_full_list(post):
    recs = recs_of(post(payload({})))
    assert len(recs) == LIMIT


def test_scores_sorted(post):
    recs = recs_of(post(payload({"current_goal": "marketing"})))
    scores = [r["score"] for r in recs if "score" in r]
    assert scores == sorted(scores, reverse=True)


def test_deterministic(post):
    p = payload({"stage": "early", "current_goal": "sales"})
    first = [r["material_id"] for r in recs_of(post(p))]
    second = [r["material_id"] for r in recs_of(post(p))]
    assert first == second, "одинаковый запрос дал разную выдачу — на демо будет странно"


def test_seen_materials_not_repeated(post):
    user = {"stage": "early", "current_goal": "marketing", "experience": "beginner"}
    first = recs_of(post(payload(user)))
    history = [{"material_id": r["material_id"], "event": "view"} for r in first[:2]]
    second = recs_of(post(payload(user, history)))
    seen = {h["material_id"] for h in history}
    assert not seen & {r["material_id"] for r in second}, "показали уже просмотренное"


def test_history_changes_result(post):
    user = {"current_goal": "marketing"}
    first = recs_of(post(payload(user)))
    history = [{"material_id": r["material_id"], "event": "complete"} for r in first[:3]]
    second = recs_of(post(payload(user, history)))
    assert [r["material_id"] for r in first] != [r["material_id"] for r in second]


@pytest.mark.parametrize("user", [
    {"stage": "unknown_stage", "experience": "guru"},
    {"current_goal": ""},
    {"current_goal": "а" * 2000},
    {"industry": None, "stage": None},
    {"some_new_field": 123},
], ids=["bad_values", "empty_goal", "long_goal", "nulls", "extra_field"])
def test_garbage_input_does_not_crash(post, user):
    resp = post(payload(user))
    assert resp.status_code in (200, 422), f"сервер упал: {resp.status_code}"


def test_unknown_history_id(post):
    resp = post(payload({}, [{"material_id": "does-not-exist", "event": "view"}]))
    assert resp.status_code in (200, 422)


def test_paid_content_not_disclosed(post):
    recs = recs_of(post(payload({"stage": "growth", "current_goal": "marketing", "experience": "advanced"})))
    for r in recs:
        if r.get("is_paid"):
            for key in ("content", "full_text", "lessons", "body"):
                assert key not in r, f"у платного материала отдаётся поле {key}"


def test_latency(post):
    start = time.perf_counter()
    recs_of(post(payload({"current_goal": "taxes"})))
    assert time.perf_counter() - start < 2.0
