"""In-memory demo catalog for a self-contained, DB-free MVP and tests.

These are illustrative public-style materials, NOT the private dataset. The
real catalog loader (recommender/data_processing) can replace `get_catalog()`
later without changing the API layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Material:
    material_id: str
    material_type: str  # course | article | template | webinar | checklist
    title: str
    description: str
    topic: str
    topics: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    industries: frozenset[str] = field(default_factory=frozenset)
    is_paid: bool | None = None
    is_available: bool = True
    url: str | None = None


def _m(**kw) -> Material:
    for key in ("topics", "tags", "industries"):
        if key in kw:
            kw[key] = frozenset(kw[key])
    return Material(**kw)


_CATALOG: list[Material] = [
    _m(material_id="mat-launch-001", material_type="article", topic="launch",
       title="С чего начать свой бизнес: первые 5 шагов",
       description="Пошаговый вводный материал для тех, кто только планирует открыть дело.",
       topics=["launch", "registration"], tags=["early", "beginner"],
       industries=["any"], url="/materials/mat-launch-001"),
    _m(material_id="mat-launch-002", material_type="checklist", topic="launch",
       title="Чек-лист регистрации ИП и ООО",
       description="Готовый чек-лист шагов регистрации бизнеса и выбора режима налогообложения.",
       topics=["launch", "registration", "taxes"], tags=["early", "beginner"],
       industries=["any"], url="/materials/mat-launch-002"),
    _m(material_id="mat-mkt-001", material_type="course", topic="marketing",
       title="Маркетинг для начинающего бизнеса",
       description="Базовый курс по привлечению первых клиентов и продвижению в соцсетях.",
       topics=["marketing", "promotion"], tags=["early", "beginner"],
       industries=["retail", "services"], is_paid=True, url="/materials/mat-mkt-001"),
    _m(material_id="mat-mkt-002", material_type="article", topic="marketing",
       title="Как настроить таргетированную рекламу с нуля",
       description="Разбор запуска таргета для малого бизнеса без агентства.",
       topics=["marketing", "promotion", "ads"], tags=["growth", "intermediate"],
       industries=["retail", "ecommerce"], url="/materials/mat-mkt-002"),
    _m(material_id="mat-mkt-003", material_type="template", topic="marketing",
       title="Шаблон контент-плана на месяц",
       description="Готовый рабочий шаблон контент-плана для соцсетей.",
       topics=["marketing", "content"], tags=["growth", "intermediate"],
       industries=["services", "ecommerce"], url="/materials/mat-mkt-003"),
    _m(material_id="mat-sales-001", material_type="course", topic="sales",
       title="Продажи для малого бизнеса",
       description="Как выстроить воронку продаж и закрывать сделки.",
       topics=["sales", "funnel"], tags=["growth", "intermediate"],
       industries=["retail", "b2b"], is_paid=True, url="/materials/mat-sales-001"),
    _m(material_id="mat-sales-002", material_type="article", topic="sales",
       title="Скрипты продаж, которые работают",
       description="Примеры скриптов для звонков и переписки с клиентами.",
       topics=["sales", "scripts"], tags=["growth", "beginner"],
       industries=["b2b", "services"], url="/materials/mat-sales-002"),
    _m(material_id="mat-acc-001", material_type="article", topic="accounting",
       title="Бухучёт для предпринимателя простыми словами",
       description="Вводный материал по учёту доходов, расходов и налогам.",
       topics=["accounting", "taxes"], tags=["early", "beginner"],
       industries=["any"], url="/materials/mat-acc-001"),
    _m(material_id="mat-acc-002", material_type="checklist", topic="accounting",
       title="Чек-лист налоговых сроков на год",
       description="Когда и какие налоги платить по разным режимам налогообложения.",
       topics=["accounting", "taxes"], tags=["growth", "intermediate"],
       industries=["any"], url="/materials/mat-acc-002"),
    _m(material_id="mat-ops-001", material_type="course", topic="operations",
       title="Организация ежедневной работы соло-фаундера",
       description="Системный курс по процессам, планированию и делегированию.",
       topics=["team", "operations", "productivity"], tags=["scaling", "advanced"],
       industries=["any"], is_paid=True, url="/materials/mat-ops-001"),
    _m(material_id="mat-ops-002", material_type="webinar", topic="operations",
       title="Вебинар: автоматизация рутины в малом бизнесе",
       description="Инструменты автоматизации процессов и экономии времени.",
       topics=["operations", "automation"], tags=["scaling", "advanced"],
       industries=["services", "ecommerce"], url="/materials/mat-ops-002"),
    _m(material_id="mat-fin-001", material_type="template", topic="finance",
       title="Шаблон финансовой модели для старта",
       description="Готовая таблица для расчёта юнит-экономики и точки безубыточности.",
       topics=["finance", "unit-economics"], tags=["early", "intermediate"],
       industries=["any"], url="/materials/mat-fin-001"),
]


def get_catalog() -> list[Material]:
    """Return the available demo catalog."""
    return [m for m in _CATALOG if m.is_available]
