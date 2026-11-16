# Alfa Recommender

Персональные рекомендации образовательных материалов «Альфа-Курса» под задачу предпринимателя. Основной продуктовый интерфейс — React + TypeScript + Vite; API — FastAPI; ранжирование — пакет `recommender`; каталог — PostgreSQL. Streamlit в `tools/streamlit` оставлен как вспомогательный инструмент и не участвует в основном запуске.

## Быстрый запуск (Docker)

**Требуется:** Docker Desktop / Docker Engine с Compose v2. На Windows запускайте команды из PowerShell в корне репозитория.

1. Скопируйте пример переменных окружения (необязательно, если подходят порты по умолчанию):

   ```powershell
   Copy-Item .env.example .env
   ```

2. Соберите и запустите стек:

   ```powershell
   docker compose up -d --build --wait
   ```

3. Откройте:

   - React: [http://localhost:8080](http://localhost:8080)
   - Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health: [http://localhost:8000/health](http://localhost:8000/health)
   - PostgreSQL: `localhost:5433`, база `alfa_course`, пользователь/пароль для локальной разработки `alfa/alfa`.

Nginx обслуживает React и проксирует `/api` к FastAPI внутри Compose-сети. Браузеру не требуется отдельный адрес backend.

**Важно:** без восстановленной выгрузки приложение всё равно запускается, но использует небольшой синтетический demo-каталог. Для проверки настоящих материалов Альфа-Курса выполните следующий раздел. В Swagger проверьте `metadata.catalog_source`: `sample` означает demo-каталог, `database` — загруженную БД.

Остановка без удаления данных:

```powershell
docker compose down
```

Не используйте `docker compose down -v`, если хотите сохранить локальную БД. Для просмотра состояния и логов:

```powershell
docker compose ps
docker compose logs --tail=100 backend db frontend
```

Если порты заняты, задайте в `.env` значения `ALFA_UI_PORT`, `ALFA_API_PORT`, `ALFA_DB_PORT` (по умолчанию 8080, 8000, 5433).

## Загрузка предоставленного каталога

SQL-выгрузка не хранится в Git: по условиям кейса исходные данные нельзя публиковать. Получите файл у организаторов, распакуйте его и положите **`alfa_course_hackathon.sql`** в локальную папку `data/`.

Из корня репозитория выполните:

```powershell
docker compose up -d --wait db
python tools/restore_catalog.py
docker compose up -d --build --wait
```

Скрипт перед импортом проверяет, что схема public пуста, и отказывается перезаписывать непустую БД. Он потоково передаёт plain SQL в контейнер и удаляет несовместимые с PostgreSQL 16 служебные строки из дампа pg_dump 17. Если импорт остановился из-за непустой БД, **не удаляйте volume автоматически**: сначала проверьте, нужна ли сохранённая база. Полный разбор и восстановление — [data/README.md](data/README.md).

После успешного импорта перезапустите backend (команда запуска всего стека выше это делает) и убедитесь, что API возвращает `metadata.catalog_source = "database"`. Если значение `sample`, настоящая выгрузка не загружена или backend не смог подключиться к БД.

## Проверка для жюри

1. Откройте React и нажмите **«Подобрать без уточнений»** — проверьте причины и следующие шаги в карточках.
2. Выберите **«Привлечь клиентов»**, при желании задайте сферу/опыт и нажмите **«Подобрать материалы»**.
3. В Swagger вызовите `POST /api/v1/recommendations` с пустым профилем. Скопируйте `material_id` одной рекомендации и повторите запрос, передав этот ID в `history`. Просмотренный материал должен исчезнуть из следующей выдачи.
4. В ответе проверьте `metadata.catalog_source = "database"` (если восстановили SQL) и в логах backend — `ranking path=engine`.
5. Подробная последовательность показа и готовые запросы — [сценарий защиты](presentation/defense.md).

[Презентация в PDF](presentation/alfa-course.pdf).

## Локальный запуск без Docker

**Требуется:** Python 3.11–3.13, Node.js 22.12+ или Node.js 24 LTS, npm и (для настоящего каталога) доступная PostgreSQL.

В первом терминале из корня:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Во втором терминале:

```powershell
cd frontend
npm ci
npm run dev
```

React: [http://localhost:5173](http://localhost:5173). Vite проксирует `/api` на `localhost:8000`. Без `DATABASE_URL` backend использует demo-каталог. Для подключения БД задайте `DATABASE_URL` в окружении backend (например, `postgresql://alfa:alfa@127.0.0.1:5433/alfa_course`) до запуска uvicorn. В Linux/macOS используйте `.venv/bin/python` вместо Windows-пути.

## Режимы и конфигурация

- Обычный запуск React + API — настоящий HTTP-запрос к FastAPI и ML-движку.
- Без настроенной БД или при ошибке загрузки backend использует demo-каталог из 12 материалов; ответ сообщает `catalog_source=sample`.
- `DATABASE_URL` задаётся только backend. Каталог загружается из PostgreSQL и кэшируется в памяти; после импорта/изменения БД перезапустите backend.
- `npm run dev:mock` в `frontend/` включает автономные frontend fixtures без вызова backend. Это режим для разработки интерфейса, не основной режим демонстрации.
- В Docker по умолчанию `RECO_STRATEGY=hybrid`. Для сравнения можно задать `RECO_STRATEGY=baseline`. `RECO_FORCE_BUILTIN=1` принудительно включает резервный скорер.
- Пример конфигурации — [.env.example](.env.example). Реальные секреты и дамп не коммитить.

## Проверки

Backend (из корня; сначала установите зависимости):

```powershell
./.venv/Scripts/python.exe -m pytest -q
```

Smoke-проверка работающего API:

```powershell
./.venv/Scripts/python.exe tools/smoke_http.py
```

Для проверки через Docker/Nginx задайте перед запуском:

```powershell
$env:SMOKE_FRONTEND_URL = "http://127.0.0.1:8080"
./.venv/Scripts/python.exe tools/smoke_http.py
```

Frontend (из каталога `frontend/`):

```powershell
npm ci
npm run build
npm run typecheck
npm run lint
npm test
```

Для тестов React с настоящим HTTP запустите backend и Vite, затем задайте `VITE_LIVE_API_URL`:

```powershell
$env:VITE_LIVE_API_URL = "http://127.0.0.1:5173"
npm test -- src/live.test.tsx
```

## Архитектура, API и ограничения

- [Контракт API](docs/api.md): `POST /api/v1/recommendations`, `GET /health), схемы запросов/ответов и метаданные.
- [Архитектура](docs/architecture.md): frontend, nginx, FastAPI, ML-движок и PostgreSQL.
- [Оценка качества](docs/experiments.md): тестовые профили, офлайн-метрики и ограничения методики.
- [План A/B-теста](docs/ab_test_plan.md): гипотеза, метрики, дизайн и логирование.
- [Заметки по данным](docs/data_notes.md): структура исходной выгрузки и особенности полей.

История передаётся через API. На текущем этапе она исключает уже просмотренные материалы из выдачи; модель пока не обучается на истории как на положительном сигнале предпочтений. Каждая рекомендация API содержит объяснение и следующий шаг. Для известных типов материалов backend преобразует корректный slug в публичный HTTPS-маршрут Альфа-Курса; неизвестные типы и некорректные slug остаются без ссылки. Закрытое содержание платных материалов не раскрывается; страница может требовать авторизацию или оплату.
