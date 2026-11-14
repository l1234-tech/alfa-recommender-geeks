"""Deterministic benchmark for onboarding-only (cold-start) profiles.

Cases and expected items are hand-authored evaluation fixtures, not observed
user outcomes. Keep them representative and review them with domain experts.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable
from recommender.algorithms.tfidf import TfidfIndex
from recommender.evaluation.metrics import aggregate_ranking_metrics,catalog_coverage
from recommender.models import CatalogItem,ItemKey,UserProfile
from recommender.ranking import recommend
@dataclass(frozen=True)
class ColdStartCase:
    profile:UserProfile
    relevant_item_keys:frozenset[ItemKey]
def evaluate_cold_start_cases(cases:Iterable[ColdStartCase],catalog:list[CatalogItem],*,k:int=5,
                              strategies:tuple[str,...]=("baseline","hybrid"))->dict[str,dict[str,float]]:
    rows=list(cases)
    if not rows:return {s:{"profiles_evaluated":0.0,f"precision@{k}":0.0,f"recall@{k}":0.0,f"ndcg@{k}":0.0,"catalog_coverage":0.0} for s in strategies}
    tfidf=TfidfIndex.fit(catalog); available={x.key for x in catalog if x.is_available}
    output={}
    for strategy in strategies:
        predictions=[]
        for case in rows:
            ranked=recommend(case.profile,catalog,limit=k,strategy=strategy,tfidf_index=tfidf)
            predictions.append([r.item.key for r in ranked])
        relevant=[set(c.relevant_item_keys) for c in rows]
        metrics=aggregate_ranking_metrics(predictions,relevant,k)
        metrics["profiles_evaluated"]=metrics.pop("users_evaluated")
        metrics.update(catalog_coverage(predictions,available))
        output[strategy]=metrics
    return output
