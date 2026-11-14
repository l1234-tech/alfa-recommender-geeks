# Recommendation Engine

Независимая от FastAPI логика рекомендаций. Этот пакет содержит только ML/Data Science часть проекта.

## Реализованные модули

- `models.py` — контракты каталога, профиля и рекомендации; ключ объекта — `(item_type, item_id)`.
- `data_processing/` — нормализация каталога, SQL-извлечение открытых метаданных и взаимодействий, построение профилей.
- `algorithms/` — metadata baseline, TF-IDF, content hybrid и item-item collaborative filtering.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов.
- `explanations.py` — объяснение рекомендаций и следующий шаг.
- `evaluation/metrics.py` — Precision@K, Recall@K, NDCG@K и catalog coverage.
- `evaluation/temporal.py` — temporal holdout с типизированной тестовой релевантностью и train-набором для CF.
- `evaluation/compare.py` — сравнение четырёх стратегий, общие метрики и срезы по типам положительных событий.
- `evaluation/cold_start.py` — benchmark onboarding-only профилей на вручную заданных тест-кейсах.
- `evaluation/sensitivity.py` — validation-only перебор порога положительного рейтинга и параметров item-item CF.

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

## Офлайн-эксперименты

`compare_content_models(events, catalog, k=10)` сравнивает metadata baseline, TF-IDF hybrid, item-item CF и content+CF hybrid на одинаковых временных разбиениях. Результат содержит общие Precision@K, Recall@K, NDCG@K, число пользователей и catalog coverage; также добавляются отдельные метрики по типам положительных событий.

`evaluate_cf_sensitivity(events, catalog, ...)` сравнивает item-item CF и content+CF hybrid на сетке порога рейтинга, min co-occurrence и shrinkage. Это инструмент выбора параметров на temporal validation, не финальная test-оценка.

`evaluate_cold_start_cases(cases, catalog, k=5)` оценивает onboarding-only профили без истории взаимодействий. `ColdStartCase` содержит профиль и ожидаемые релевантные ключи материалов. Эти кейсы являются синтетическими экспертными фикстурами, а не реальными наблюдениями пользователей.

## Ограничения

- Веса гибридных моделей, CF shrinkage и порог рейтинга 4 — стартовые гипотезы, не обученные параметры.
- События разных типов отражают разные стадии воронки; раздельные срезы не заменяют полноценную модель вероятности конверсии.
- TF-IDF строится по текущему каталогу; исторические снимки каталога не подготовлены.
- Cold-start benchmark зависит от качества вручную заданных кейсов и требует экспертной проверки.
- Фактические метрики на реальной БД не заявляются до запуска эксперимента на разрешённой выгрузке.
- UserId и IP не используются в признаках и не должны логироваться. Закрытое содержимое платных материалов не извлекается.

Это исследовательский MVP, а не production-модель.
