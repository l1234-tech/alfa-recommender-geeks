// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { HomePage } from "./pages/HomePage";
import { getRecommendations, mockEnabled } from "./api/recommendations";
import { emptyProfile, toRequest } from "./config/profile";
const live = import.meta.env.VITE_LIVE_API_URL;
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});
it.runIf(Boolean(live))(
  "renders actual HTTP results and retries after unavailable server",
  async () => {
    expect(mockEnabled).toBe(false);
    vi.stubEnv("VITE_API_BASE_URL", live);
    render(<HomePage />);
    fireEvent.click(
      screen.getByRole("radio", { name: "Разобраться с финансами" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Подобрать материалы" }),
    );
    await screen.findByText(
      "Подборка по учебному каталогу",
      {},
      { timeout: 10000 },
    );
    expect(screen.getAllByText("Почему подходит").length).toBeGreaterThan(0);
    expect(screen.queryByText("Пример подборки")).toBeNull();
    fireEvent.click(
      screen.getByRole("radio", { name: "Наладить работу команды" }),
    );
    vi.stubEnv("VITE_API_BASE_URL", "http://127.0.0.1:1");
    fireEvent.click(
      screen.getByRole("button", { name: "Подобрать материалы" }),
    );
    await screen.findByRole("alert");
    expect(
      (
        screen.getByRole("radio", {
          name: "Наладить работу команды",
        }) as HTMLInputElement
      ).checked,
    ).toBe(true);
    vi.stubEnv("VITE_API_BASE_URL", live);
    fireEvent.click(screen.getByText("Попробовать снова"));
    await screen.findByText("Материалы об управлении командой");
    expect(
      screen.getByText("Организация ежедневной работы соло-фаундера"),
    ).toBeTruthy();
  },
);
it.runIf(Boolean(live))(
  "validates actual cold start, format preference, history and empty response",
  async () => {
    vi.stubEnv("VITE_API_BASE_URL", live);
    const request = toRequest(emptyProfile);
    const first = await getRecommendations(
      request,
      new AbortController().signal,
    );
    expect(first.metadata.cold_start).toBe(true);
    const all = await getRecommendations(
      { ...request, limit: 50 },
      new AbortController().signal,
    );
    const empty = await getRecommendations(
      {
        ...request,
        history: all.recommendations.map((item) => ({
          material_id: item.material_id,
          event_type: "view",
        })),
      },
      new AbortController().signal,
    );
    expect(empty.recommendations).toEqual([]);
    const formats = await getRecommendations(
      { user_profile: { preferred_formats: ["course"] }, history: [] },
      new AbortController().signal,
    );
    expect(formats.recommendations[0].material_type).toBe("course");
    const abort = new AbortController();
    abort.abort();
    await expect(
      getRecommendations(request, abort.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
  },
);
