# Карта сущностей каталога и взаимодействий

## Каталог: подтверждённое сопоставление ContentSettings

Сопоставление проверено точным пересечением `ContentSettings.EntityId` с первичными ключами таблиц.

| EntityTypeId | Таблица | Совпавших EntityId | Строк ContentSettings |
|---|---|---:|---:|
| `8b440b1a-00c3-423a-9bae-3376475eb203` | Courses | 37 | 37 |
| `142c23e2-bf71-4a73-b12e-6b1b5e4d47cc` | Podcasts | 8 | 8 |
| `8ede4179-0faf-407d-a4fc-1d94f9a63089` | Articles | 855 | 855 |
| `da1ad865-8605-4ab1-9f6c-4489a26fbc35` | Documents | 247 | 247 |
| `ece4acf3-5dd3-47b9-9f08-99c0d6203cc7` | Webinars | 19 | 19 |

## Дополнительные сущности

Lessons и Calculators не входят в подтверждённые пять типов ContentSettings, но нужны для связывания с пользовательскими оценками.

- Lessons включаются в общий каталог только если они не удалены, не являются группами и доступны через опубликованный/не закрытый курс как trial-урок либо урок бесплатного курса (`Courses.Cost IS NULL`). Текст `Lessons.Content` не выгружается.
- Calculators включаются напрямую, если не удалены; используются только Title, Description и Url.

Эти правила консервативны и должны быть проверены владельцем данных перед production-использованием.

## UserRatings: отдельное сопоставление EntityTypeId

`UserRatings.EntityTypeId` нельзя трактовать как идентификатор типа из ContentSettings. Проверка EntityId показала:

| UserRatings.EntityTypeId | Фактическая таблица | Оценок |
|---|---|---:|
| `8b440b1a-00c3-423a-9bae-3376475eb203` | Lessons | 4 531 |
| `7ac1c8c3-18b8-42ea-92ea-fcc10a6d496f` | Calculators | 3 809 |
| `72dfaf58-4e43-4b92-a1cd-5f8b5de739b4` | Calculators | 3 |

Из 8 343 оценок только 2 325 имеют UserId: 2 308 для Lessons и 17 для Calculators. Остальные 6 018 анонимны и не включаются в персональную историю.

## Поля каталога

| Тип | Таблица | Поля |
|---|---|---|
| Статья | Articles | Id, Title, Description, Published, IsPublic, IsClosed |
| Курс | Courses | Id, Title, Description, Duration, LessonQuantity, Cost, Published, IsClosed |
| Документ | Documents | Id, Title, Description, Url, Published |
| Вебинар | Webinars | Id, Title, Description, StartsAt, EndsAt, Published, IsClosed |
| Подкаст | Podcasts | Id, Title, Description, Duration, Published, IsClosed |
| Урок | Lessons | Id, Title, Description, IsGroup, IsDeleted |
| Калькулятор | Calculators | Id, Title, Description, Url, IsDeleted |

ContentSettings связывает первые пять типов с темами, тегами и отраслями. Для уроков и калькуляторов эти признаки в текущей выгрузке не добавляются.

## Взаимодействия

| Источник | Допустимая интерпретация |
|---|---|
| UserRatings | Явная оценка Lesson или Calculator |
| UserRatingTagsBindings | Теги/текст оценки; смысл Text проверить отдельно |
| CourseUserBindings | Связь пользователя с Course, состояние обучения/доступа |
| CourseUserLessonBindings | Состояние прохождения Lesson |
| RecommendedItems | Исторические рекомендованные сущности; не ground truth без выяснения семантики |

`UserId` и IP не являются признаками модели; не выводить их в логи и отчёты.
