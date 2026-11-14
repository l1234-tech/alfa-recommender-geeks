# Recommendation Engine

Независимая от FastAPI логика рекомендаций.

## Реализованные модули

- `models.py` — контракты профиля, материала и рекомендации.
- `data_processing/catalog.py`, `postgres_catalog.py`, `catalog.sql` — нормализация и извлечение открытых метаданных каталога.
- `data_processing/interactions.py`, `interactions.sql` — извлечение оценок и прогресса.
- `data_processing/profiles.py` — агрегация onboarding и положительной истории в профиль.
- `algorithms/content_baseline.py` — прозрачный metadata baseline.
- `algorithms/tfidf.py` — TF-IDF индекс по открытым метаданным.
- `algorithms/hybrid.py` — комбинация TF-IDF и metadata baseline.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов и сортировка.
- `explanations.py` — объяснение причин и следующий шаг.
- `evaluation/metrics.py` — Precision@K, Recall@K, NDCG@K.
- `evaluation/temporal.py` — временное разделение событий по пользователям.
- `evaluation/evaluate.py` — агрегатная офлайн-оценка baseline.
- `evaluation/compare.py` — сравнение baseline и TF-IDF hybrid на одинаковых temporal splits.
- `data_processing/audit_sql_dump.py` — безопасный агрегатный аудит plain SQL dump.

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

## Запуск извлечения

Функции `load_catalog(connection)` и `load_interactions(connection)` принимают уже созданное psycopg-соединение. Подключение и секреты намеренно остаются на стороне backend/локального окружения. Требуется `psycopg[binary]==3.2.3`.

## Построение профиля и оценка

`build_user_profile(events, catalog, onboarding=...)` объединяет onboarding с темами/тегами/отраслями материалов из положительной истории. По умолчанию положительными считаются оценки 4–5 и подтверждённое завершение курса/урока. Сырые UserId остаются только внутри пайплайна.

`evaluate_content_baseline(events, catalog, k=10)` выполняет per-user temporal holdout и возвращает только агрегированные метрики. Повторные материалы, уже присутствующие в train, исключаются из тестовой релевантности, поскольку ranking подавляет ранее просмотренные элементы.

## Сравнение алгоритмов

`recommend(..., strategy="baseline")` использует простой baseline; `recommend(..., strategy="hybrid")` включает TF-IDF + metadata overlap. Для сравнения на одинаковых временных разбиениях используйте `compare_content_models(events, catalog, k=10)` из `recommender.evaluation.compare`. TF-IDF реализован на стандартной библиотеке Python и не добавляет runtime-зависимостей.

## Ограничения текущей версии

- Веса baseline равные и не обучены.
- Порог рейтинга 4 — стартовая гипотеза, требует анализа чувствительности.
- События разных типов пока используются как бинарные позитивные сигналы в общей оценке; отдельно по типам их ещё нужно сравнить.
- Нет collaborative filtering и negative sampling.
- Нет оценки качества на реальном PostgreSQL окружении в CI.
- Идентификаторы пользователей и IP не используются в признаках и не должны логироваться.
- Закрытое содержимое платных материалов не извлекается.

Это воспроизводимый исследовательский MVP, а не production-модель.

## Коллаборативная фильтрация

Добавлен item-item CF в `algorithms/collaborative.py`. Индекс строится только по высоким оценкам и подтверждённым завершениям, использует cosine similarity бинарных историй и significance weighting. Сырые user_id не сохраняются в индексе.

Доступные стратегии ранжирования:
- `baseline` — метаданные;
- `hybrid` — TF-IDF + метаданные;
- `collaborative` — item-item CF;
- `content_cf_hybrid` — контент + CF с fallback на контент при отсутствии CF-сигнала.

`evaluation/compare.py` сравнивает все четыре стратегии на одинаковых temporal splits. Для каждого тестового пользователя CF обучается только на событиях, предшествующих началу его test-периода. Подробности и ограничения: `docs/collaborative_filtering.md`.

Проверка на реальном SQL-дампе и запуск тестов пока не выполнены; численные выводы о качестве моделей не делаются.
