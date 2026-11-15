import type {
  Recommendation,
  RecommendationRequest,
  RecommendationResponse,
} from "../types/recommendation";
import { mockTransport, type Scenario } from "./mock";
export const mockEnabled =
  import.meta.env.VITE_USE_MOCK === "true" || import.meta.env.MODE === "mock";
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;
const text = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;
export function safeMaterialUrl(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) &&
      !url.username &&
      !url.password
      ? url.href
      : undefined;
  } catch {
    return undefined;
  }
}
export function validateResponse(value: unknown): RecommendationResponse {
  const invalid = () =>
    new Error("Сервер вернул ответ в неожиданном формате. Попробуйте снова.");
  if (
    !record(value) ||
    !Array.isArray(value.recommendations) ||
    !record(value.metadata)
  )
    throw invalid();
  const meta = value.metadata;
  if (
    typeof meta.cold_start !== "boolean" ||
    !text(meta.strategy) ||
    !Number.isInteger(meta.limit) ||
    typeof meta.limit !== "number" ||
    meta.limit < 1 ||
    !Number.isInteger(meta.returned) ||
    meta.returned !== value.recommendations.length ||
    value.recommendations.length > meta.limit ||
    (meta.catalog_source !== undefined &&
      typeof meta.catalog_source !== "string")
  )
    throw invalid();
  const recommendations: Recommendation[] = [];
  const ids = new Set<string>();
  for (const item of value.recommendations) {
    if (
      !record(item) ||
      !text(item.material_id) ||
      !text(item.title) ||
      !text(item.material_type) ||
      !(item.topic === null || typeof item.topic === "string") ||
      !(item.is_paid === null || typeof item.is_paid === "boolean") ||
      !Array.isArray(item.reasons) ||
      !item.reasons.every(text) ||
      !text(item.next_step) ||
      typeof item.score !== "number" ||
      !Number.isFinite(item.score) ||
      item.score < 0 ||
      item.score > 1 ||
      ids.has(item.material_id) ||
      (item.description !== undefined &&
        item.description !== null &&
        typeof item.description !== "string") ||
      (item.url !== undefined &&
        item.url !== null &&
        typeof item.url !== "string")
    )
      throw invalid();
    ids.add(item.material_id);
    recommendations.push({
      material_id: item.material_id,
      title: item.title,
      material_type: item.material_type,
      topic: item.topic,
      is_paid: item.is_paid,
      score: item.score,
      reasons: item.reasons,
      next_step: item.next_step,
      description: item.description,
      url: safeMaterialUrl(item.url),
    });
  }
  return {
    recommendations,
    metadata: {
      cold_start: meta.cold_start,
      strategy: meta.strategy,
      limit: meta.limit,
      returned: meta.returned,
      catalog_source: meta.catalog_source,
    },
  };
}
export async function getRecommendations(
  request: RecommendationRequest,
  signal: AbortSignal,
  scenario: Scenario = "success",
  timeout = 12000,
): Promise<RecommendationResponse> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener("abort", abort, { once: true });
  if (signal.aborted) controller.abort();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  try {
    const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
    const response = mockEnabled
      ? await mockTransport(request, controller.signal, scenario)
      : await fetch(base + "/api/v1/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
          signal: controller.signal,
        });
    if (!response.ok)
      throw new Error(
        "Не удалось получить подборку. Попробуйте снова чуть позже.",
      );
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      throw new Error("Не удалось прочитать ответ сервера. Попробуйте снова.");
    }
    return validateResponse(data);
  } catch (error) {
    if (signal.aborted) throw new DOMException("Aborted", "AbortError");
    if (timedOut)
      throw new Error("Сервер отвечает слишком долго. Попробуйте снова.");
    if (error instanceof TypeError)
      throw new Error(
        "Нет соединения с сервером. Проверьте подключение и попробуйте снова.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", abort);
  }
}
