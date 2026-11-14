# Recommendation Engine

Независимая от FastAPI логика рекомендаций. Этот пакет содержит только ML/Data Science часть проекта.

## Реализованные модули

- `models.py` — контракты каталога, профиля и рекомендации; ключ объекта — `(item_type, item_id)`.
- `data_processing/catalog.py`, `postgres_catalog.py`, `catalog.sql` — нормализация и извлечение открытых метаданных каталога.
- `data_processing/interactions.py`, `interactions.sql` — извлечение оценок и прогресса.
- `data_processing/profiles.py` — агрегация onboarding и положительной истории в профиль.
- `algorithms/content_baseline.py` — прозрачный metadata baseline.
- `algorithms/tfidf.py` — TF-IDF индекс по открытым метаданным.
- `algorithms/hybrid.py` — комбинация TF-IDF и metadata baseline.
- `algorithms/collaborative.py` — item-item collaborative filtering по типизированным ключам.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов и сортировка.
- `explanations.py` — объяснение причин и следующий шаг.
- `evaluation/metrics.py` — Precision@K, Recall@K, NDCG@K.
- `evaluation/temporal.py` — временное разделение событий по пользователям.
- `evaluation/evaluate.py` — агрегатная офлайн-оценка baseline.
- `evaluation/compare.py` — сравнение четырёх стратегий на одинаковых temporal splits.

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

## ML-пайплайн

`load_catalog(connection)` и `load_interactions(connection)` принимают уже созданное psycopg-соединение; управление подключением и секретами остаётся вне ML-пакета.

`build_user_profile(events, catalog, onboarding=...)` объединяет onboarding с темами/тегами/отраслями материалов из положительной истории. По умолчанию положительными считаются оценки 4–5 и подтверждённое завершение курса/урока. Сырые UserId остаются только внутри пайплайна.

`recommend(..., strategy=...)` поддерживает:
- `baseline` — metadata overlap;
- `hybrid` — TF-IDF + metadata overlap;
- `collaborative` — item-item CF;
- `content_cf_hybrid` — контент + CF с fallback на контент при отсутствии CF-сигнала.

`compare_content_models(events, catalog, k=10)` сравнивает все четыре стратегии на одинаковых временных разбиениях. Для каждого тестового пользователя CF обучается только на событиях, предшествующих его тестовому периоду.

## Ограничения

- Веса гибридных моделей, CF shrinkage и порог рейтинга 4 — стартовые гипотезы, не обученные параметры.
- События разных типов пока используются как бинарные позитивные сигналы; нужны отдельные срезы по типам событий.
- TF-IDF индекс строится по текущему каталогу целиком; исторические снимки каталога не подготовлены.
- Нет negative sampling и подтверждённой оценки качества на реальном PostgreSQL окружении в CI.
- Численные выводы о качестве моделей не делаются до фактического запуска эксперимента.
- Идентификаторы пользователей и IP не используются в признаках и не должны логироваться.
- Закрытое содержимое платных материалов не извлекается.

Это исследовательский MVP, а не production-модель.
