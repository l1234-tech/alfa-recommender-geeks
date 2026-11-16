from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _post(payload):
    return client.post("/api/v1/recommendations", json=payload)


def test_profile_request_returns_ranked_explained_items():
    resp = _post({
        "user_profile": {
            "business_stage": "early",
            "industry": "retail",
            "current_goal": "marketing",
            "experience_level": "beginner",
            "preferred_formats": ["course", "article"],
        },
        "history": [],
        "limit": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["cold_start"] is False
    assert data["metadata"]["returned"] == len(data["recommendations"]) <= 3
    scores = [r["score"] for r in data["recommendations"]]
    assert scores == sorted(scores, reverse=True)
    top = data["recommendations"][0]
    assert top["reasons"] and top["next_step"]
    # A marketing/retail profile should surface a marketing material at the top.
    assert any(r["topic"] == "marketing" for r in data["recommendations"])


def test_cold_start_empty_profile_is_valid():
    resp = _post({})
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["cold_start"] is True
    assert len(data["recommendations"]) > 0


def test_history_items_are_not_recommended_again():
    seen = "mat-mkt-001"
    resp = _post({
        "user_profile": {"current_goal": "marketing"},
        "history": [{"material_id": seen, "event_type": "view"}],
    })
    assert resp.status_code == 200
    ids = [r["material_id"] for r in resp.json()["recommendations"]]
    assert seen not in ids


def test_limit_is_capped_and_validated():
    # Over the hard cap is rejected by schema validation.
    assert _post({"limit": 999}).status_code == 422
    # Zero is rejected.
    assert _post({"limit": 0}).status_code == 422


def test_health():
    assert client.get("/health").json()["status"] == "ok"
