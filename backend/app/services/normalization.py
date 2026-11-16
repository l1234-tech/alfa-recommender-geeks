"""API/catalog vocabulary alignment. Theme groups reuse the analytics mapping."""
from analytics.config import THEME_MAP

_THEMES = {key.casefold(): value for key, value in THEME_MAP.items()}
_THEMES.update({"маркетинг": "marketing", "accounting": "finance"})
_VALUES = {"розничная торговля": "retail", "услуги": "services",
           "производство": "production", "старт бизнеса": "early",
           "начинающий": "beginner", "развитие бизнеса": "growth",
           "experienced": "intermediate"}
_GOALS = {"marketing": "маркетинг реклама", "finance": "финансы учет",
          "team": "управление командой"}

def normalize_topics(values):
    return frozenset(_THEMES.get(str(v).strip().casefold(), str(v).strip().casefold()) for v in values if str(v).strip())

def normalize_values(values):
    return frozenset(_VALUES.get(str(v).strip().casefold(), str(v).strip().casefold()) for v in values if str(v).strip())

def goal_text(value):
    text = (value or "").strip()
    return _GOALS.get(text.casefold(), text)
