import type { RecommendationRequest } from "../types/recommendation";
// API accepts optional strings. Codes align with sample catalog and backend normalization.
export const fields = [
  {
    key: "business_stage",
    label: "На каком этапе ваш бизнес?",
    options: [
      ["early", "Начинаю бизнес"],
      ["growth", "Развиваю бизнес"],
    ],
  },
  {
    key: "industry",
    label: "В какой сфере работаете?",
    options: [
      ["retail", "Розничная торговля"],
      ["services", "Услуги"],
      ["production", "Производство"],
    ],
  },
  {
    key: "current_goal",
    label: "Что сейчас важно для бизнеса?",
    options: [
      ["marketing", "Привлечь клиентов"],
      ["finance", "Разобраться с финансами"],
      ["team", "Наладить работу команды"],
    ],
  },
  {
    key: "experience_level",
    label: "Какой у вас опыт?",
    options: [
      ["beginner", "Начинающий предприниматель"],
      ["intermediate", "Есть опыт ведения бизнеса"],
      ["advanced", "Большой опыт"],
    ],
  },
] as const;
export type Profile = Record<(typeof fields)[number]["key"], string> & {
  preferred_formats: string[];
};
export const emptyProfile: Profile = {
  business_stage: "",
  industry: "",
  current_goal: "",
  experience_level: "",
  preferred_formats: [],
};
export function toRequest(profile: Profile): RecommendationRequest {
  const user: RecommendationRequest["user_profile"] = {};
  for (const { key } of fields) if (profile[key]) user[key] = profile[key];
  if (profile.preferred_formats.length)
    user.preferred_formats = [...profile.preferred_formats];
  return { user_profile: user, history: [], limit: 5 };
}
export function profileErrors(profile: Profile) {
  return fields
    .filter(
      (field) =>
        profile[field.key] &&
        !field.options.some(([value]) => value === profile[field.key]),
    )
    .map((field) => field.key);
}

export const exampleProfile: Profile = {
  business_stage: "early",
  industry: "retail",
  current_goal: "marketing",
  experience_level: "beginner",
  preferred_formats: [],
};

export const goalField = fields.find((field) => field.key === "current_goal")!;
export const goalTitles: Record<string, string> = {
  marketing: "Материалы о привлечении клиентов",
  finance: "Материалы о финансах бизнеса",
  team: "Материалы об управлении командой",
};
export function profileSummary(profile: Profile) {
  return fields
    .filter((field) => field.key !== "current_goal")
    .map(
      (field) =>
        field.options.find(([value]) => value === profile[field.key])?.[1],
    )
    .filter(Boolean)
    .join(" · ");
}
