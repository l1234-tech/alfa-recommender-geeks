"""Privacy-conscious item-item collaborative filtering."""
from __future__ import annotations
from collections import defaultdict
from collections.abc import Iterable
from math import sqrt
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import is_positive_event
from recommender.models import CatalogItem, ItemKey, UserProfile
class ItemItemIndex:
    def __init__(self, similarities: dict[ItemKey,dict[ItemKey,float]], support: dict[ItemKey,int]):
        self._similarities=similarities; self._support=support
    @classmethod
    def fit(cls, events: Iterable[UserInteraction], catalog: Iterable[CatalogItem], *,
            positive_rating_threshold:int=4,min_cooccurrence:int=2,shrinkage:float=5.0)->"ItemItemIndex":
        if min_cooccurrence<1: raise ValueError("min_cooccurrence must be at least 1")
        if shrinkage<0: raise ValueError("shrinkage must be non-negative")
        valid={x.key for x in catalog if x.is_available}
        user_items=defaultdict(set)
        for e in events:
            if e.item_key in valid and is_positive_event(e,positive_rating_threshold): user_items[e.user_id].add(e.item_key)
        item_users=defaultdict(set)
        for uid,keys in user_items.items():
            for key in keys: item_users[key].add(uid)
        support={key:len(users) for key,users in item_users.items()}
        counts=defaultdict(lambda:defaultdict(int))
        for keys in user_items.values():
            ordered=sorted(keys)
            for i,left in enumerate(ordered):
                for right in ordered[i+1:]: counts[left][right]+=1; counts[right][left]+=1
        sims=defaultdict(dict)
        for left,neighbors in counts.items():
            for right,count in neighbors.items():
                if count<min_cooccurrence: continue
                denom=sqrt(support[left]*support[right])
                cosine=count/denom if denom else 0.0
                sims[left][right]=cosine*count/(count+shrinkage)
        return cls(dict(sims),support)
    def score(self,profile:UserProfile,candidate:CatalogItem|ItemKey)->float:
        key=candidate.key if isinstance(candidate,CatalogItem) else candidate
        history=profile.positive_item_keys
        if not history:return 0.0
        vals=[self._similarities.get(src,{}).get(key,0.0) for src in history if src!=key]
        return sum(vals)/len(history)
    def has_neighbors(self,item:CatalogItem|ItemKey)->bool:
        key=item.key if isinstance(item,CatalogItem) else item
        return bool(self._similarities.get(key))
    @property
    def item_count(self)->int:return len(self._support)
