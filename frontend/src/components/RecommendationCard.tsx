import type { Recommendation } from "../types/recommendation";
import { safeMaterialUrl } from "../api/recommendations";
const formats: Record<string, string> = {
  course: "Курс",
  article: "Статья",
  document: "Документ",
  template: "Шаблон",
  checklist: "Чек-лист",
  webinar: "Вебинар",
  podcast: "Подкаст",
  lesson: "Урок",
  calculator: "Калькулятор",
};
const topics: Record<string, string> = {
  marketing: "Маркетинг",
  finance: "Финансы",
  team: "Команда",
  operations: "Управление бизнесом",
  sales: "Продажи",
  launch: "Старт бизнеса",
  accounting: "Учёт",
  taxes: "Налоги",
  registration: "Регистрация",
};
export function RecommendationCard({
  item,
  practicalStep = false,
}: {
  item: Recommendation;
  practicalStep?: boolean;
}) {
  const url = safeMaterialUrl(item.url);
  const action =
    (
      {
        article: "Открыть статью",
        course: "Перейти к курсу",
        lesson: "Открыть урок",
        webinar: "Открыть вебинар",
      } as Record<string, string>
    )[item.material_type] ?? "Открыть материал";
  return (
    <article className="material">
      <p className="material-details">
        {formats[item.material_type] ?? "Материал"}
        {item.topic && <> · {topics[item.topic] ?? item.topic}</>}
        {item.is_paid === true && " · Платный"}
        {item.is_paid === false && " · Бесплатный"}
      </p>
      <h3>
        {url ? (
          <a href={url} target="_blank" rel="noopener noreferrer">
            {item.title}
          </a>
        ) : (
          item.title
        )}
      </h3>
      {item.description && (
        <p className="material-description">{item.description}</p>
      )}
      {item.reasons.length > 0 && (
        <div className="reason">
          <h4>Почему подходит</h4>
          <ul>
            {item.reasons.map((reason, index) => (
              <li key={index}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="next">
        <h4>
          {practicalStep ? "Попробуйте после изучения" : "Следующий шаг"}
        </h4>
        <p>{item.next_step}</p>
      </div>
      {!url && (
        <p className="availability-note">
          Материал пока недоступен для перехода
        </p>
      )}
      {url && (
        <a
          className="material-link"
          href={url}
          target="_blank"
          rel="noopener noreferrer"
        >
          {action} ↗
        </a>
      )}
    </article>
  );
}
