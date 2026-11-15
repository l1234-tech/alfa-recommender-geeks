-- Normalized interaction export for offline experiments.
-- UserId is required for per-user grouping but must never be logged or exported
-- into public reports. No absence-of-event negative samples are generated.

SELECT
    ur."UserId"::text AS user_id,
    ur."EntityId"::text AS item_id,
    CASE
        WHEN ur."EntityTypeId" = '8b440b1a-00c3-423a-9bae-3376475eb203'::uuid THEN 'lesson'
        WHEN ur."EntityTypeId" IN (
            '7ac1c8c3-18b8-42ea-92ea-fcc10a6d496f'::uuid,
            '72dfaf58-4e43-4b92-a1cd-5f8b5de739b4'::uuid
        ) THEN 'calculator'
    END AS item_type,
    'rating'::text AS event_type,
    ur."Value"::integer AS rating_value,
    NULL::boolean AS is_completed,
    ur."Created" AS event_at
FROM public."UserRatings" ur
WHERE ur."UserId" IS NOT NULL
  AND NOT COALESCE(ur."IsDeleted", false)
  AND (
      (ur."EntityTypeId" = '8b440b1a-00c3-423a-9bae-3376475eb203'::uuid
       AND EXISTS (SELECT 1 FROM public."Lessons" l WHERE l."Id" = ur."EntityId"))
      OR
      (ur."EntityTypeId" IN (
          '7ac1c8c3-18b8-42ea-92ea-fcc10a6d496f'::uuid,
          '72dfaf58-4e43-4b92-a1cd-5f8b5de739b4'::uuid
      ) AND EXISTS (SELECT 1 FROM public."Calculators" c WHERE c."Id" = ur."EntityId"))
  )

UNION ALL

SELECT
    cub."UserId"::text,
    cub."CourseId"::text,
    'course'::text,
    'course_binding'::text,
    NULL::integer,
    cub."IsCompleted"::boolean,
    COALESCE(cub."StudyingStartDate", cub."BuyingDate", cub."Created")
FROM public."CourseUserBindings" cub
JOIN public."Courses" c ON c."Id" = cub."CourseId"
WHERE NOT COALESCE(cub."IsDeleted", false)
  AND NOT COALESCE(c."IsDeleted", false)

UNION ALL

SELECT
    cub."UserId"::text,
    culb."LessonId"::text,
    'lesson'::text,
    'lesson_progress'::text,
    NULL::integer,
    (culb."Completed" IS NOT NULL),
    COALESCE(culb."StudyingStartDate", culb."Created")
FROM public."CourseUserLessonBindings" culb
JOIN public."CourseUserBindings" cub ON cub."Id" = culb."CourseUserId"
JOIN public."Lessons" l ON l."Id" = culb."LessonId"
WHERE NOT COALESCE(cub."IsDeleted", false)

ORDER BY event_at NULLS LAST;
