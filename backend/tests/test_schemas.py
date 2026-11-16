import pytest
from pydantic import ValidationError

from app.schemas.recommendation import RecommendationRequest, UserProfileIn


def test_empty_profile_detected():
    assert UserProfileIn().is_empty() is True
    assert UserProfileIn(current_goal="marketing").is_empty() is False


def test_request_defaults():
    req = RecommendationRequest()
    assert req.user_profile.is_empty()
    assert req.history == []
    assert req.limit is None


def test_limit_bounds():
    assert RecommendationRequest(limit=10).limit == 10
    with pytest.raises(ValidationError):
        RecommendationRequest(limit=0)
    with pytest.raises(ValidationError):
        RecommendationRequest(limit=51)


def test_history_event_requires_material_id():
    with pytest.raises(ValidationError):
        RecommendationRequest(history=[{"material_id": ""}])
