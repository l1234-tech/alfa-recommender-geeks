import unittest
from datetime import datetime, timedelta

from recommender.data_processing.interactions import UserInteraction
from recommender.evaluation.tuning import tune_hybrid_weights
from recommender.models import CatalogItem, UserProfile
from recommender.ranking import recommend


class HybridTuningTests(unittest.TestCase):
    def test_recommend_accepts_explicit_hybrid_weights(self):
        catalog = [
            CatalogItem("a", "article", "Маркетинг и продажи", topics=frozenset({"маркетинг"})),
            CatalogItem("b", "article", "Финансовое планирование", topics=frozenset({"финансы"})),
        ]
        profile = UserProfile(topics=frozenset({"маркетинг"}))
        result = recommend(profile, catalog, strategy="hybrid", tfidf_weight=0.8)
        self.assertEqual(result[0].item.item_id, "a")
        with self.assertRaises(ValueError):
            recommend(profile, catalog, strategy="hybrid", tfidf_weight=1.1)
        with self.assertRaises(ValueError):
            recommend(profile, catalog, strategy="hybrid", content_weight=-0.1)

    def test_grid_search_returns_aggregate_rows_without_user_ids(self):
        catalog = [
            CatalogItem("a", "article", "Основы продаж", topics=frozenset({"продажи"})),
            CatalogItem("b", "article", "Маркетинг", topics=frozenset({"маркетинг"})),
            CatalogItem("c", "article", "Финансы", topics=frozenset({"финансы"})),
            CatalogItem("d", "article", "Команда", topics=frozenset({"команда"})),
        ]
        events = []
        for user_index in range(5):
            for offset, item in enumerate(("a", "b", "c", "d")):
                events.append(UserInteraction(
                    f"user-{user_index}", item, "article", "rating", 5, None,
                    datetime(2026, 1, 1) + timedelta(days=offset),
                ))
        result = tune_hybrid_weights(
            events, catalog, tfidf_weights=(0.5, 0.7),
            content_weights=(0.4, 0.6), k=2,
        )
        self.assertEqual(len(result), 6)
        self.assertTrue(all("ndcg@2" in row for row in result))
        self.assertTrue(all("user_id" not in row and "user_ids" not in row for row in result))
        self.assertEqual(result, sorted(
            result, key=lambda row: (
                -float(row["ndcg@2"]), -float(row["recall@2"]),
                -float(row["precision@2"]), -float(row["catalog_coverage"]),
            )
        ))

    def test_invalid_grid_is_rejected(self):
        with self.assertRaises(ValueError):
            tune_hybrid_weights([], [], tfidf_weights=(1.2,))


if __name__ == "__main__":
    unittest.main()
