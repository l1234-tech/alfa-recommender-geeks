# Анализ признаков для персонализации

## Признаки материалов

- Текст: Title и Description из открытых метаданных.
- Темы, теги и отрасли: через ContentSettingsTopics, ContentSettingsTags, ContentSettingsIndustries для Articles, Courses, Documents, Webinars и Podcasts.
- Тип материала: article, course, document, webinar, podcast, lesson, calculator.
- Доступность: Published, IsDeleted, IsClosed и связи с доступным курсом. Для Lessons применяется консервативное правило: trial-урок или урок курса с Cost IS NULL.
- Для курсов: Duration, LessonQuantity, Cost, HasTrial, IsCertified.
- Для вебинаров: StartsAt.
- Для статей: SubjectId, Duration, IsLesson.

## Признаки взаимодействий

- Оценка: UserRatings.Value и Created. EntityId сопоставлен с Lessons (4 531 оценка) и Calculators (3 812 оценок).
- Персональные оценки: только 2 325 строк имеют UserId (2 308 Lesson, 17 Calculator). Анонимные оценки не входят в user-item события.
- Прохождение курса: IsCompleted, Completed, LessonsCompleted, StudyingStartDate.
- Прохождение урока: Completed — timestamp; завершение равно Completed IS NOT NULL.
- Теги оценки: UserRatingTagsBindings.

## Внешний профиль

В дампе нет подтверждённой таблицы с бизнес-стадией, текущей задачей и уровнем опыта предпринимателя. Эти признаки должны приходить из onboarding/API.

## Рекомендуемый MVP feature set

1. TF-IDF по Title + Description (только разрешённые открытые описания).
2. Multi-hot/взвешенные признаки Topics, Tags, Industries.
3. Тип материала как categorical feature.
4. Профиль пользователя из onboarding: темы, отрасль, текущая задача и предпочтительные типы.
5. История пользователя из явных оценок и подтверждённых событий обучения.

## Правила

- Не считать отсутствие оценки негативной меткой.
- Не трактовать CourseUserBindings как просмотр курса.
- Не смешивать рейтинги и прогресс в один сигнал без эксперимента.
- Исключать недоступные материалы.
- Для offline evaluation использовать временное разделение по event_at.
- Не использовать UserId, IP и закрытый Content как признаки.
