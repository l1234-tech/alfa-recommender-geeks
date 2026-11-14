"""Candidate filtering and ranking for content and collaborative strategies."""
from __future__ import annotations
from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.content_baseline import score_item
from recommender.algorithms.hybrid import score_hybrid
from recommender.algorithms.tfidf import TfidfIndex
from recommender.explanations import explain
from recommender.models import CatalogItem,Recommendation,UserProfile
def recommend(profile:UserProfile,catalog:list[CatalogItem],limit:int=10,*,strategy:str="baseline",
              tfidf_index:TfidfIndex|None=None,collaborative_index:ItemItemIndex|None=None)->list[Recommendation]:
    strategies={"baseline","hybrid","collaborative","content_cf_hybrid"}
    if limit<1:return []
    if strategy not in strategies:raise ValueError(f"strategy must be one of: {', '.join(sorted(strategies))}")
    if strategy in {"hybrid","content_cf_hybrid"} and tfidf_index is None:tfidf_index=TfidfIndex.fit(catalog)
    if strategy in {"collaborative","content_cf_hybrid"} and collaborative_index is None:raise ValueError("collaborative_index is required for collaborative strategies")
    def score(item):
        if strategy=="baseline":return score_item(profile,item)
        if strategy=="hybrid":
            assert tfidf_index is not None
            return score_hybrid(profile,item,tfidf_index)
        assert collaborative_index is not None
        cf=collaborative_index.score(profile,item)
        if strategy=="collaborative":return cf
        assert tfidf_index is not None
        content=score_hybrid(profile,item,tfidf_index)
        return content if cf<=0 else 0.5*content+0.5*cf
    candidates=[x for x in catalog if x.is_available and x.key not in profile.completed_item_keys and x.key not in profile.seen_item_keys]
    ranked=sorted(candidates,key=lambda x:(-score(x),x.key))
    result=[]
    for item in ranked[:limit]:
        reason,next_step=explain(profile,item)
        result.append(Recommendation(item,round(score(item),6),reason,next_step))
    return result
