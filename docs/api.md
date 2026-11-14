# API-контракт

Зафиксированная базовая версия контракта (по Issue #1). Backend реализует её
как есть; Frontend и ML ориентируются на эти поля. При изменениях — синхронно
обновлять `docs/api.md`, Pydantic-схемы (`backend/app/schemas`), ML-адаптер и
TypeScript-типы.

## Endpoint

`POST /api/v1/recommendations`

### Запрос

```json
{
  "user_profile": {
    "business_stage": "early",
    "industry": "retail",
    "current_goal": "marketing",
    "experience_level": "beginner",
    "preferred_formats": ["course", "article"]
  },
  "history": [
    { "material_id": "mat-mkt-001", "event_type": "view" }
  ],
  "limit": 5
}
```

- Все поля `user_profile` необязательные. Пустой профиль без истории — валидный
  сценарий **cold start**.
- `history[].material_id` — непустая строка; `event_type` по умолчанию `"view"`.
- `limit` — необязательный, `1..50`; если не задан, берётся `RECO_DEFAULT_LIMIT`
  (по умолчанию 5) и ограничивается `RECO_MAX_LIMIT` (по умолчанию 20).

### Ответ

```json
{
  "recommendations": [
    {
      "material_id": "mat-mkt-001",
      "title": "Маркетинг для начинающего бизнеса",
      "material_type": "course",
      "topic": "marketing",
      "is_paid": true,
      "score": 0.42,
      "reasons": ["совпадают выбранные темы", "материал связан с вашей отраслью"],
      "next_step": "Посмотреть программу курса и оценить требуемое время на обучение."
    }
  ],
  "metadata": {
    "cold_start": false,
    "strategy": "baseline",
    "limit": 5,
    "returned": 1
  }
}
```

Правила контракта:
- `score` — внутренняя нормализованная оценка ранжирования `[0, 1]`, не
  вероятность покупки.
- `recommendations` отсортирован по убыванию `score`.
- `reasons` — человекочитаемые объяснения (1–2 пункта).
- `next_step` — предлагаемое пользователю следующее действие.
- Уже просмотренные материалы (из `history`) не попадают в выдачу.

## Интеграция с ML

Backend вызывает `recommender.ranking.recommend(profile, catalog, limit, strategy)`
через `app/services/ml_adapter.py` над каталогом в памяти (БД для MVP не нужна).
Если пакет `recommender` недоступен при импорте, используется встроенный
overlap-скорер с эквивалентным поведением — API продолжает работать.

Стратегия ранжирования задаётся переменной `RECO_STRATEGY` (`baseline` | `hybrid`).

## Прочее

- `GET /health` → `{"status": "ok"}`
- Swagger UI: `/docs`, OpenAPI JSON: `/openapi.json`

> Фактические значения `business_stage`, `experience_level`, `industry`,
> `preferred_formats`, `event_type` и типы материалов сверяются с реальной
> выгрузкой и при расхождении обновляются согласованно всей командой.
