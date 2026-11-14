"""Hybrid content ranking combining metadata overlap and TF-IDF cosine."""
from __future__ import annotations
from recommender.algorithms.content_baseline import score_item as score_metadata
from recommender.algorithms.tfidf import TfidfIndex
from recommender.models import CatalogItem,UserProfile
def score_hybrid(profile:UserProfile,item:CatalogItem,index:TfidfIndex,*,tfidf_weight:float=0.65)->float:
    if not 0<=tfidf_weight<=1: raise ValueError("tfidf_weight must be between 0 and 1")
    metadata=score_metadata(profile,item); text=index.score(profile,item)
    if not profile_query_available(profile):return metadata
    return tfidf_weight*text+(1-tfidf_weight)*metadata
def profile_query_available(profile:UserProfile)->bool:
    return bool(profile.topics or profile.tags or profile.industries or profile.preferred_types or profile.current_goal.strip())
