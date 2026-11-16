"""Pydantic request/response schemas for the recommendations API.

Field names follow the team API contract fixed in docs/api.md. All profile
fields are optional so the cold-start scenario (empty profile) stays valid.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

# Event types accepted on input. Kept permissive but validated; the canonical
# set is reconciled with the real dataset in docs/api.md.
EventType = str


class HistoryEvent(BaseModel):
    material_id: str = Field(min_length=1)
    event_type: EventType = "view"


class UserProfileIn(BaseModel):
    business_stage: str | None = None
    industry: str | None = None
    current_goal: str | None = None
    experience_level: str | None = None
    preferred_formats: list[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.business_stage,
            self.industry,
            self.current_goal,
            self.experience_level,
            self.preferred_formats,
        ])


class RecommendationRequest(BaseModel):
    user_profile: UserProfileIn = Field(default_factory=UserProfileIn)
    history: list[HistoryEvent] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1, le=20)


class RecommendationItem(BaseModel):
    material_id: str
    title: str
    material_type: str
    topic: str | None = None
    is_paid: bool | None = None
    description: str | None = None
    url: str | None = None
    score: float
    reasons: list[str]
    next_step: str


class RecommendationMeta(BaseModel):
    cold_start: bool
    strategy: str
    limit: int
    returned: int
    catalog_source: str = "sample"


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
    metadata: RecommendationMeta
