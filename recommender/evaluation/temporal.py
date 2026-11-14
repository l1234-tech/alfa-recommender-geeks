"""Per-user temporal holdout without exposing user identifiers in reports."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from typing import Iterable
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import is_positive_event
from recommender.models import ItemKey
@dataclass(frozen=True)
class UserTemporalSplit:
    train_events:tuple[UserInteraction,...]
    test_relevant_item_keys:frozenset[ItemKey]
    collaborative_train_events:tuple[UserInteraction,...]=()
def _utc_sort_value(value:datetime|None)->datetime:
    if value is None:return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
def temporal_holdout(events:Iterable[UserInteraction],*,positive_rating_threshold:int=4,
                     holdout_fraction:float=0.2,min_train_events:int=1)->list[UserTemporalSplit]:
    if not 0<holdout_fraction<1:raise ValueError("holdout_fraction must be between 0 and 1")
    all_events=list(events); grouped={}
    for e in all_events:grouped.setdefault(e.user_id,[]).append(e)
    splits=[]
    for rows in grouped.values():
        ordered=sorted(rows,key=lambda e:_utc_sort_value(e.event_at))
        if len(ordered)<=min_train_events:continue
        size=max(1,math_ceil(len(ordered)*holdout_fraction)); size=min(size,len(ordered)-min_train_events)
        train,test=ordered[:-size],ordered[-size:]; train_keys={e.item_key for e in train}
        relevant=frozenset(e.item_key for e in test if is_positive_event(e,positive_rating_threshold) and e.item_key not in train_keys)
        if not relevant:continue
        boundary=min(_utc_sort_value(e.event_at) for e in test)
        cf_train=tuple(e for e in all_events if _utc_sort_value(e.event_at)<boundary)
        splits.append(UserTemporalSplit(tuple(train),relevant,cf_train))
    return splits
def math_ceil(value:float)->int:
    integer=int(value); return integer if integer==value else integer+1
