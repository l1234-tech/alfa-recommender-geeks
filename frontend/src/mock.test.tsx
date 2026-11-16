// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { HomePage } from "./pages/HomePage";
import { mockTransport } from "./api/mock";
import { validateResponse } from "./api/recommendations";
vi.hoisted(() => {
  vi.stubEnv("VITE_USE_MOCK", "true");
});
beforeEach(() => {
  vi.useFakeTimers();
  vi.stubEnv("VITE_USE_MOCK", "true");
  vi.stubEnv("VITE_ENABLE_DIAGNOSTICS", "true");
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
function send() {
  fireEvent.click(
    screen.getByRole("button", {
      name: /Подобрать материалы|Подобрать без уточнений/,
    }),
  );
}
async function tick(ms = 750) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}
function scenario(value: string) {
  fireEvent.change(screen.getByLabelText("Сценарий"), { target: { value } });
}
it("returns distinct finance and team responses instead of marketing", async () => {
  const results = [];
  for (const goal of ["marketing", "finance", "team"]) {
    const response = mockTransport(
      { user_profile: { current_goal: goal }, history: [] },
      new AbortController().signal,
      "success",
    );
    await vi.advanceTimersByTimeAsync(750);
    results.push(validateResponse(await (await response).json()));
  }
  const ids = results.map((result) =>
    result.recommendations.map((item) => item.material_id),
  );
  expect(new Set(ids.flat()).size).toBe(9);
  expect(results[1].recommendations[0].title).toContain("Денежный поток");
  expect(results[2].recommendations[0].title).toContain("Делегирование");
});
it("validates empty form, fills example without sending and refreshes by goal", async () => {
  render(<HomePage />);
  expect(
    screen.getByRole("button", { name: "Подобрать без уточнений" }),
  ).toBeTruthy();
  fireEvent.click(screen.getByText("Заполнить пример"));
  expect(
    (document.getElementById("business_stage") as HTMLSelectElement).value,
  ).toBe("early");
  expect(screen.queryByText(/Подбираем материалы/)).toBeNull();
  send();
  await tick();
  expect(
    screen.getByText("Первые клиенты: как проверить канал привлечения"),
  ).toBeTruthy();
  fireEvent.click(
    document.querySelector('input[name="current_goal"][value="finance"]')!,
  );
  expect(screen.getByText(/Параметры изменились/)).toBeTruthy();
  send();
  await tick();
  expect(screen.getByText(/Денежный поток:/)).toBeTruthy();
  expect(
    screen.queryByText("Первые клиенты: как проверить канал привлечения"),
  ).toBeNull();
  fireEvent.click(
    document.querySelector('input[name="current_goal"][value="team"]')!,
  );
  send();
  await tick();
  expect(screen.getByText(/Делегирование:/)).toBeTruthy();
});
it("supports cold start, empty response, error and retry", async () => {
  render(<HomePage />);
  fireEvent.click(screen.getByText("Настройки демонстрации"));
  fireEvent.click(
    document.querySelector('input[name="current_goal"][value="team"]')!,
  );
  send();
  await tick();
  expect(screen.getByText(/Делегирование:/)).toBeTruthy();
  scenario("empty");
  send();
  await tick();
  expect(screen.getByText("Подборка не найдена")).toBeTruthy();
  scenario("error");
  send();
  await tick();
  expect(screen.getByRole("alert")).toBeTruthy();
  expect(
    (
      document.querySelector(
        'input[name="current_goal"]:checked',
      ) as HTMLInputElement
    ).value,
  ).toBe("team");
  scenario("success");
  fireEvent.click(screen.getByText("Попробовать снова"));
  await tick();
  expect(screen.getByText(/Делегирование:/)).toBeTruthy();
});
it("shows controlled timeout and invalid-response errors", async () => {
  render(<HomePage />);
  fireEvent.click(screen.getByText("Заполнить пример"));
  fireEvent.click(screen.getByText("Настройки демонстрации"));
  scenario("slow");
  send();
  await tick(12001);
  expect(
    screen.getByText("Не удалось загрузить рекомендации. Попробуйте ещё раз."),
  ).toBeTruthy();
  scenario("invalid");
  fireEvent.click(screen.getByText("Попробовать снова"));
  await tick();
  expect(
    screen.getByText("Не удалось загрузить рекомендации. Попробуйте ещё раз."),
  ).toBeTruthy();
});
it("scrolls toward mobile results without moving keyboard focus", async () => {
  const scroll = vi.fn();
  vi.stubGlobal("matchMedia", () => ({ matches: true }));
  const original = HTMLElement.prototype.scrollIntoView;
  HTMLElement.prototype.scrollIntoView = scroll;
  try {
    render(<HomePage />);
    fireEvent.click(screen.getByText("Заполнить пример"));
    const button = screen.getByRole("button", {
      name: /Подобрать материалы|Подобрать без уточнений/,
    });
    button.focus();
    send();
    await tick();
    expect(scroll).toHaveBeenCalledOnce();
    expect(document.activeElement).toBe(button);
  } finally {
    HTMLElement.prototype.scrollIntoView = original;
  }
});

it("hides diagnostics by default independently of mock mode", () => {
  vi.stubEnv("VITE_ENABLE_DIAGNOSTICS", "");
  render(<HomePage />);
  expect(screen.queryByText("Настройки демонстрации")).toBeNull();
  expect(screen.queryByLabelText("Сценарий")).toBeNull();
  expect(screen.getByText("Заполнить пример")).toBeTruthy();
});
it("never exposes diagnostics in production even when explicitly enabled", () => {
  vi.stubEnv("DEV", false);
  vi.stubEnv("VITE_ENABLE_DIAGNOSTICS", "true");
  render(<HomePage />);
  expect(screen.queryByText("Настройки демонстрации")).toBeNull();
});

it("keeps the submitted profile context until the next successful response", async () => {
  render(<HomePage />);
  fireEvent.click(screen.getByText("Заполнить пример"));
  send();
  await tick();
  expect(
    screen.getByRole("heading", { name: "Материалы о привлечении клиентов" }),
  ).toBeTruthy();
  expect(screen.getByText(/Профиль запроса:/).textContent).toContain(
    "Розничная торговля",
  );
  fireEvent.click(
    screen.getByRole("radio", { name: "Разобраться с финансами" }),
  );
  fireEvent.change(document.getElementById("industry")!, {
    target: { value: "services" },
  });
  expect(
    screen.getByRole("heading", { name: "Материалы о привлечении клиентов" }),
  ).toBeTruthy();
  expect(screen.getByText(/Профиль запроса:/).textContent).toContain(
    "Розничная торговля",
  );
  expect(screen.getByText(/Профиль запроса:/).textContent).not.toContain(
    "Услуги",
  );
  send();
  await tick();
  expect(
    screen.getByRole("heading", { name: "Материалы о финансах бизнеса" }),
  ).toBeTruthy();
  expect(screen.getByText(/Профиль запроса:/).textContent).toContain("Услуги");
  expect(screen.queryByRole("link", { name: /Открыть/ })).toBeNull();
  expect(
    screen.queryByText(/минут|Рейтинг|Стоимость|Чему научитесь/),
  ).toBeNull();
  expect(screen.getAllByText("Попробуйте после изучения")).toHaveLength(3);
});
