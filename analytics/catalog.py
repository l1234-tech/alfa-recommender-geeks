import csv
import json
import re
from pathlib import Path

from analytics.config import STAGE_TAGS, THEME_MAP

MOCK_CATALOG = Path(__file__).parent / "fixtures" / "mock_catalog.json"

# в базе встречаются латинские буквы внутри русских слов: «Маркeтплейсы», «HoReСa»
_LATIN_TO_CYR = str.maketrans("aeopcxyAEOPCXHKMBT", "аеорсхуАЕОРСХНКМВТ")
_CYR_TO_LATIN = str.maketrans("аеорсхуАЕОРСХНКМВТ", "aeopcxyAEOPCXHKMBT")


def fix_homoglyphs(text):
    words = []
    for w in str(text).split(" "):
        cyr = len(re.findall(r"[а-яё]", w, re.I))
        lat = len(re.findall(r"[a-z]", w, re.I))
        if cyr and lat:
            w = w.translate(_LATIN_TO_CYR) if cyr >= lat else w.translate(_CYR_TO_LATIN)
        words.append(w)
    return " ".join(words)


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [fix_homoglyphs(v).strip() for v in value if v]
    return [fix_homoglyphs(v).strip() for v in str(value).split("|") if v.strip()]


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "да"}


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_item(raw):
    topics = _to_list(raw.get("topics"))
    tags = _to_list(raw.get("tags"))
    stages = {STAGE_TAGS[t] for t in tags if t in STAGE_TAGS}
    return {
        "material_id": str(raw["material_id"]),
        "title": raw.get("title", ""),
        "format": raw.get("format", ""),
        "topics": topics,
        "tags": tags,
        "themes": {THEME_MAP.get(t, t) for t in topics},
        "industries": _to_list(raw.get("industries")),
        "level": raw.get("level") or "",
        # если у материала и «старт», и «развитие» — стадию не считаем известной
        "stage": stages.pop() if len(stages) == 1 else "",
        "is_paid": _to_bool(raw.get("is_paid")),
        "is_closed": _to_bool(raw.get("is_closed")),
        "duration_min": _to_float(raw.get("duration_min")),
        "popularity": _to_float(raw.get("popularity"), 0.0),
    }


def load_catalog(path=None):
    path = Path(path) if path else MOCK_CATALOG
    if path.suffix == ".csv":
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    return [normalize_item(r) for r in rows]
