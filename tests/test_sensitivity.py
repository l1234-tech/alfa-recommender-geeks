import unittest
from datetime import datetime, timedelta

from recommender.data_processing.interactions import UserInteraction
from recommender.evaluation.sensitivity import evaluate_cf_sensitivity
from recommender.models import CatalogItem


class SensitivityTests(unittest.TestCase):
    def test_grid_returns_aggregate_rows_without_user_identifiers(self):
        catalog = [
            CatalogItem("a", "article", "Основы продаж", topics=frozenset({"продажи"})),
            CatalogItem("b", "article", "Маркетинг", topics=frozenset({"маркетинг"})),
            CatalogItem("c", "article", "Финансы", topics=frozenset({"финансы"})),
            CatalogItem("d", "article", "Команда", topics=frozenset({"команда"})),
        ]
        events = []
        for user_index in range(5):
            user = f"user-{user_index}"
            for offset, item in enumerate(("a", "b", "c", "d")):
                events.append(UserInteraction(
                    user, item, "article", "rating",
                    5, None,
                    datetime(2026, 1, 1) + timedelta(days=offset),
                ))

        result = evaluate_cf_sensitivity(
            events, catalog,
            rating_thresholds=(4,),
            min_cooccurrences=(1, 2),
            shrinkages=(0.0,),
            k=2,
        )
        self.assertEqual(len(result), 8)
        self.assertTrue(all("users_evaluated" in row for row in result))
        self.assertTrue(all("ndcg@2" in row for row in result))
        self.assertTrue(all("user_id" not in row and "user_ids" not in row for row in result))

    def test_invalid_grid_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_cf_sensitivity([], [], min_cooccurrences=(0,))


if __name__ == "__main__":
    unittest.main()
