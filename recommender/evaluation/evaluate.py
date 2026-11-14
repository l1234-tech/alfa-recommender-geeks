"""Aggregate-only offline evaluation of the metadata recommender."""
from __future__ import annotations
from collections.abc import Iterable
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem,UserProfile
from recommender.ranking import recommend
def evaluate_content_baseline(events:Iterable[UserInteraction],catalog:list[CatalogItem],*,k:int=10,
                              onboarding:UserProfile|None=None)->dict[str,float]:
    recs=[]; relevant=[]
    for split in temporal_holdout(events):
        profile=build_user_profile(split.train_events,catalog,onboarding=onboarding)
        recs.append([r.item.key for r in recommend(profile,catalog,limit=k)])
        relevant.append(set(split.test_relevant_item_keys))
    return aggregate_ranking_metrics(recs,relevant,k)
