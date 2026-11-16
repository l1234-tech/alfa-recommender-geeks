# Alfa Recommender

Подбор образовательных материалов под задачу бизнеса. Основной интерфейс — React + TypeScript + Vite; FastAPI вызывает recommender.ranking.recommend над каталогом. Streamlit сохранён отдельно в tools/streamlit как вспомогательный инструмент.

## Основной запуск — Docker

Нужен работающий Docker Engine/Compose:

```sh
docker compose up --build
```

- [Интерфейс React](http://localhost:8080).
- [Swagger](http://localhost:8000/docs) и [проверка Backend](http://localhost:8000/health).
- PostgreSQL 16: localhost:5433, база alfa_course, dev user/password alfa/alfa.
- nginx передаёт /api к backend:8000 внутри сети; браузер использует свой origin.
- `docker compose down` останавливает сервисы и сохраняет базу в Docker volume.
- При занятых портах задайте `ALFA_UI_PORT`, `ALFA_API_PORT` и `ALFA_DB_PORT` в окружении или в `.env`.

### Проверка для жюри

1. В React нажмите **Подобрать без уточнений**. В карточках появятся причины и следующие шаги.
2. Выберите **Привлечь клиентов**, укажите сферу или формат по желанию и нажмите **Подобрать материалы**.
3. В Swagger отправьте запрос с ID из первой подборки в `history`. API исключит этот материал. Готовая команда и порядок показа есть в [сценарии защиты](presentation/defense.md).

[Презентация в PDF](presentation/alfa-course.pdf).

## Локальный запуск без Docker

Python 3.11–3.13, Node.js 22.12+ / 24 LTS, npm. Из корня (PowerShell):

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

В другом терминале:

```sh
cd frontend
npm ci
npm run dev
```

React: http://localhost:5173. Vite проксирует /api на localhost:8000. Пакеты recommender и analytics доступны из корня; в backend Dockerfile они включены в образ, а не требуют ручного volume.
В Linux/macOS используйте .venv/bin/python вместо Windows-пути.

## Подключение исходного каталога Альфа-Курса

Чтобы рекомендации вели на реальные материалы, восстановите предоставленную SQL-выгрузку. Без неё приложение запускается с синтетическим демо-каталогом, в котором нет настоящих страниц материалов.

1. Распакуйте архив и положите `alfa_course_hackathon.sql` в `data/`.
2. Запустите PostgreSQL: `docker compose up -d --wait db`.
3. Выполните импорт: `python tools/restore_catalog.py`.
4. Запустите весь стек: `docker compose up -d --build --wait`.

Подробности и совместимость PostgreSQL 16/pg_dump 17 — в [инструкции по восстановлению каталога](data/README.md). Дамп остаётся локальным и не коммитится. Скрипт отказывается импортировать поверх непустой базы.

После импорта backend должен вернуть `metadata.catalog_source = "database"`. Если указано `sample`, настоящие ссылки не появятся.

## Каталог и режимы

- Обычный npm run dev / compose: настоящий HTTP API и движок. Без настроенной БД или при ошибке загрузки backend использует sample из 12 материалов; UI честно помечает «Подборка по учебному каталогу».
- DATABASE_URL (только backend) подключает предоставленную PostgreSQL-базу. Загрузчик читает публичные метаданные через recommender/data_processing/catalog.sql; события и пользовательские таблицы для этого API не читаются. Каталог кэшируется, после импорта перезапустите backend.
- Для предоставленной plain SQL-выгрузки используйте [инструкцию восстановления](data/README.md).
- Дамп и секреты не коммитятся. В рабочем data/ дамп не предоставлен.
- npm run dev:mock — только автономные frontend fixtures, без вызова движка; пометка «Пример подборки». Этот режим не нужен при запущенном backend.

## Проверки

```powershell
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe tools/smoke_http.py
```

`tools/smoke_http.py` проверяет OpenAPI, проксирование, подборку и исключение истории. Для Docker задайте `SMOKE_FRONTEND_URL=http://127.0.0.1:8080`. Сценарий поддерживает демо-каталог и PostgreSQL.

```sh
cd frontend
npm run build
npm run typecheck
npm run lint
npm test
```

Для React-тестов с настоящим HTTP (PowerShell, backend и Vite запущены):

```powershell
$env:VITE_LIVE_API_URL="http://127.0.0.1:5173"
npm test -- src/live.test.tsx
```

В Docker по умолчанию используется `RECO_STRATEGY=hybrid`. Для сравнения
установите `RECO_STRATEGY=baseline`. Логи Backend показывают `path=engine`
при вызове движка и `path=builtin` для резервного ранжирования.

## Ограничения и материалы команды

React собирает профиль. История передаётся в API, её удобно проверить в Swagger.
В предоставленной выгрузке поле `Url` содержит slug, а не полный адрес. Backend формирует HTTPS-ссылку по типу материала для известных публичных маршрутов; неизвестные типы и некорректные slug остаются без ссылки. Платные страницы могут требовать авторизацию или оплату.

[Контракт API](docs/api.md), [архитектура](docs/architecture.md), [оценка качества](docs/experiments.md), [план A/B-теста](docs/ab_test_plan.md).
