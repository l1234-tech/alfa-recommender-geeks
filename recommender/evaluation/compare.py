"""Compare recommendation strategies on shared temporal splits."""
from __future__ import annotations
from collections.abc import Iterable
from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend
def compare_content_models(events:Iterable[UserInteraction],catalog:list[CatalogItem],*,k:int=10)->dict[str,dict[str,float]]:
    rows=list(events); splits=temporal_holdout(rows); tfidf=TfidfIndex.fit(catalog)
    outputs={name:[] for name in ("metadata_baseline","tfidf_hybrid","item_item_cf","content_cf_hybrid")}
    relevant=[]
    for split in splits:
        profile=build_user_profile(split.train_events,catalog)
        cf=ItemItemIndex.fit(split.collaborative_train_events,catalog)
        for strategy in outputs:
            recs=recommend(profile,catalog,limit=k,strategy=strategy,tfidf_index=tfidf,collaborative_index=cf)
            outputs[strategy].append([r.item.key for r in recs])
        relevant.append(set(split.test_relevant_item_keys))
    return {name:aggregate_ranking_metrics(pred,relevant,k) for name,pred in outputs.items()}
