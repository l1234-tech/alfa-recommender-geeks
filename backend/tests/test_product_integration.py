import logging
from dataclasses import replace

from app.schemas.recommendation import RecommendationRequest, UserProfileIn
from app.services import ml_adapter, recommendation_service
from app.services.sample_catalog import get_catalog


def test_actual_engine_path_and_hybrid_are_used(monkeypatch, caplog):
    assert ml_adapter.RECOMMENDER_AVAILABLE
    original = ml_adapter._engine_recommend
    calls = []
    def observed(*args, **kwargs):
        calls.append(kwargs["strategy"])
        return original(*args, **kwargs)
    monkeypatch.setattr(ml_adapter, "_engine_recommend", observed)
    def forbidden(*args):
        raise AssertionError("Unexpected fallback")
    monkeypatch.setattr(ml_adapter, "_rank_builtin", forbidden)
    fields = ml_adapter.build_profile_fields(UserProfileIn(current_goal="marketing"), [])
    with caplog.at_level(logging.INFO):
        for strategy in ("baseline", "hybrid"):
            assert ml_adapter.rank(get_catalog(), fields, 5, strategy)
    assert calls == ["baseline", "hybrid"]
    assert "path=engine" in caplog.text


def test_russian_catalog_topics_are_normalized_consistently():
    item = replace(get_catalog()[0], topics=frozenset({"Финансы и учет"}),
                   title="Финансы и учет", description="", tags=frozenset(), industries=frozenset())
    fields = ml_adapter.build_profile_fields(UserProfileIn(current_goal="finance"), [])
    assert ml_adapter.rank([item], fields, 1, "baseline")[0].score > 0


def test_optional_metadata_and_unknown_payment_are_preserved(monkeypatch):
    item = replace(get_catalog()[0], url="https://example.org/material", is_paid=None)
    monkeypatch.setattr(recommendation_service, "get_materials", lambda: [item])
    monkeypatch.setattr(recommendation_service, "catalog_source", lambda: "database")
    result = recommendation_service.get_recommendations(RecommendationRequest())
    assert result.metadata.catalog_source == "database"
    assert result.recommendations[0].url == item.url
    assert result.recommendations[0].description == item.description
    assert result.recommendations[0].is_paid is None
    assert recommendation_service.public_url("javascript:alert(1)") is None
    assert recommendation_service.public_url("/materials/fake") is None


def test_forced_fallback_remains_explicit(caplog):
    fields = ml_adapter.build_profile_fields(UserProfileIn(), [])
    with caplog.at_level(logging.WARNING):
        assert ml_adapter.rank(get_catalog(), fields, 2, "baseline", force_builtin=True)
    assert "path=builtin" in caplog.text
