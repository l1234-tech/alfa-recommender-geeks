# Analytics / QA

Тестовые профили, метрики, выгрузка данных и сравнение алгоритмов с бейзлайном.

```
analytics/
  export_catalog.py            — выгрузка каталога и записей на курсы из базы в data/raw/*.csv
  profiles/test_profiles.json  — 15 тестовых профилей с ожиданиями
  fixtures/mock_catalog.json   — синтетический каталог (та же схема, что у выгрузки)
  config.py                    — группы тем (THEME_MAP), стадии, ключевые слова
  catalog.py                   — загрузка каталога (csv/json), чистка латиницы в русских словах
  history.py                   — синтетическая история
  metrics.py                   — метрики и проверки
  recommenders.py              — бейзлайны и адаптеры (API / python-функция)
  evaluate.py                  — прогон тестовых профилей → reports/report.md
  offline_eval.py              — leave-one-out на реальных записях → reports/offline_eval.md
```
Заметки по данным: `docs/data_notes.md`. Методика и результаты: `docs/experiments.md`.

## 1. Поднять базу и выгрузить данные (один раз)

Дамп сделан `pg_dump` 17, поэтому нужен PostgreSQL 17+:

```bash
docker run -d --name alfa-db -e POSTGRES_PASSWORD=pg -p 5432:5432 postgres:17
docker cp alfa_course_hackathon.backup alfa-db:/tmp/db.backup
docker exec alfa-db createdb -U postgres courses
docker exec alfa-db pg_restore -U postgres -d courses --no-owner /tmp/db.backup

pip install psycopg2-binary==2.9.10
python -m analytics.export_catalog --dsn postgresql://postgres:pg@localhost:5432/courses
# -> data/raw/catalog.csv, data/raw/interactions.csv (в git не коммитим)
```

Колонки `catalog.csv`: `material_id, format (course/article/document/webinar/podcast), title,
description, topics, tags, industries` (списки через `|`), `level (beginner/experienced/пусто),
access (free/paid/subscription), is_paid, is_closed, duration_min, rating, signal, url, popularity`.

## 2. Оценка

```bash
# тестовые профили: бейзлайны на реальном каталоге (если его нет — на мок-каталоге)
python -m analytics.evaluate

# наш бэкенд против бейзлайна
python -m analytics.evaluate --algo topic_baseline --algo api=http://localhost:8000/api/v1/recommendations

# функция алгоритма напрямую, без бэкенда
python -m analytics.evaluate --algo topic_baseline --algo py=recommender.ranking:recommend

# реальное поведение (leave-one-out)
python -m analytics.offline_eval --algo api=http://localhost:8000/api/v1/recommendations --max-users 300

# тесты (контрактные пропускаются, пока нет эндпоинта)
pytest
RECO_API_URL=http://localhost:8000 pytest tests/test_recommendations_contract.py
```

Функция для `py=` должна иметь вид `recommend(user, history, k=5, catalog=None)` и возвращать
список словарей с `material_id`, `reason`, `next_step` (или `{"recommendations": [...]}`).
`history` — список `{"material_id", "event"}`, где event это view/complete/purchase.
