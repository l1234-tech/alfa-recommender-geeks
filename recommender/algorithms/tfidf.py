"""Dependency-free TF-IDF retrieval over public catalog metadata."""
from __future__ import annotations
import math,re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable
from recommender.models import CatalogItem,ItemKey,UserProfile
TOKEN_RE=re.compile(r"[\w-]+",re.UNICODE)
STOP_WORDS=frozenset({"для","это","как","что","или","при","над","под","без","the","and","for","with","from","that","this","are","was"})
def tokenize(text:str)->list[str]:
    return [t.casefold() for t in TOKEN_RE.findall(text) if len(t)>2 and t.casefold() not in STOP_WORDS]
def profile_query(profile:UserProfile)->str:
    vals=[*sorted(profile.topics),*sorted(profile.tags),*sorted(profile.industries),*sorted(profile.preferred_types),profile.current_goal]
    return " ".join(v for v in vals if v)
@dataclass(frozen=True)
class TfidfIndex:
    item_keys:tuple[ItemKey,...]
    vectors:dict[ItemKey,dict[str,float]]
    norms:dict[ItemKey,float]
    idf:dict[str,float]
    @classmethod
    def fit(cls,catalog:Iterable[CatalogItem])->"TfidfIndex":
        items=list(catalog); dfs=Counter(); tokenized={}
        for item in items:
            txt=" ".join((item.title,item.description,*item.topics,*item.tags,*item.industries))
            counts=Counter(tokenize(txt)); tokenized[item.key]=counts; dfs.update(counts.keys())
        total=max(len(items),1); idf={t:math.log((total+1)/(f+1))+1 for t,f in dfs.items()}
        vectors={}; norms={}
        for key,counts in tokenized.items():
            vec={t:(1+math.log(c))*idf[t] for t,c in counts.items()}
            vectors[key]=vec; norms[key]=math.sqrt(sum(v*v for v in vec.values()))
        return cls(tuple(x.key for x in items),vectors,norms,idf)
    def score(self,profile:UserProfile,item:CatalogItem|ItemKey)->float:
        key=item.key if isinstance(item,CatalogItem) else item
        counts=Counter(tokenize(profile_query(profile)))
        if not counts:return 0.0
        query={t:(1+math.log(c))*self.idf[t] for t,c in counts.items() if t in self.idf}
        vec=self.vectors.get(key,{}); qn=math.sqrt(sum(v*v for v in query.values())); n=self.norms.get(key,0)
        if not qn or not n:return 0.0
        dot=sum(v*vec.get(t,0.0) for t,v in query.items())
        return max(0.0,min(1.0,dot/(qn*n)))
