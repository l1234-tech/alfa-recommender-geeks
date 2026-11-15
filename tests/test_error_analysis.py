import unittest
from datetime import datetime, timedelta, timezone

from recommender.data_processing.interactions import UserInteraction
from recommender.evaluation.error_analysis import analyze_recommendation_errors
from recommender.models import CatalogItem


class RecommendationErrorAnalysisTests(unittest.TestCase):
    def _events(self, user, target, target_type="article"):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = []
        for index in range(4):
            rows.append(UserInteraction(
                user_id=user, item_id=f"history-{index}", item_type="article",
                event_type="rating", rating_value=5, is_completed=None,
                event_at=start + timedelta(days=index),
            ))
        rows.append(UserInteraction(
            user_id=user, item_id=target, item_type=target_type,
            event_type="rating", rating_value=5, is_completed=None,
            event_at=start + timedelta(days=5),
        ))
        return rows

    def test_classifies_missing_unavailable_and_recommended_items(self):
        catalog = [
            CatalogItem("history-0","article","История 0"),
            CatalogItem("history-1","article","История 1"),
            CatalogItem("history-2","article","История 2"),
            CatalogItem("history-3","article","История 3"),
            CatalogItem("available","article","Доступный материал"),
            CatalogItem("hidden","article","Недоступный материал",is_available=False),
        ]
        events = (
            self._events("u1","available")
            + self._events("u2","hidden")
            + self._events("u3","outside-catalog")
        )
        result = analyze_recommendation_errors(events,catalog,k=10,strategies=("baseline",))
        row = result["baseline"]
        self.assertEqual(row["relevant_items"],3.0)
        self.assertEqual(row["recommended_in_top_k"],1.0)
        self.assertEqual(row["unavailable"],1.0)
        self.assertEqual(row["missing_from_catalog"],1.0)
        self.assertAlmostEqual(row["hit_rate@10"],1/3)
        self.assertAlmostEqual(row["miss_rate@10"],2/3)

    def test_rejects_invalid_k_and_unknown_strategy(self):
        with self.assertRaises(ValueError):
            analyze_recommendation_errors([],[],k=0)
        with self.assertRaises(ValueError):
            analyze_recommendation_errors([],[],strategies=("backend",))

    def test_empty_input_returns_zero_aggregates(self):
        result = analyze_recommendation_errors([],[],strategies=("baseline",))
        self.assertEqual(result["baseline"]["relevant_items"],0.0)
        self.assertEqual(result["baseline"]["hit_rate@10"],0.0)
        self.assertEqual(result["baseline"]["missing_from_catalog_rate"],0.0)


if __name__ == "__main__":
    unittest.main()
