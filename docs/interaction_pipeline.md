# Взаимодействия и офлайн-обучение

## Источники

`recommender/data_processing/interactions.sql` приводит к общей схеме три вида записей:
- `rating`: явная оценка Lesson или Calculator;
- `course_binding`: связь пользователя с Course;
- `lesson_progress`: прохождение Lesson через CourseUserBindings.

В UserRatings сопоставление по EntityId:
- `8b440b1a-00c3-423a-9bae-3376475eb203` → Lessons;
- `7ac1c8c3-18b8-42ea-92ea-fcc10a6d496f` и `72dfaf58-4e43-4b92-a1cd-5f8b5de739b4` → Calculators.

Из 8 343 оценок только 2 325 имеют UserId: 2 308 оценок уроков и 17 оценок калькуляторов. SQL намеренно исключает оценки без UserId из персональной выгрузки. Анонимные оценки не должны превращаться в пользовательские события.

## Схема выгрузки

| Поле | Значение |
|---|---|
| user_id | внутренний идентификатор для группировки истории |
| item_id | идентификатор материала |
| item_type | course, lesson или calculator |
| event_type | rating, course_binding или lesson_progress |
| rating_value | оценка только для rating |
| is_completed | признак завершения только для progress/binding |
| event_at | дата события/состояния, если доступна |

## Правила

- Не создавать негативные примеры из отсутствия события.
- Не трактовать course_binding как просмотр курса.
- Для lesson_progress завершение определяется по timestamp `Completed IS NOT NULL`.
- Явную оценку сохранять отдельно от прогресса, не сводить сигналы в произвольный вес до эксперимента.
- Для temporal split использовать event_at.
- user_id нужен только внутри изолированного пайплайна. Не печатать и не сохранять сырые ID в Git, отчётах или логах.
