import { useEffect, useRef, useState } from "react";
import { mockEnabled, getRecommendations } from "../api/recommendations";
import type { Scenario } from "../api/mock";
import {
  emptyProfile,
  goalTitles,
  profileSummary,
  type Profile,
  exampleProfile,
  profileErrors,
  toRequest,
} from "../config/profile";
import type {
  Recommendation,
  RecommendationResponse,
} from "../types/recommendation";
import { ProfileForm } from "../components/ProfileForm";
import { RecommendationList } from "../components/RecommendationList";
type State =
  | { kind: "initial" }
  | { kind: "loading"; key: string }
  | {
      kind: "success";
      key: string;
      profile: Profile;
      metadata: RecommendationResponse["metadata"];
      items: Recommendation[];
    }
  | { kind: "error"; key: string };
export function HomePage() {
  const diagnostics =
    import.meta.env.DEV && import.meta.env.VITE_ENABLE_DIAGNOSTICS === "true";
  const [profile, setProfile] = useState(emptyProfile),
    [scenario, setScenario] = useState<Scenario>("success"),
    [errors, setErrors] = useState<string[]>([]),
    [state, setState] = useState<State>({ kind: "initial" });
  const active = useRef<AbortController | null>(null),
    sequence = useRef(0);
  useEffect(
    () => () => {
      active.current?.abort();
    },
    [],
  );
  const key = JSON.stringify([toRequest(profile), scenario]);
  const changed = state.kind !== "initial" && state.key !== key;
  async function submit() {
    const invalid = profileErrors(profile);
    setErrors(invalid);
    if (invalid.length) {
      document.getElementById(invalid[0])?.focus();
      return;
    }
    if (state.kind === "loading" && state.key === key) return;
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    const id = ++sequence.current;
    const submittedProfile = { ...profile };
    setState({ kind: "loading", key });
    if (window.matchMedia?.("(max-width: 650px)").matches) {
      document
        .getElementById("results-title")
        ?.scrollIntoView({ block: "start", behavior: "instant" });
    }
    try {
      const response = await getRecommendations(
        toRequest(profile),
        controller.signal,
        diagnostics ? scenario : "success",
      );
      if (id === sequence.current && !controller.signal.aborted)
        setState({
          kind: "success",
          key,
          profile: submittedProfile,
          items: response.recommendations,
          metadata: response.metadata,
        });
    } catch {
      if (id === sequence.current && !controller.signal.aborted)
        setState({
          kind: "error",
          key,
        });
    }
  }
  return (
    <>
      <header>
        <a className="brand" href="./">
          Alfa<span> Recommender</span>
          <i>.</i>
        </a>
      </header>
      <main>
        <div className="page-heading">
          <div>
            <h1>Какую задачу бизнеса хотите решить?</h1>
            <p>
              Найдём учебные материалы, которые помогут разобраться и перейти к
              действиям
            </p>
          </div>
        </div>
        {mockEnabled && diagnostics && (
          <details className="demo-settings">
            <summary>Настройки демонстрации</summary>
            <p className="fine">
              Готовые примеры по задаче. Модель не подключена.
            </p>
            <label>
              Сценарий{" "}
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value as Scenario)}
              >
                <option value="success">Обычная выдача</option>
                <option value="empty">Нет результатов</option>
                <option value="error">Ошибка сервера</option>
                <option value="slow">Медленный ответ / таймаут</option>
                <option value="invalid">Некорректный ответ</option>
              </select>
            </label>
          </details>
        )}
        <div className="workspace">
          <aside className="profile-panel">
            <ProfileForm
              profile={profile}
              onChange={setProfile}
              onSubmit={() => void submit()}
              loading={state.kind === "loading" && !changed}
              errors={errors}
              mock={mockEnabled}
              onExample={() => {
                setProfile({ ...exampleProfile });
                setErrors([]);
              }}
            />
          </aside>
          <section className="results" aria-labelledby="results-title">
            <div className="result-heading">
              <div>
                <h2 id="results-title">
                  {state.kind === "initial"
                    ? "Здесь появятся рекомендации"
                    : state.kind === "success"
                      ? (goalTitles[state.profile.current_goal] ??
                        "Рекомендации для вас")
                      : "Рекомендации для вас"}
                </h2>
                {state.kind === "success" && profileSummary(state.profile) && (
                  <p className="profile-summary">
                    Профиль запроса: {profileSummary(state.profile)}
                  </p>
                )}
                {mockEnabled &&
                  state.kind === "success" &&
                  state.items.length > 0 && (
                    <p className="example-caption">Пример подборки</p>
                  )}
                {!mockEnabled &&
                  state.kind === "success" &&
                  state.metadata.catalog_source === "sample" && (
                    <p className="example-caption">
                      Подборка по учебному каталогу
                    </p>
                  )}
              </div>
            </div>
            <div role="status" aria-live="polite">
              {changed && (
                <p className="notice">
                  Параметры изменились. Обновите подборку
                </p>
              )}
              {state.kind === "loading" && (
                <p className="notice">Подбираем материалы…</p>
              )}
            </div>

            {state.kind === "initial" && (
              <p className="initial-hint">
                Выберите задачу и расскажите немного о бизнесе.
              </p>
            )}
            {state.kind === "loading" && (
              <div className="skeleton" aria-hidden="true">
                {[1, 2, 3].map((n) => (
                  <div key={n}>
                    <span />
                    <span />
                    <span />
                  </div>
                ))}
              </div>
            )}
            {state.kind === "error" && (
              <div className="placeholder error" role="alert">
                <h3>Подборка пока недоступна</h3>
                <p>Не удалось загрузить рекомендации. Попробуйте ещё раз.</p>
                <button className="secondary" onClick={() => void submit()}>
                  Попробовать снова
                </button>
              </div>
            )}
            {state.kind === "success" &&
              (state.items.length ? (
                <RecommendationList
                  items={state.items}
                  practicalSteps={mockEnabled}
                />
              ) : (
                <div className="placeholder">
                  <h3>Подборка не найдена</h3>
                  <p>
                    Измените задачу или другие параметры профиля и запросите
                    материалы снова.
                  </p>
                  <button
                    className="secondary"
                    onClick={() =>
                      document.getElementById("current_goal")?.focus()
                    }
                  >
                    Изменить профиль
                  </button>
                </div>
              ))}
          </section>
        </div>
      </main>
    </>
  );
}
