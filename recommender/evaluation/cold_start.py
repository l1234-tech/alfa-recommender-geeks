"""Synthetic expert-authored onboarding-only cold-start benchmark."""
from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass
from recommender.algorithms.tfidf import TfidfIndex
from recommender.evaluation.metrics import aggregate_ranking_metrics, catalog_coverage
from recommender.models import CatalogItem, ItemKey, UserProfile
from recommender.ranking import recommend

@dataclass(frozen=True)
class ColdStartCase:
    profile: UserProfile
    relevant_item_keys: frozenset[ItemKey]

def evaluate_cold_start_cases(cases: Iterable[ColdStartCase], catalog: list[CatalogItem], *,
                              k: int = 5, strategies: tuple[str, ...] = ("baseline", "hybrid")
                              ) -> dict[str, dict[str, float]]:
    """Compare content strategies; relevance labels are manually reviewed, not inferred."""
    if k < 1:
        raise ValueError("k must be >= 1")
    rows = list(cases)
    if not rows:
        return {s: {"profiles_evaluated": 0.0, f"precision@{k}": 0.0,
                    f"recall@{k}": 0.0, f"ndcg@{k}": 0.0, f"hit_rate@{k}": 0.0,
                    f"mrr@{k}": 0.0, "catalog_coverage": 0.0,
                    "explanation_coverage": 0.0} for s in strategies}
    tfidf = TfidfIndex.fit(catalog)
    available = {x.key for x in catalog if x.is_available}
    output = {}
    for strategy in strategies:
        predictions, explanation_flags = [], []
        for case in rows:
            p = case.profile
            if p.positive_item_keys or p.positive_item_weights or p.completed_item_keys or p.seen_item_keys:
                raise ValueError("cold-start profiles must not contain interaction history")
            ranked = recommend(p, catalog, limit=k, strategy=strategy, tfidf_index=tfidf)
            predictions.append([r.item.key for r in ranked])
            explanation_flags.extend(bool(r.reason.strip() and r.next_step.strip()) for r in ranked)
        relevant = [set(c.relevant_item_keys) for c in rows]
        metrics = aggregate_ranking_metrics(predictions, relevant, k)
        metrics["profiles_evaluated"] = metrics.pop("users_evaluated")
        hits, reciprocal = [], []
        for prediction, rel in zip(predictions, relevant):
            rank = next((i for i, key in enumerate(prediction[:k], 1) if key in rel), None)
            hits.append(rank is not None)
            reciprocal.append(1.0 / rank if rank else 0.0)
        metrics[f"hit_rate@{k}"] = sum(hits) / len(hits)
        metrics[f"mrr@{k}"] = sum(reciprocal) / len(reciprocal)
        metrics["explanation_coverage"] = sum(explanation_flags) / len(explanation_flags) if explanation_flags else 0.0
        metrics.update(catalog_coverage(predictions, available))
        output[strategy] = metrics
    return output

def build_expert_cold_start_benchmark() -> tuple[list[CatalogItem], list[ColdStartCase]]:
    """Build five synthetic profiles; stage/experience are encoded in onboarding tags/topics."""
    catalog = [
        CatalogItem("validate-demand","article","Проверка спроса на идею","Интервью с клиентами и проверка гипотез",
          topics=frozenset({"валидация","исследование"}),tags=frozenset({"идея","начинающий"}),industries=frozenset({"retail","services"})),
        CatalogItem("first-sales","course","Первые продажи","Запуск продаж и поиск первых клиентов",
          topics=frozenset({"продажи","запуск"}),tags=frozenset({"стартап","начинающий"}),industries=frozenset({"it","services"})),
        CatalogItem("retail-marketing","article","Маркетинг розничного магазина","Привлечение покупателей и локальное продвижение",
          topics=frozenset({"маркетинг"}),tags=frozenset({"рост"}),industries=frozenset({"retail"})),
        CatalogItem("manufacturing-process","document","Оптимизация производства","Управление процессами и операционная эффективность",
          topics=frozenset({"операции","процессы"}),tags=frozenset({"масштабирование"}),industries=frozenset({"manufacturing"})),
        CatalogItem("cash-flow","calculator","Планирование денежного потока","Финансовое планирование и контроль денежных потоков",
          topics=frozenset({"финансы"}),tags=frozenset({"управление"}),industries=frozenset({"manufacturing","retail"})),
        CatalogItem("team-hiring","webinar","Найм и развитие команды","Подбор сотрудников и управление командой",
          topics=frozenset({"команда","найм"}),tags=frozenset({"опытный","управление"}),industries=frozenset({"services","it"})),
        CatalogItem("service-sales","article","Продажи услуг","Упаковка предложения и привлечение заказчиков",
          topics=frozenset({"продажи"}),tags=frozenset({"рост"}),industries=frozenset({"services"})),
        CatalogItem("digital-product","course","Запуск цифрового продукта","Проверка продукта и выход на рынок",
          topics=frozenset({"запуск","продукт"}),tags=frozenset({"стартап"}),industries=frozenset({"it"})),
        CatalogItem("general-leadership","article","Основы управления бизнесом","Базовые управленческие практики",topics=frozenset({"управление"})),
        CatalogItem("unavailable-finance","course","Закрытый финансовый курс",topics=frozenset({"финансы"}),is_available=False),
    ]
    cases = [
      ColdStartCase(UserProfile(topics=frozenset({"валидация","исследование"}),tags=frozenset({"идея","начинающий"}),
        industries=frozenset({"retail"}),current_goal="проверить спрос на идею"),frozenset({("article","validate-demand")})),
      ColdStartCase(UserProfile(topics=frozenset({"продажи","запуск"}),tags=frozenset({"стартап","начинающий"}),
        industries=frozenset({"it"}),current_goal="найти первых клиентов"),
        frozenset({("course","first-sales"),("course","digital-product")})),
      ColdStartCase(UserProfile(topics=frozenset({"операции","финансы"}),tags=frozenset({"масштабирование","управление"}),
        industries=frozenset({"manufacturing"}),current_goal="оптимизировать процессы производства"),
        frozenset({("document","manufacturing-process"),("calculator","cash-flow")})),
      ColdStartCase(UserProfile(topics=frozenset({"команда","найм"}),tags=frozenset({"опытный","управление"}),
        industries=frozenset({"services"}),current_goal="нанять сотрудников и развивать команду"),
        frozenset({("webinar","team-hiring")})),
      ColdStartCase(UserProfile(topics=frozenset({"маркетинг","продажи"}),tags=frozenset({"начинающий"}),
        industries=frozenset({"retail"}),current_goal="привлекать покупателей в магазин"),
        frozenset({("article","retail-marketing"),("article","service-sales")})),
    ]
    return catalog, cases
