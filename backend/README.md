# Backend
Основной запуск из корня: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000.
Зависимости: python -m pip install -r backend/requirements.txt.
Тесты из корня: python -m pytest -q. Конфигурация pytest добавляет backend в pythonpath для старых импортов app.*.
HTTP-контракт: docs/api.md; полный запуск React + API + PostgreSQL: корневой README.
DATABASE_URL задаётся только backend, без него используется sample-каталог. RECO_STRATEGY=baseline|hybrid. Фактический путь виден в логах path=engine/path=builtin.
В Docker context — корень репозитория: docker build -f backend/Dockerfile .; образ включает recommender и analytics.
