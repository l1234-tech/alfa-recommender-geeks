import unittest
from datetime import datetime, timedelta

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.models import CatalogItem, UserProfile


def event(user, item, rating=5, days=0):
    return UserInteraction(
        user_id=user,
        item_id=item,
        item_type="article",
        event_type="rating",
        rating_value=rating,
        is_completed=None,
        event_at=datetime(2026, 1, 1) + timedelta(days=days),
    )


class CollaborativeTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            CatalogItem("a", "article", "A"),
            CatalogItem("b", "article", "B"),
            CatalogItem("c", "article", "C"),
            CatalogItem("d", "article", "D"),
        ]
        self.events = [
            event("u1", "a"), event("u1", "b"),
            event("u2", "a"), event("u2", "b"),
            event("u3", "a"), event("u3", "c"),
            event("u4", "b", rating=2),
            event("u5", "d"),
        ]

    def test_similar_items_are_retrieved_from_positive_cooccurrence(self):
        index = ItemItemIndex.fit(
            self.events, self.catalog, min_cooccurrence=2, shrinkage=0
        )
        score = index.score(UserProfile(positive_item_ids=frozenset({"a"})), "b")
        self.assertGreater(score, 0)
        self.assertEqual(index.score(UserProfile(positive_item_ids=frozenset({"a"})), "d"), 0)

    def test_no_positive_history_means_no_cf_signal(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1)
        self.assertEqual(index.score(UserProfile(), "b"), 0)

    def test_user_ids_are_not_retained_in_index(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1)
        self.assertFalse(hasattr(index, "user_ids"))


if __name__ == "__main__":
    unittest.main()
