# Локальная интеграция React, 16.11.2026

## Восстановление и источники

Ветка integration/react-product основана на origin/integration (72021f0).
Исходный React целиком сохранён в backup/react-before-integration, коммит 4aa5293 (22 файла). Включены untracked исходники и lockfile; исключены node_modules, dist, кэш, секреты и выгрузки. Ветка feat/frontend-ui и remote-ветки не менялись.
Streamlit сохранён в tools/streamlit. Основной frontend — прежний React, адаптированный к актуальному API.

| Источник                                                                          | Решение                                                                                            |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| origin/integration 72021f0                                                        | Основа: backend, ML, аналитика, тесты, PostgreSQL                                                  |
| origin/feat/backend-api 4a47a24                                                   | Уже предок integration, повторно не переносился                                                    |
| origin/feat/ml-recommender c9ff979 + 7d2d954                                      | Основная часть уже вошла; 7d2d954 перенесён cherry-pick (f82f6db), исправляет публикацию вебинаров |
| origin/feat/ui-streamlit 2a51a50                                                  | Уже вошёл, UI сохранён отдельно                                                                    |
| origin/feature/analytics-tests f18ac5b                                            | Уже вошёл, сохранён                                                                                |
| origin/main, feat/analytics-qa, feat/product-integration, remote feat/frontend-ui | Совпадают с b75e3d4, дополнительных изменений нет                                                  |
| backup/react-before-integration 4aa5293                                           | Локальный React: форма, сценарии запросов, тесты и стили                                           |

## Разрешённые расхождения

- README Streamlit не заменяет React-инструкцию; Python/Node зависимости разделены.
- React переведён с user/stage/experience/reason на user_profile/business_stage/experience_level/reasons[] и metadata.
- Пустой профиль допустим, добавлены preferred_formats; history поддерживается транспортом, пока не собирается интерфейсом.
- Нормализация API/catalog использует темы analytics.config.THEME_MAP и фиксированные алиасы в backend, не клиентское ранжирование.
- is_paid неизвестен без Cost: null вместо ложного «бесплатно».
- description, url и metadata.catalog_source — документированные интеграционные расширения для ревью команды, не внешнее согласование.
- SQL-слой уже содержал description/url; теперь они доходят до UI. Только абсолютные безопасные ссылки. Фиктивные sample-ссылки не отдаются.
- Аналитический HTTP-адаптер и контрактные тесты мигрированы к новой схеме, внутренние профили аналитики сохранены.
- Один TF-IDF-тест использовал строковый ID после миграции ML на typed keys; переведён на CatalogItem без изменения проверки релевантности.
- Backend Docker теперь содержит движок в образе; React nginx использует same-origin /api proxy.

## Фактическая проверка

Локальный запуск: React dev (реальный режим) → Vite proxy → FastAPI → recommender.ranking.recommend → sample-каталог (12 материалов).
В логах подтверждено path=engine, strategy=baseline; fallback не использовался в HTTP smoke. Отдельные Python-тесты подтверждают engine baseline и hybrid. Collaborative filtering не подключён в API-пути.

tools/smoke_http.py проверяет health, актуальный OpenAPI, три задачи, пустой/неполный профиль, предпочтительные форматы, исключение истории и пустую выдачу по настоящему HTTP.
frontend/src/live.test.tsx использует настоящий fetch и React-компоненты: выдача, сервер недоступен, сохранение формы и повтор, cold start, форматы, history, пустой ответ и отмена. Это проверка компонентов с настоящим HTTP, не браузерная визуальная проверка.

Docker compose config валиден. Engine Docker Desktop не доступен (named pipe отсутствует), поэтому build/up контейнеров не подтверждены; существующие volumes не удалялись.
В рабочем data/ нет дампа. Подключение PostgreSQL-выгрузки и её реальные URL не проверены. 15 analytics-тестов пропускаются из-за отсутствия data/raw/catalog.csv.
По просьбе пользователя управление Chrome прекращено; визуальный сценарий desktop/360 px и браузерный Network остаются для ручной проверки. Качество модели на реальных данных этим прогоном не измеряется.

Итоговый прогон: frontend build/typecheck/lint прошли; 20 React-тестов прошли (включая 2 live HTTP с sample-каталогом). Python: 134 passed, 15 skipped (приватный CSV отсутствует). HTTP smoke через Vite proxy прошёл. Доступность backend и React подтверждена HTTP; это не заменяет ручной браузерный просмотр.
