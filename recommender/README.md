# Recommendation Engine

Независимая от FastAPI логика рекомендаций. Этот пакет содержит только ML/Data Science часть проекта.

## Реализованные модули

- `models.py` — контракты каталога, профиля и рекомендации; ключ объекта — `(item_type, item_id)`.
- `data_processing/` — нормализация каталога, SQL-извлечение открытых метаданных и взаимодействий, построение профилей.
- `algorithms/` — metadata baseline, TF-IDF, content hybrid и item-item collaborative filtering.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов; опциональный MMR reranking и настройка весов гибридных моделей.
- `algorithms/diversity.py` — Jaccard-похожесть метаданных и Maximal Marginal Relevance.
- `explanations.py` — объяснение рекомендаций и следующий шаг.
- `evaluation/metrics.py` — Precision@K, Recall@K, NDCG@K, catalog coverage, Intra-List Diversity и разнообразие тем/типов.
- `evaluation/temporal.py` — temporal holdout с типизированной тестовой релевантностью и train-набором для CF.
- `evaluation/compare.py` — сравнение базовых стратегий и MMR-вариантов на одинаковых temporal validation splits.
- `evaluation/cold_start.py` — benchmark onboarding-only профилей на вручную заданных тест-кейсах.
- `evaluation/sensitivity.py` — validation-only перебор порога положительного рейтинга и параметров item-item CF.
- `evaluation/tuning.py` — validation-only подбор весов TF-IDF/метаданных и Content/CF.

`recommend(..., diversity_weight=0.25)` включает MMR. Значение `0.0` сохраняет исходное ранжирование.
Параметр `tfidf_weight` задаёт долю TF-IDF в контентном гибриде, а `content_weight` — долю контентной модели в Content+CF. По умолчанию сохранены прежние веса 0.65 и 0.5.

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

## Офлайн-эксперименты

`tune_hybrid_weights(events, catalog, k=10)` перебирает веса на одинаковых temporal validation splits и возвращает агрегированные метрики Precision@K, Recall@K, NDCG@K, catalog coverage и diversity. Первая группа строк сравнивает TF-IDF/metadata; вторая — дополнительно Content/CF. Результат предназначен для выбора кандидата на validation, а не для заявления независимого test-качества.

`compare_content_models(...)` сравнивает стратегии и MMR. `evaluate_cf_sensitivity(...)` исследует параметры CF. `evaluate_cold_start_cases(...)` оценивает экспертные onboarding-only кейсы.

## Ограничения

- Подбор весов выполняется на validation; для независимой итоговой оценки нужен отдельный нетронутый test-период.
- TF-IDF строится по текущему каталогу; исторические снимки каталога не подготовлены, поэтому возможна утечка каталожной информации.
- События рейтинга и завершения отражают разные стадии воронки; раздельные срезы не заменяют модель вероятности конверсии.
- Cold-start benchmark зависит от качества вручную заданных кейсов и требует экспертной проверки.
- Фактические метрики на реальной БД не заявляются до запуска эксперимента на разрешённой выгрузке.
- UserId и IP не используются в признаках и не должны логироваться. Закрытое содержимое платных материалов не извлекается.

Это исследовательский MVP, а не production-модель.
