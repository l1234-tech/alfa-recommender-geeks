# Alfa Recommender

Подбор образовательных материалов под задачу бизнеса. Основной интерфейс — React + TypeScript + Vite; FastAPI вызывает recommender.ranking.recommend над каталогом. Streamlit сохранён отдельно в tools/streamlit как вспомогательный инструмент.

## Основной запуск — Docker

Нужен работающий Docker Engine/Compose:

```sh
docker compose up --build
```

- React: http://localhost:8080 (nginx, production build).
- API / Swagger: http://localhost:8000/docs; health: /health.
- PostgreSQL 16: localhost:5433, база alfa_course, dev user/password alfa/alfa.
- nginx передаёт /api к backend:8000 внутри сети; браузер использует свой origin.
- Существующий volume alfa_pgdata сохраняется. Веб-интерфейс не отправляет запросы к внутреннему имени backend.

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

## Каталог и режимы

- Обычный npm run dev / compose: настоящий HTTP API и движок. Без настроенной БД или при ошибке загрузки backend использует sample из 12 материалов; UI честно помечает «Подборка по учебному каталогу».
- DATABASE_URL (только backend) подключает предоставленную PostgreSQL-базу. Загрузчик читает публичные метаданные через recommender/data_processing/catalog.sql; события и пользовательские таблицы для этого API не читаются. Каталог кэшируется, после импорта перезапустите backend.
- Для нового compose volume поместите совместимый plain SQL в data/ до первого запуска. Для custom backup используйте pg_restore соответствующей версии в отдельную базу/volume, затем настройте DATABASE_URL. Не удаляйте существующую БД и не используйте команды сброса volume. Подробности: data/README.md.
- Дамп и секреты не коммитятся. В рабочем data/ дамп не предоставлен.
- npm run dev:mock — только автономные frontend fixtures, без вызова движка; пометка «Пример подборки». Этот режим не нужен при запущенном backend.

## Проверки

```powershell
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe tools/smoke_http.py
```

smoke_http требует работающие backend:8000 и Vite:5173 (реальный режим), проверяет OpenAPI, proxy, цели, cold start, формат и исключение истории.

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

Логи backend различают path=engine и path=builtin. RECO_STRATEGY=baseline (по умолчанию) либо hybrid. Fallback сохраняется, но не считается доказательством вызова движка. Collaborative filtering API-путь сейчас не использует.

## Ограничения и материалы команды

is_paid=null при неизвестной платности. description и безопасный абсолютный url передаются только при наличии; sample не содержит работающих ссылок. Форма истории пока не собирает, API history принимает и исключает просмотренное. Все поля профиля необязательны. Настроенные форматы — предпочтение, не фильтр.
Качество на предоставленной выгрузке и открытие её URL требуют самой выгрузки; sample-прогон не доказывает качество на реальных данных.
Контракт и расширения этой ветки: docs/api.md. Архитектура: docs/architecture.md. Исследования и метрики: recommender/README.md, analytics/README.md, docs/experiments.md. Презентация: presentation/outline.md.
Аудит веток, сохранение React и проверенные ограничения: docs/react-integration.md.
