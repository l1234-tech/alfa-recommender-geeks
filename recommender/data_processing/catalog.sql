-- Public metadata catalog for the MVP recommender.
-- ContentSettings EntityTypeId values are confirmed against entity primary keys.
-- Deliberately excludes private Content fields and user identifiers.

WITH catalog_entities AS (
    SELECT
        cs."Id" AS content_settings_id,
        cs."EntityId" AS item_id,
        'article'::text AS item_type,
        a."Title" AS title,
        a."Description" AS description,
        a."Url" AS url,
        (NOT COALESCE(a."IsDeleted", false)
         AND NOT COALESCE(cs."IsDeleted", false)
         AND a."Published" IS NOT NULL
         AND COALESCE(a."IsPublic", false)
         AND cs."Published" IS NOT NULL
         AND NOT COALESCE(a."IsClosed", false)) AS is_available
    FROM public."ContentSettings" cs
    JOIN public."Articles" a ON a."Id" = cs."EntityId"
    WHERE cs."EntityTypeId" = '8ede4179-0faf-407d-a4fc-1d94f9a63089'::uuid

    UNION ALL

    SELECT cs."Id", cs."EntityId", 'course', c."Title", c."Description", c."Url",
        (NOT COALESCE(c."IsDeleted", false)
         AND NOT COALESCE(cs."IsDeleted", false)
         AND c."Published" IS NOT NULL
         AND cs."Published" IS NOT NULL
         AND NOT COALESCE(c."IsClosed", false))
    FROM public."ContentSettings" cs
    JOIN public."Courses" c ON c."Id" = cs."EntityId"
    WHERE cs."EntityTypeId" = '8b440b1a-00c3-423a-9bae-3376475eb203'::uuid

    UNION ALL

    SELECT cs."Id", cs."EntityId", 'document', d."Title", d."Description", d."Url",
        (NOT COALESCE(d."IsDeleted", false)
         AND NOT COALESCE(cs."IsDeleted", false)
         AND d."Published" IS NOT NULL
         AND cs."Published" IS NOT NULL)
    FROM public."ContentSettings" cs
    JOIN public."Documents" d ON d."Id" = cs."EntityId"
    WHERE cs."EntityTypeId" = 'da1ad865-8605-4ab1-9f6c-4489a26fbc35'::uuid

    UNION ALL

    SELECT cs."Id", cs."EntityId", 'webinar', w."Title", w."Description", w."Url",
        (NOT COALESCE(w."IsDeleted", false)
         AND NOT COALESCE(cs."IsDeleted", false)
         AND w."Published" IS NOT NULL
         AND cs."Published" IS NOT NULL
         AND NOT COALESCE(w."IsClosed", false))
    FROM public."ContentSettings" cs
    JOIN public."Webinars" w ON w."Id" = cs."EntityId"
    WHERE cs."EntityTypeId" = 'ece4acf3-5dd3-47b9-9f08-99c0d6203cc7'::uuid

    UNION ALL

    SELECT cs."Id", cs."EntityId", 'podcast', p."Title", p."Description", p."Url",
        (NOT COALESCE(p."IsDeleted", false)
         AND NOT COALESCE(cs."IsDeleted", false)
         AND p."Published" IS NOT NULL
         AND cs."Published" IS NOT NULL
         AND NOT COALESCE(p."IsClosed", false))
    FROM public."ContentSettings" cs
    JOIN public."Podcasts" p ON p."Id" = cs."EntityId"
    WHERE cs."EntityTypeId" = '142c23e2-bf71-4a73-b12e-6b1b5e4d47cc'::uuid

    UNION ALL

    -- Lessons are included only when an available course exposes them as trial
    -- content or the course is free (Cost IS NULL in this source schema).
    SELECT
        NULL::uuid,
        l."Id",
        'lesson'::text,
        l."Title",
        l."Description",
        NULL::public.citext,
        (
            NOT COALESCE(l."IsDeleted", false)
            AND NOT COALESCE(l."IsGroup", false)
            AND EXISTS (
                SELECT 1
                FROM public."CourseLessonBindings" clb
                JOIN public."Courses" c ON c."Id" = clb."CourseId"
                WHERE clb."LessonId" = l."Id"
                  AND NOT COALESCE(clb."IsDeleted", false)
                  AND NOT COALESCE(clb."IsClosed", false)
                  AND (COALESCE(clb."IsTrial", false) OR c."Cost" IS NULL)
                  AND NOT COALESCE(c."IsDeleted", false)
                  AND c."Published" IS NOT NULL
                  AND NOT COALESCE(c."IsClosed", false)
            )
        )
    FROM public."Lessons" l

    UNION ALL

    SELECT
        NULL::uuid,
        calc."Id",
        'calculator'::text,
        calc."Title",
        calc."Description",
        calc."Url",
        NOT COALESCE(calc."IsDeleted", false)
    FROM public."Calculators" calc
)
SELECT
    ce.item_id::text AS item_id,
    ce.item_type,
    COALESCE(ce.title, '') AS title,
    COALESCE(ce.description, '') AS description,
    ce.url,
    ce.is_available,
    COALESCE(array_agg(DISTINCT t."Title") FILTER (WHERE t."Title" IS NOT NULL), ARRAY[]::text[]) AS tags,
    COALESCE(array_agg(DISTINCT tp."Title") FILTER (WHERE tp."Title" IS NOT NULL), ARRAY[]::text[]) AS topics,
    COALESCE(array_agg(DISTINCT i."Title") FILTER (WHERE i."Title" IS NOT NULL), ARRAY[]::text[]) AS industries
FROM catalog_entities ce
LEFT JOIN public."ContentSettingsTags" cst ON cst."ContentSettingsId" = ce.content_settings_id
LEFT JOIN public."Tags" t ON t."Id" = cst."TagId" AND NOT COALESCE(t."IsDeleted", false)
LEFT JOIN public."ContentSettingsTopics" cstop ON cstop."ContentSettingsId" = ce.content_settings_id
LEFT JOIN public."Topics" tp ON tp."Id" = cstop."TopicId" AND NOT COALESCE(tp."IsDeleted", false)
LEFT JOIN public."ContentSettingsIndustries" csi ON csi."ContentSettingsId" = ce.content_settings_id
LEFT JOIN public."Industries" i ON i."Id" = csi."IndustryId" AND NOT COALESCE(i."IsDeleted", false)
GROUP BY ce.content_settings_id, ce.item_id, ce.item_type, ce.title, ce.description, ce.url, ce.is_available
ORDER BY ce.item_type, ce.title;
