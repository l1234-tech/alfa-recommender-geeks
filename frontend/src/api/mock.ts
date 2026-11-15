import type {
  RecommendationRequest,
  RecommendationResponse,
} from "../types/recommendation";
export type Scenario = "success" | "empty" | "error" | "slow" | "invalid";
export const fixtures: RecommendationResponse = {
  metadata: {
    cold_start: false,
    strategy: "fixture",
    limit: 5,
    returned: 3,
    catalog_source: "frontend_mock",
  },
  recommendations: [
    {
      material_id: "demo-001",
      title: "Первые клиенты: как проверить канал привлечения",
      material_type: "article",
      topic: "marketing",
      is_paid: null,
      score: 0.91,
      reasons: [
        "Для привлечения клиентов важно проверить канал на небольшом тесте. Материал разбирает подготовку предложения и первого эксперимента.",
      ],
      next_step:
        "Сформулируйте предложение для клиентов и выберите канал для проверки.",
    },
    {
      material_id: "demo-002",
      title: "Как понять, кто ваш покупатель",
      material_type: "article",
      topic: "marketing",
      is_paid: null,
      score: 0.84,
      reasons: [
        "Перед запуском рекламы стоит определить аудиторию. Материал посвящён вопросам, которые помогают узнать потребности покупателей.",
      ],
      next_step: "Запишите три вопроса потенциальному покупателю.",
    },
    {
      material_id: "demo-003",
      title: "Маркетинговый бюджет без сложных таблиц",
      material_type: "article",
      topic: "marketing",
      is_paid: null,
      score: 0.78,
      reasons: [
        "Для проверки продвижения нужен ограниченный бюджет. Материал разбирает планирование расходов на первый тест.",
      ],
      next_step: "Определите бюджет первого эксперимента.",
    },
  ],
};

const financeFixtures: RecommendationResponse = {
  metadata: {
    cold_start: false,
    strategy: "fixture",
    limit: 5,
    returned: 3,
    catalog_source: "frontend_mock",
  },
  recommendations: [
    {
      material_id: "demo-finance-001",
      title: "Денежный поток: как заранее увидеть кассовый разрыв",
      material_type: "article",
      topic: "finance",
      is_paid: null,
      score: 0.91,
      reasons: [
        "Для задачи управления финансами: материал объясняет, как сопоставить даты поступлений и обязательных платежей.",
      ],
      next_step:
        "Составьте календарь поступлений и платежей на ближайшие четыре недели.",
    },
    {
      material_id: "demo-finance-002",
      title: "Прибыль и выручка: что остаётся бизнесу",
      material_type: "article",
      topic: "finance",
      is_paid: null,
      score: 0.84,
      reasons: [
        "Помогает отделить выручку от расходов и понять, какие затраты учитывать при расчёте прибыли.",
      ],
      next_step:
        "Выпишите выручку и основные расходы за прошлый месяц, затем рассчитайте разницу.",
    },
    {
      material_id: "demo-finance-003",
      title: "Цена продукта: как учитывать все затраты",
      material_type: "article",
      topic: "finance",
      is_paid: null,
      score: 0.78,
      reasons: [
        "Разбор себестоимости помогает проверить, покрывает ли цена прямые и постоянные расходы.",
      ],
      next_step:
        "Для одного продукта перечислите затраты на продажу и долю постоянных расходов.",
    },
  ],
};
const teamFixtures: RecommendationResponse = {
  metadata: {
    cold_start: false,
    strategy: "fixture",
    limit: 5,
    returned: 3,
    catalog_source: "frontend_mock",
  },
  recommendations: [
    {
      material_id: "demo-team-001",
      title: "Делегирование: как передать задачу с понятным результатом",
      material_type: "article",
      topic: "team",
      is_paid: null,
      score: 0.91,
      reasons: [
        "Для задачи управления командой: материал помогает описать ожидаемый результат, срок и границы ответственности.",
      ],
      next_step:
        "Выберите задачу для передачи и запишите результат, срок и критерии готовности.",
    },
    {
      material_id: "demo-team-002",
      title: "Роли в небольшой команде: кто за что отвечает",
      material_type: "article",
      topic: "team",
      is_paid: null,
      score: 0.84,
      reasons: [
        "Помогает обнаружить задачи без ответственного и пересечения обязанностей в небольшой команде.",
      ],
      next_step:
        "Составьте список регулярных задач и назначьте одного ответственного за каждую.",
    },
    {
      material_id: "demo-team-003",
      title: "Обратная связь без взаимных обвинений",
      material_type: "article",
      topic: "team",
      is_paid: null,
      score: 0.78,
      reasons: [
        "Материал предлагает структуру разговора о конкретной рабочей ситуации и договорённостях на будущее.",
      ],
      next_step:
        "Подготовьте пример ситуации: наблюдаемый факт, его последствия и предложение для обсуждения.",
    },
  ],
};
// Fixed demonstration responses by goal, without client-side ranking.
const fixturesByGoal: Record<string, RecommendationResponse> = {
  marketing: fixtures,
  finance: financeFixtures,
  team: teamFixtures,
};

export function mockTransport(
  request: RecommendationRequest,
  signal: AbortSignal,
  scenario: Scenario,
): Promise<Response> {
  const selected = fixturesByGoal[
    request.user_profile.current_goal || "marketing"
  ] ?? {
    metadata: {
      cold_start: false,
      strategy: "fixture",
      limit: 5,
      returned: 3,
      catalog_source: "frontend_mock",
    },
    recommendations: [],
  };
  const limit = Math.min(request.limit ?? 5, 20);
  const seen = new Set(request.history.map((event) => event.material_id));
  const recommendations = selected.recommendations
    .filter((item) => !seen.has(item.material_id))
    .slice(0, limit);
  const metadata = {
    ...selected.metadata,
    limit,
    returned: recommendations.length,
    cold_start:
      request.history.length === 0 &&
      !Object.values(request.user_profile).some(
        (value) => value && value.length,
      ),
  };
  return new Promise((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    const timer = setTimeout(
      () => {
        signal.removeEventListener("abort", abort);
        resolve(
          new Response(
            JSON.stringify(
              scenario === "empty"
                ? {
                    recommendations: [],
                    metadata: { ...metadata, returned: 0 },
                  }
                : scenario === "invalid"
                  ? { recommendations: [{ title: 123 }] }
                  : {
                      recommendations,
                      metadata,
                    },
            ),
            { status: scenario === "error" ? 503 : 200 },
          ),
        );
      },
      scenario === "slow" ? 16000 : 700,
    );
    if (signal.aborted) abort();
    else signal.addEventListener("abort", abort, { once: true });
  });
}
