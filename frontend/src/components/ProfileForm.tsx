import { fields, goalField, type Profile } from "../config/profile";
interface Props {
  profile: Profile;
  onChange: (value: Profile) => void;
  onSubmit: () => void;
  loading: boolean;
  errors: string[];
  mock: boolean;
  onExample: () => void;
}
export function ProfileForm({
  profile,
  onChange,
  onSubmit,
  loading,
  errors,
  mock,
  onExample,
}: Props) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      noValidate
    >
      <h2>Расскажите о бизнесе</h2>
      <fieldset
        className="goal-options"
        aria-describedby={
          errors.includes("current_goal") ? "current_goal-error" : undefined
        }
      >
        <legend>Что сейчас важно для бизнеса?</legend>
        {goalField.options.map(([value, label], index) => (
          <label className="goal-option" key={value}>
            <input
              type="radio"
              name="current_goal"
              id={index === 0 ? "current_goal" : "goal-" + value}
              value={value}
              checked={profile.current_goal === value}
              aria-invalid={errors.includes("current_goal")}
              onChange={() => onChange({ ...profile, current_goal: value })}
            />
            <span>{label}</span>
          </label>
        ))}
        {errors.includes("current_goal") && (
          <span className="field-error" id="current_goal-error">
            Выберите задачу бизнеса.
          </span>
        )}
      </fieldset>
      <h3 className="refine-heading">Уточните подборку</h3>
      <p className="muted intro">
        Все поля необязательны. Можно подобрать материалы без уточнений.
      </p>
      {fields
        .filter((field) => field.key !== "current_goal")
        .map((field) => (
          <div className="field" key={field.key}>
            <label htmlFor={field.key}>{field.label}</label>
            <select
              id={field.key}
              value={profile[field.key]}
              aria-invalid={errors.includes(field.key)}
              aria-describedby={
                errors.includes(field.key) ? field.key + "-error" : undefined
              }
              onChange={(e) =>
                onChange({ ...profile, [field.key]: e.target.value })
              }
            >
              <option value="">Не указывать</option>
              {field.options.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {errors.includes(field.key) && (
              <span className="field-error" id={field.key + "-error"}>
                Выберите вариант для этого поля.
              </span>
            )}
          </div>
        ))}

      <p className="fine">В подборке могут быть и другие форматы.</p>
      <fieldset className="format-options">
        <legend>Предпочтительный формат</legend>
        {[
          ["course", "Курс"],
          ["article", "Статья"],
          ["webinar", "Вебинар"],
          ["document", "Документ"],
          ["podcast", "Подкаст"],
        ].map(([value, label]) => (
          <label key={value}>
            <input
              type="checkbox"
              checked={profile.preferred_formats.includes(value)}
              onChange={(event) =>
                onChange({
                  ...profile,
                  preferred_formats: event.target.checked
                    ? [...profile.preferred_formats, value]
                    : profile.preferred_formats.filter(
                        (format) => format !== value,
                      ),
                })
              }
            />
            {label}
          </label>
        ))}
      </fieldset>
      {mock && (
        <button className="example-button" type="button" onClick={onExample}>
          Заполнить пример
        </button>
      )}
      <button className="primary" disabled={loading} type="submit">
        {loading
          ? "Подбираем материалы…"
          : !Object.values(profile).some((value) => value.length)
            ? "Подобрать без уточнений"
            : "Подобрать материалы"}
      </button>
    </form>
  );
}
