# Recommendation Engine

Независимая от FastAPI логика рекомендаций. Этот пакет содержит только ML/Data Science часть проекта.

## Реализованные модули

- `models.py` — контракты каталога, профиля и рекомендации; ключ объекта — `(item_type, item_id)`.
- `data_processing/` — нормализация каталога, SQL-извлечение открытых метаданных и взаимодействий, построение профилей.
- `algorithms/` — metadata baseline, TF-IDF, content hybrid и item-item collaborative filtering.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов; опциональный MMR reranking.
- `algorithms/diversity.py` — Jaccard-похожесть метаданных и Maximal Marginal Relevance.
- `explanations.py` — объяснение рекомендаций и следующий шаг.
- `evaluation/metrics.py` — Precision@K, Recall@K, NDCG@K, catalog coverage, Intra-List Diversity и разнообразие тем/типов.
- `evaluation/temporal.py` — temporal holdout с типизированной тестовой релевантностью и train-набором для CF.
- `evaluation/compare.py` — сравнение четырёх базовых стратегий и MMR-вариантов на одинаковых temporal validation splits; ranking, coverage, diversity и срезы по типам событий.
- `evaluation/cold_start.py` — benchmark onboarding-only профилей на вручную заданных тест-кейсах.
- `evaluation/sensitivity.py` — validation-only перебор порога положительного рейтинга и параметров item-item CF.

`recommend(..., diversity_weight=0.25)` включает MMR: чем выше вес, тем сильнее штраф за сходство с уже выбранными материалами. Значение `0.0` сохраняет исходное ранжирование и используется по умолчанию.

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

## Офлайн-эксперименты

`compare_content_models(events, catalog, k=10, diversity_weights=(0.15, 0.25, 0.35))` сравнивает четыре базовые стратегии и MMR-варианты content+CF hybrid на одинаковых temporal validation splits. Для каждой стратегии считаются Precision@K, Recall@K, NDCG@K, catalog coverage, Intra-List Diversity и среднее число уникальных тем/типов в списке.

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
