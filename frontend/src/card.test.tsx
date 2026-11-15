// @vitest-environment jsdom
import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { RecommendationCard } from "./components/RecommendationCard";
import { fixtures } from "./api/mock";
afterEach(cleanup);
it("renders all reasons, safe links and preserves unknown payment", () => {
  const item = {
    ...fixtures.recommendations[0],
    material_type: "future_format",
    topic: null,
    is_paid: null,
    url: "javascript:alert(1)",
    reasons: ["Первая причина", "Вторая причина"],
  };
  const view = render(<RecommendationCard item={item} />);
  expect(screen.getByText("Вторая причина")).toBeTruthy();
  expect(screen.queryByRole("link")).toBeNull();
  expect(screen.getByText("Следующий шаг")).toBeTruthy();
  expect(screen.getByText(item.next_step)).toBeTruthy();
  expect(
    screen.getByText("Материал пока недоступен для перехода"),
  ).toBeTruthy();
  expect(screen.queryByText(/Бесплатный/)).toBeNull();
  view.rerender(
    <RecommendationCard
      item={{
        ...item,
        url: "https://example.org/course",
        description: "Описание из каталога",
      }}
    />,
  );
  const link = screen.getByRole("link", { name: /Открыть материал/ });
  expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  expect(link.getAttribute("href")).toBe("https://example.org/course");
});
