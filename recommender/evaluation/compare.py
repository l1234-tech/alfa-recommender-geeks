"""Compare recommendation strategies on shared temporal splits."""
from __future__ import annotations
from collections.abc import Iterable
from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile
from recommender.evaluation.metrics import aggregate_ranking_metrics,catalog_coverage
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem
from recommender.ranking import recommend
def compare_content_models(events:Iterable[UserInteraction],catalog:list[CatalogItem],*,k:int=10)->dict[str,dict[str,float]]:
    rows=list(events); splits=temporal_holdout(rows); tfidf=TfidfIndex.fit(catalog)
    names=("metadata_baseline","tfidf_hybrid","item_item_cf","content_cf_hybrid")
    outputs={name:[] for name in names}; relevant=[]; type_relevant={}
    for split in splits:
        profile=build_user_profile(split.train_events,catalog)
        cf=ItemItemIndex.fit(split.collaborative_train_events,catalog)
        split_predictions={}
        for strategy in names:
            recs=recommend(profile,catalog,limit=k,strategy=strategy,tfidf_index=tfidf,collaborative_index=cf)
            keys=[r.item.key for r in recs]; outputs[strategy].append(keys); split_predictions[strategy]=keys
        relevant.append(set(split.test_relevant_item_keys))
        for event_type in {e.event_type for e in split.test_positive_events}:
            type_relevant.setdefault(event_type,[]).append(set(e.item_key for e in split.test_positive_events if e.event_type==event_type))
        for event_type in type_relevant:
            # Keep each event-type metric aligned to the split index; empty relevance is a valid zero-hit slice.
            if len(type_relevant[event_type]) < len(relevant):
                type_relevant[event_type].append(set())
    available={x.key for x in catalog if x.is_available}
    result={}
    for strategy,predictions in outputs.items():
        metrics=aggregate_ranking_metrics(predictions,relevant,k)
        metrics.update(catalog_coverage(predictions,available))
        for event_type,sets in type_relevant.items():
            # Only evaluate users with at least one positive event of this type.
            paired=[(pred,rel) for pred,rel in zip(predictions,sets) if rel]
            if paired:
                slice_metrics=aggregate_ranking_metrics([p for p,_ in paired],[r for _,r in paired],k)
                metrics.update({f"{event_type}_{name}":value for name,value in slice_metrics.items()})
            else:
                metrics[f"{event_type}_users_evaluated"]=0.0
        result[strategy]=metrics
    return result
