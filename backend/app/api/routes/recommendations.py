"""Recommendations endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from ...schemas.recommendation import RecommendationRequest, RecommendationResponse
from ...services.recommendation_service import get_recommendations

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """Rank catalog materials for the given profile/history and explain each pick.

    An empty profile with no history is a valid cold-start request and returns a
    useful starter selection.
    """
    return get_recommendations(request)
