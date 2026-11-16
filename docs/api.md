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
- `limit` — необязательный, `1..20`; если не задан, берётся `RECO_DEFAULT_LIMIT`
  (по умолчанию 5). Верхняя граница совпадает с `RECO_MAX_LIMIT` (по умолчанию 20).

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
      "description": null,
      "url": null,
      "score": 0.42,
      "reasons": ["совпадают выбранные темы", "материал связан с вашей отраслью"],
      "next_step": "Посмотреть программу курса и оценить требуемое время на обучение."
    }
  ],
  "metadata": {
    "cold_start": false,
    "strategy": "baseline",
    "limit": 5,
    "returned": 1,
    "catalog_source": "sample"
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
overlap-скорер с тем же форматом ответа — API продолжает работать.

Стратегия ранжирования задаётся переменной `RECO_STRATEGY` (`baseline` | `hybrid`).

## Прочее

- `GET /health` → `{"status": "ok"}`
- Swagger UI: `/docs`, OpenAPI JSON: `/openapi.json`

> Фактические значения `business_stage`, `experience_level`, `industry`,
> `preferred_formats`, `event_type` и типы материалов сверяются с реальной
> выгрузкой и при расхождении обновляются согласованно всей командой.


## Поля для React

- description: строка из открытого описания каталога или null. Для платных материалов возвращается null.
- url: необязательная строка/null. Передаются только абсолютные http/https без логина/пароля из database-каталога. Относительные URL без подтверждённого origin не достраиваются. В sample ссылки /materials/... фиктивны и не выдаются.
- is_paid: boolean | null. PostgreSQL предоставляет стоимость курсов и подкастов, тип курса учитывает подписку. При отсутствии данных возвращается null.
- metadata.catalog_source: sample | database (в frontend mock — frontend_mock). Позволяет отличить sample от предоставленного каталога. Источник меняется только после успешной загрузки непустого каталога из БД.

Профиль принимает необязательные строки, закрытых enum схема не задаёт. UI использует marketing/finance/team; ранжирующий адаптер нормализует темы с помощью analytics.config.THEME_MAP, включая «Маркетинг», «Финансы и учет», «Управление командой». Коды отрасли/стадии/опыта приводятся к нижнему регистру и известным эквивалентам в backend/app/services/normalization.py. Неизвестные значения сохраняются, признаки не придумываются.
Форматы: course, article, document, webinar, podcast; каталог также может содержать lesson, calculator, template, checklist. Предпочтительный формат — сигнал ранжирования, а не жёсткий фильтр.

В stdout backend пишется ranking path=engine либо path=builtin, стратегия и число материалов; тексты профиля и секреты не логируются. Fallback сохраняется при ошибке импорта/исполнения либо RECO_FORCE_BUILTIN=true. metadata.strategy — настроенная стратегия, фактический путь подтверждается логом. API подключает baseline или hybrid (TF-IDF + content); collaborative index здесь не строится.

Переходы: sample_catalog содержит синтетические записи и фиктивные /materials/...; они намеренно не публикуются как URL. Страницы обучения для них не существуют. При отсутствии URL UI показывает недоступность и не предлагает открыть материал. Источник реальных адресов — Url в таблицах Articles/Courses/Documents/Webinars/Podcasts/Calculators предоставленной БД. Предпочтительные форматы — мягкий сигнал, дополнительные материалы могут иметь другую тему и формат.
