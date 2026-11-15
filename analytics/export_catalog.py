"""Выгрузка каталога и взаимодействий из базы courses_for_bu в CSV.

Нужна восстановленная база (см. analytics/README.md). Результат пишется в data/raw/,
эта папка в .gitignore — выгрузку в git не коммитим.

    python -m analytics.export_catalog --dsn postgresql://postgres:pg@localhost:5432/courses
"""
import argparse
import csv
import math
import os
import re
from html import unescape
from pathlib import Path

import psycopg2

from analytics.catalog import fix_homoglyphs

# EntityTypeId из ContentSettings / UserRatings / RecommendedItems
ENTITY_TYPES = {
    "8b440b1a-00c3-423a-9bae-3376475eb203": "course",
    "8ede4179-0faf-407d-a4fc-1d94f9a63089": "article",
    "da1ad865-8605-4ab1-9f6c-4489a26fbc35": "document",
    "ece4acf3-5dd3-47b9-9f08-99c0d6203cc7": "webinar",
    "142c23e2-bf71-4a73-b12e-6b1b5e4d47cc": "podcast",
}
PUBLISHED = "Опубликовано"

# в таблице Industries вперемешку лежат отрасли, опыт и промо-метки
EXPERIENCE = {"Без опыта": "beginner", "С опытом": "experienced"}
NOT_INDUSTRY = {"Актуальное 🔥", "Альфа-Банк", "💥 Альфа-Курс", "Alfa Students", "For you", "Marketplace",
                "💥 NEW", "⚡️ Популярное", "Татмолодежь.Бизнес"}

MATERIALS_SQL = """
select c."Id", 'course', c."Title", c."Description", c."Duration", c."Url",
       (c."Cost" is not null) as paid, (ct."Title" = 'По подписке') as subscription, c."Rating", c."IsClosed"
from "Courses" c
join "Statuses" s on s."Id" = c."StatusId"
left join "CourseTypes" ct on ct."Id" = c."TypeId"
where not c."IsDeleted" and s."Title" = %(pub)s
union all
select a."Id", 'article', a."Title", coalesce(a."CardDescription", a."Description"), a."Duration", a."Url",
       false, not a."IsPublic", null, a."IsClosed"
from "Articles" a join "Statuses" s on s."Id" = a."StatusId"
where not a."IsDeleted" and not a."IsLesson" and s."Title" = %(pub)s
union all
select d."Id", 'document', d."Title", d."Description", null, d."Url", false, false, null, false
from "Documents" d join "Statuses" s on s."Id" = d."StatusId"
where not d."IsDeleted" and s."Title" = %(pub)s
union all
select w."Id", 'webinar', w."Title", w."Description", w."Duration", w."Url", false, false, w."Rating", w."IsClosed"
from "Webinars" w join "Statuses" s on s."Id" = w."StatusId"
where not w."IsDeleted" and s."Title" = %(pub)s
union all
select p."Id", 'podcast', p."Title", p."Description", p."Duration", p."Url",
       (p."Cost" is not null), false, p."Rating", p."IsClosed"
from "Podcasts" p join "Statuses" s on s."Id" = p."StatusId"
where not p."IsDeleted" and s."Title" = %(pub)s
"""

LABELS_SQL = """
select cs."EntityId", '{kind}', t."Title"
from "ContentSettings" cs
join "{bind}" b on b."ContentSettingsId" = cs."Id"
join "{table}" t on t."Id" = b."{fk}"
where not t."IsDeleted"
order by cs."EntityId", b."Order" nulls last
"""

ENROLL_SQL = """select "CourseId", count(*) from "CourseUserBindings" where not "IsDeleted" group by 1"""
REFS_SQL = """select "ItemId", count(*) from "RecommendedItems" group by 1"""

INTERACTIONS_SQL = """
select "UserId", "CourseId", "IsCompleted", "IsPaid", "LessonsCompleted",
       coalesce("StudyingStartDate", "BuyingDate") as ts
from "CourseUserBindings"
where not "IsDeleted"
order by "UserId", ts nulls first
"""


def clean_html(text, limit=300):
    if not text:
        return ""
    text = unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_duration(text):
    """'1 час 25 минут' / '3,5 часа' / '~2 часа' / '7 минут' -> минуты."""
    if not text:
        return ""
    text = text.lower().replace(",", ".")
    total = 0.0
    hours = re.search(r"(\d+(?:\.\d+)?)\s*час", text)
    minutes = re.search(r"(\d+)\s*мин", text)
    if hours:
        total += float(hours.group(1)) * 60
    if minutes:
        total += int(minutes.group(1))
    return int(total) if total else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.getenv("SOURCE_DB_DSN", "postgresql://postgres:pg@localhost:5432/courses"))
    parser.add_argument("--out", default="data/raw")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    con = psycopg2.connect(args.dsn)
    cur = con.cursor()

    cur.execute(MATERIALS_SQL, {"pub": PUBLISHED})
    materials = cur.fetchall()

    labels = {}
    for kind, bind, table, fk in [("topics", "ContentSettingsTopics", "Topics", "TopicId"),
                                  ("tags", "ContentSettingsTags", "Tags", "TagId"),
                                  ("industries", "ContentSettingsIndustries", "Industries", "IndustryId")]:
        cur.execute(LABELS_SQL.format(kind=kind, bind=bind, table=table, fk=fk))
        for entity_id, k, title in cur.fetchall():
            labels.setdefault(entity_id, {}).setdefault(k, []).append(fix_homoglyphs(title).strip())

    cur.execute(ENROLL_SQL)
    enrolls = dict(cur.fetchall())
    cur.execute(REFS_SQL)
    refs = dict(cur.fetchall())

    rows = []
    for mid, fmt, title, descr, duration, url, paid, subscription, rating, closed in materials:
        lab = labels.get(mid, {})
        inds = lab.get("industries", [])
        levels = [EXPERIENCE[i] for i in inds if i in EXPERIENCE]
        signal = enrolls.get(mid, 0) if fmt == "course" else refs.get(mid, 0)
        rows.append({
            "material_id": mid,
            "format": fmt,
            "title": fix_homoglyphs(title).replace("\xa0", " "),
            "description": clean_html(descr),
            "topics": "|".join(dict.fromkeys(lab.get("topics", []))),
            "tags": "|".join(dict.fromkeys(lab.get("tags", []))),
            "industries": "|".join(i for i in dict.fromkeys(inds) if i not in EXPERIENCE and i not in NOT_INDUSTRY),
            "level": levels[0] if levels else "",
            "access": "paid" if paid else ("subscription" if subscription else "free"),
            "is_paid": paid or subscription,
            "is_closed": bool(closed),
            "duration_min": parse_duration(duration),
            "rating": rating if rating is not None else "",
            "signal": signal,
            "url": url or "",
        })

    top = max(math.log1p(r["signal"]) for r in rows) or 1
    for r in rows:
        r["popularity"] = round(math.log1p(r["signal"]) / top, 4)

    with open(out / "catalog.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    cur.execute(INTERACTIONS_SQL)
    with open(out / "interactions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "material_id", "is_completed", "is_paid", "lessons_completed", "ts"])
        writer.writerows(cur.fetchall())

    by_format = {}
    for r in rows:
        by_format[r["format"]] = by_format.get(r["format"], 0) + 1
    print(f"catalog.csv: {len(rows)} материалов {by_format}")
    print(f"interactions.csv: {cur.rowcount} записей")


if __name__ == "__main__":
    main()
