// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { emptyProfile, profileErrors, toRequest } from "./config/profile";
import { fixtures } from "./api/mock";
import { validateResponse, getRecommendations } from "./api/recommendations";
import { HomePage } from "./pages/HomePage";
beforeEach(() => {
  vi.stubEnv("VITE_USE_MOCK", "false");
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});
const profile = {
  business_stage: "early",
  industry: "retail",
  current_goal: "marketing",
  experience_level: "beginner",
  preferred_formats: [],
};
it("creates exact payload, including empty history and omitted unknown fields", () => {
  expect(toRequest(profile)).toEqual({
    user_profile: {
      business_stage: "early",
      industry: "retail",
      current_goal: "marketing",
      experience_level: "beginner",
    },
    history: [],
    limit: 5,
  });
  expect(toRequest({ ...emptyProfile, current_goal: "marketing" })).toEqual({
    user_profile: { current_goal: "marketing" },
    history: [],
    limit: 5,
  });
  expect(profileErrors({ ...emptyProfile, current_goal: "marketing" })).toEqual(
    [],
  );
  expect(profileErrors(emptyProfile)).toEqual([]);
  expect(profileErrors({ ...emptyProfile, industry: "invalid" })).toEqual([
    "industry",
  ]);
});
it("rejects malformed or duplicate materials", () => {
  expect(() =>
    validateResponse({ recommendations: [{ title: 123 }] }),
  ).toThrow();
  expect(() =>
    validateResponse({
      recommendations: [
        fixtures.recommendations[0],
        fixtures.recommendations[0],
      ],
    }),
  ).toThrow();
});
function fill() {
  render(<HomePage />);
  for (const [key, value] of Object.entries(profile).filter(
    ([key]) => key !== "preferred_formats",
  ))
    if (key === "current_goal")
      fireEvent.click(
        document.querySelector(
          'input[name="current_goal"][value="' + value + '"]',
        )!,
      );
    else fireEvent.change(document.getElementById(key)!, { target: { value } });
}
function submit() {
  fireEvent.click(
    screen.getByRole("button", {
      name: /Подобрать материалы|Подобрать без уточнений/,
    }),
  );
}
it("shows server order, explanations and stale profile notice", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(JSON.stringify(fixtures))),
  );
  fill();
  submit();
  await screen.findByText(fixtures.recommendations[0].title);
  expect(vi.mocked(fetch)).toHaveBeenCalledWith(
    "/api/v1/recommendations",
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify({
        user_profile: {
          business_stage: "early",
          industry: "retail",
          current_goal: "marketing",
          experience_level: "beginner",
        },
        history: [],
        limit: 5,
      }),
    }),
  );
  expect(screen.getAllByText("Почему подходит")).toHaveLength(3);
  fireEvent.change(document.getElementById("industry")!, {
    target: { value: "services" },
  });
  expect(screen.getByText(/Параметры изменились/)).toBeTruthy();
});
it("shows empty state", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          '{"recommendations":[],"metadata":{"cold_start":false,"strategy":"baseline","limit":5,"returned":0}}',
        ),
      ),
  );
  fill();
  submit();
  await screen.findByText("Подборка не найдена");
});
it("offers a broader cold-start selection when all returned scores are zero", async () => {
  const zeroScoreResponse = {
    ...fixtures,
    recommendations: fixtures.recommendations.map((item) => ({
      ...item,
      score: 0,
    })),
  };
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(JSON.stringify(zeroScoreResponse))),
  );
  fill();
  submit();
  await screen.findByText("Точного совпадения не нашлось");
  fireEvent.click(
    screen.getByRole("button", {
      name: "Сбросить профиль для общей подборки",
    }),
  );
  expect((document.getElementById("industry") as HTMLSelectElement).value).toBe(
    "",
  );
  expect(
    screen.getByText("Параметры изменились. Обновите подборку"),
  ).toBeTruthy();
});
it("preserves profile and allows retry after server error", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(new Response("", { status: 503 }))
    .mockResolvedValueOnce(new Response(JSON.stringify(fixtures)));
  vi.stubGlobal("fetch", fetcher);
  fill();
  submit();
  await screen.findByRole("alert");
  expect((document.getElementById("industry") as HTMLSelectElement).value).toBe(
    "retail",
  );
  fireEvent.click(screen.getByText("Попробовать снова"));
  await screen.findByText(fixtures.recommendations[0].title);
});
it("handles malformed JSON and invalid response at boundary", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response("{"))
      .mockResolvedValueOnce(new Response('{"recommendations":[{}]}')),
  );
  await expect(
    getRecommendations(toRequest(profile), new AbortController().signal),
  ).rejects.toThrow(/прочитать/);
  await expect(
    getRecommendations(toRequest(profile), new AbortController().signal),
  ).rejects.toThrow(/формате/);
});
it("ignores old response even when transport ignores abort", async () => {
  let finish: (value: Response) => void = () => {};
  const pending = new Promise<Response>((resolve) => {
    finish = resolve;
  });
  const fetcher = vi
    .fn()
    .mockReturnValueOnce(pending)
    .mockResolvedValueOnce(
      new Response(
        '{"recommendations":[],"metadata":{"cold_start":false,"strategy":"baseline","limit":5,"returned":0}}',
      ),
    );
  vi.stubGlobal("fetch", fetcher);
  fill();
  submit();
  fireEvent.change(document.getElementById("industry")!, {
    target: { value: "services" },
  });
  submit();
  await screen.findByText("Подборка не найдена");
  await act(async () => {
    finish(new Response(JSON.stringify(fixtures)));
    await pending;
  });
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  expect(screen.queryByText(fixtures.recommendations[0].title)).toBeNull();
});
it("cancels transport and reports timeout separately", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (_url: unknown, options: RequestInit) =>
        new Promise((_resolve, reject) =>
          options.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    ),
  );
  await expect(
    getRecommendations(
      toRequest(profile),
      new AbortController().signal,
      "success",
      5,
    ),
  ).rejects.toThrow(/долго/);
  const controller = new AbortController();
  const request = getRecommendations(toRequest(profile), controller.signal);
  controller.abort();
  await expect(request).rejects.toMatchObject({ name: "AbortError" });
});

it("supports labelled native controls and focuses the first invalid field", async () => {
  const user = userEvent.setup();
  render(<HomePage />);
  await user.click(
    screen.getByRole("button", {
      name: /Подобрать материалы|Подобрать без уточнений/,
    }),
  );
  expect(
    screen.getByText(
      "Все поля необязательны. Можно подобрать материалы без уточнений.",
    ),
  ).toBeTruthy();
  await user.selectOptions(
    screen.getByLabelText("На каком этапе ваш бизнес?"),
    "early",
  );
  expect((document.activeElement as HTMLSelectElement).value).toBe("early");
});
