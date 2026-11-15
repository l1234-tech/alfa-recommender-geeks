# Recommendation Engine

Независимая от FastAPI логика рекомендаций. Этот пакет содержит только ML/Data Science часть проекта.

## Реализованные модули

- `models.py` — контракты каталога, профиля и рекомендации; ключ объекта — `(item_type, item_id)`.
- `data_processing/` — нормализация каталога, SQL-извлечение открытых метаданных и построение профилей.
- `algorithms/` — metadata baseline, field-aware TF-IDF, content hybrid и item-item collaborative filtering.
- `ranking.py` — фильтрация недоступных, просмотренных и завершённых материалов; MMR и настраиваемые гибридные веса.
- `explanations.py` — объяснение рекомендаций и следующий шаг.
- `evaluation/` — temporal validation, ranking/coverage/diversity метрики, CF sensitivity, подбор гибридных весов и cold-start benchmark.

## Контентные признаки

TF-IDF использует только открытые Title, Description, Topics, Tags, Industries и тип материала. Заголовок получает умеренный 2x boost, структурные onboarding-поля усиливаются в запросе. Metadata baseline усредняет только поля, присутствующие и у профиля, и у кандидата. Дубликаты typed item keys при построении TF-IDF вызывают ошибку, а не тихую перезапись.

Эти коэффициенты — эвристики. Они должны сравниваться на validation и экспертных cold-start кейсах.

## Подбор и оценка

- `tune_hybrid_weights(...)` — validation-only подбор TF-IDF/metadata и Content/CF весов.
- `compare_content_models(...)` — сравнение стратегий и MMR на temporal splits.
- `evaluate_cf_sensitivity(...)` — чувствительность CF к порогу рейтинга, поддержке и shrinkage.
- `evaluate_cold_start_cases(...)` — экспертные onboarding-only кейсы.

Тесты запускаются из корня: `python -m unittest discover -s tests -v`.

## Ограничения

- Веса контентной модели и CF — экспериментальные, не обученные параметры.
- TF-IDF строится по текущему каталогу; исторический снимок каталога отсутствует.
- Дополнительные числовые поля (длительность, цена, дата вебинара, сертификат) пока не включены до проверки их смысла и leakage risk.
- Фактические метрики на реальной БД не заявляются до запуска эксперимента на разрешённой выгрузке.
- UserId и IP не используются в признаках; закрытое содержимое платных материалов не извлекается.

Это исследовательский MVP, а не production-модель.
