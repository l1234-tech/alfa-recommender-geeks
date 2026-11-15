# Frontend — интерфейс рекомендаций

Минимальный веб-интерфейс на **Streamlit**: форма профиля пользователя → вызов
backend API → карточки рекомендаций с объяснениями (`reasons`) и следующим шагом
(`next_step`). Поддерживает холодный старт (пустой профиль) и учёт истории.
Цель — продемонстрировать сквозной сценарий, а не повторять сайт платформы
(что явно допускается условиями кейса).

## Запуск

Вместе со всем стеком из корня репозитория:

```bash
docker compose up --build
```

- Интерфейс: http://localhost:8501
- Обращается к backend по `BACKEND_URL` (в compose — `http://backend:8000`).

Локально (нужен запущенный backend на :8000):

```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run streamlit_app.py
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Адрес backend API |

Контракт ответа — в [`../docs/api.md`](../docs/api.md).
