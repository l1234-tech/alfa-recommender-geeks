# Backend / API — Alfa Course Recommender

HTTP-API персональных рекомендаций: принимает профиль и историю пользователя,
вызывает рекомендательный движок и возвращает ранжированный список материалов
с объяснениями. Реализует зафиксированный контракт из [`../docs/api.md`](../docs/api.md).

## Стек

FastAPI + Pydantic. Движок ранжирования — пакет `recommender` (ML-команда),
вызывается через `app/services/ml_adapter.py`. Каталог материалов берётся из
предоставленного PostgreSQL-дампа Альфа-Курса; без БД сервис работает на
встроенном демо-каталоге.

## Запуск

### Локально

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Docker

```bash
docker build -t alfa-backend ./backend
docker run --rm -p 8000:8000 --env-file .env alfa-backend
```

Из корня репозитория сервис поднимается через общий `compose.yaml`
(`docker compose up`), который монтирует пакет `recommender`.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | — | `postgresql://user:pass@host:5432/db` к восстановленному дампу Альфа-Курса. Если не задана — используется демо-каталог. |
| `RECO_STRATEGY` | `baseline` | Стратегия ранжирования движка: `baseline` или `hybrid`. |
| `RECO_DEFAULT_LIMIT` | `5` | Число рекомендаций по умолчанию, если `limit` не передан. |
| `RECO_MAX_LIMIT` | `20` | Жёсткий предел числа рекомендаций. |
| `RECO_FORCE_BUILTIN` | `false` | Принудительно использовать встроенный скорер вместо ML-движка. |

Секреты не коммитятся: см. [`../.env.example`](../.env.example).

## Данные

Рекомендации строятся на предоставленном датасете Альфа-Курса. Каталог
извлекается SQL-запросом ML-команды (`recommender/data_processing/catalog.sql`)
и содержит только открытые метаданные материалов (без приватного содержимого и
идентификаторов пользователей). Исходный дамп в репозиторий не коммитится.

Порядок подключения реальных данных:
1. Восстановить дамп в PostgreSQL (локально или сервисом `db` в compose).
2. Задать `DATABASE_URL`.
3. Старт сервиса — каталог загрузится из БД, иначе будет демо-каталог.

## Endpoint

`POST /api/v1/recommendations` — формат запроса и ответа в [`../docs/api.md`](../docs/api.md).

Пример:

```bash
curl -s http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"user_profile":{"business_stage":"early","industry":"retail","current_goal":"marketing","experience_level":"beginner","preferred_formats":["course","article"]},"history":[],"limit":5}'
```

## Проверка (сценарий для ревью)

```bash
cd backend && pip install -r requirements.txt
python -m pytest -q          # 1) все тесты зелёные
uvicorn app.main:app --reload
# 2) открыть /docs и выполнить POST /api/v1/recommendations
# 3) профиль "marketing/retail" → сверху материал по маркетингу, у каждого reasons и next_step
# 4) пустой body {} → cold_start=true, непустая стартовая подборка
# 5) material_id из history не появляется в выдаче
```

## Границы и устойчивость

- Контракт API стабилен для фронтенда независимо от источника каталога.
- Если пакет `recommender` ещё не влит или движок падает в рантайме — ответ
  отдаётся встроенным overlap-скорером того же формата, API не возвращает 500.
- Открытые вопросы к команде: признак платности (`is_paid`) и основной `topic`
  в `catalog.sql` пока не выгружаются — согласовать с ML; маппинг
  `business_stage`/`experience_level` на признаки движка.
