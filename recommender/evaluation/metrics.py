"""Ranking and catalog-coverage metrics for offline evaluation."""
from __future__ import annotations
import math
from collections.abc import Iterable,Sequence
from typing import Hashable
Item=Hashable
def precision_at_k(recommended:Sequence[Item],relevant:set[Item],k:int)->float:
    if k<=0:return 0.0
    return sum(x in relevant for x in recommended[:k])/k
def recall_at_k(recommended:Sequence[Item],relevant:set[Item],k:int)->float:
    if k<=0 or not relevant:return 0.0
    return sum(x in relevant for x in recommended[:k])/len(relevant)
def ndcg_at_k(recommended:Sequence[Item],relevant:set[Item],k:int)->float:
    if k<=0 or not relevant:return 0.0
    dcg=sum(1/math.log2(rank+2) for rank,x in enumerate(recommended[:k]) if x in relevant)
    ideal=min(len(relevant),k)
    idcg=sum(1/math.log2(rank+2) for rank in range(ideal))
    return dcg/idcg if idcg else 0.0
def aggregate_ranking_metrics(recommendations:Iterable[Sequence[Item]],relevant_sets:Iterable[set[Item]],k:int=10)->dict[str,float]:
    pairs=list(zip(recommendations,relevant_sets))
    if not pairs:return {"users_evaluated":0.0,f"precision@{k}":0.0,f"recall@{k}":0.0,f"ndcg@{k}":0.0}
    return {"users_evaluated":float(len(pairs)),
        f"precision@{k}":sum(precision_at_k(r,s,k) for r,s in pairs)/len(pairs),
        f"recall@{k}":sum(recall_at_k(r,s,k) for r,s in pairs)/len(pairs),
        f"ndcg@{k}":sum(ndcg_at_k(r,s,k) for r,s in pairs)/len(pairs)}
def catalog_coverage(recommendations:Iterable[Sequence[Item]],available_catalog:Iterable[Item])->dict[str,float]:
    catalog=set(available_catalog)
    recommended={item for row in recommendations for item in row if item in catalog}
    return {"available_items":float(len(catalog)),"recommended_unique_items":float(len(recommended)),
            "catalog_coverage":len(recommended)/len(catalog) if catalog else 0.0}
