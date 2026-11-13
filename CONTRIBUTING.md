# Правила совместной разработки

1. Не коммитить напрямую в `main`.
2. Для каждой задачи создавать ветку: `feature/<name>`, `fix/<name>` или `docs/<name>`.
3. Делать небольшие осмысленные коммиты.
4. Открывать Pull Request в `main`.
5. Перед merge проверять код и запускать тесты.
6. Не добавлять `.env`, ключи, исходные выгрузки и пользовательские данные.
7. Согласовывать изменения API и схем данных в команде до реализации.

## Имена веток
- `feature/recommender-ranking`
- `feature/backend-api`
- `feature/frontend-onboarding`
- `feature/analytics-tests`
- `docs/readme`

## Коммиты
Рекомендуемый формат: `feat: add baseline ranking`, `fix: handle empty history`, `docs: describe API`.
