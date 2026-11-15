"""Минимальный интерфейс демонстрации персональных рекомендаций «Альфа-Курса».

Собирает профиль пользователя, вызывает backend API и показывает карточки
рекомендаций с объяснениями и следующим шагом. Намеренно простой: цель —
показать сквозной сценарий, а не повторять сайт платформы.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ENDPOINT = f"{BACKEND_URL}/api/v1/recommendations"

STAGES = ["", "early", "growth", "scaling"]
EXPERIENCE = ["", "beginner", "intermediate", "advanced"]
INDUSTRIES = ["", "retail", "services", "ecommerce", "b2b", "any"]
GOALS = ["", "marketing", "sales", "accounting", "launch", "operations", "finance"]
FORMATS = ["course", "article", "template", "webinar", "checklist", "podcast", "document"]

st.set_page_config(page_title="Альфа-Курс · Рекомендации", page_icon="🎓", layout="centered")
st.title("🎓 Персональные рекомендации «Альфа-Курса»")
st.caption("Заполните профиль — система подберёт материалы, объяснит выбор и предложит следующий шаг.")

with st.form("profile"):
    col1, col2 = st.columns(2)
    with col1:
        business_stage = st.selectbox("Стадия бизнеса", STAGES,
                                      help="Оставьте пустым — получите стартовую подборку (холодный старт).")
        industry = st.selectbox("Сфера", INDUSTRIES)
        experience_level = st.selectbox("Опыт", EXPERIENCE)
    with col2:
        current_goal = st.selectbox("Текущая задача", GOALS)
        preferred_formats = st.multiselect("Предпочитаемые форматы", FORMATS)
        limit = st.slider("Сколько материалов", 1, 20, 5)

    history_raw = st.text_input("Уже просмотрено (material_id через запятую, необязательно)",
                                placeholder="mat-mkt-001, mat-acc-001")
    submitted = st.form_submit_button("Получить рекомендации", use_container_width=True)

if submitted:
    history = [{"material_id": m.strip(), "event_type": "view"}
               for m in history_raw.split(",") if m.strip()]
    payload = {
        "user_profile": {
            "business_stage": business_stage or None,
            "industry": industry or None,
            "current_goal": current_goal or None,
            "experience_level": experience_level or None,
            "preferred_formats": preferred_formats,
        },
        "history": history,
        "limit": limit,
    }

    try:
        resp = requests.post(ENDPOINT, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        st.error(f"Не удалось получить рекомендации: {exc}\n\nБэкенд доступен по {ENDPOINT}?")
        st.stop()

    meta = data.get("metadata", {})
    cols = st.columns(3)
    cols[0].metric("Найдено", meta.get("returned", 0))
    cols[1].metric("Стратегия", meta.get("strategy", "—"))
    cols[2].metric("Холодный старт", "да" if meta.get("cold_start") else "нет")

    if meta.get("cold_start"):
        st.info("Профиль пуст — показываем стартовую подборку, чтобы начать знакомство с платформой.")

    recommendations = data.get("recommendations", [])
    if not recommendations:
        st.warning("Подходящих материалов не нашлось. Уточните профиль или задачу.")

    for rec in recommendations:
        with st.container(border=True):
            top = st.columns([6, 2])
            paid = "💳 платный" if rec.get("is_paid") else "🆓 бесплатно"
            top[0].subheader(rec.get("title", "—"))
            top[1].markdown(f"**{paid}**")
            tags = " · ".join(filter(None, [rec.get("material_type"), rec.get("topic")]))
            if tags:
                st.caption(tags)
            st.progress(min(max(float(rec.get("score", 0.0)), 0.0), 1.0),
                        text=f"релевантность {rec.get('score', 0.0):.2f}")
            reasons = rec.get("reasons") or []
            if reasons:
                st.markdown("**Почему:** " + "; ".join(reasons))
            if rec.get("next_step"):
                st.markdown(f"**Следующий шаг:** {rec['next_step']}")
            if rec.get("url"):
                st.markdown(f"[Открыть материал]({rec['url']})")

st.divider()
st.caption(f"API: {ENDPOINT}")
