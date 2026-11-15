import unittest
from datetime import datetime, timedelta

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.data_processing.interactions import UserInteraction
from recommender.models import CatalogItem, UserProfile


def event(user, item, rating=5, days=0, item_type="article"):
    return UserInteraction(
        user, item, item_type, "rating", rating, None,
        datetime(2026, 1, 1) + timedelta(days=days),
    )


class CollaborativeTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            CatalogItem("a", "article", "A"), CatalogItem("b", "article", "B"),
            CatalogItem("c", "article", "C"), CatalogItem("d", "article", "D"),
            CatalogItem("a", "course", "Same raw ID"),
        ]
        self.events = [
            event("u1", "a"), event("u1", "b"),
            event("u2", "a"), event("u2", "b"),
            event("u3", "a"), event("u3", "c"),
            event("u4", "b", 2), event("u5", "d"),
        ]

    def test_similar_items(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=2, shrinkage=0)
        profile = UserProfile(positive_item_keys=frozenset({("article", "a")}))
        self.assertGreater(index.score(profile, ("article", "b")), 0)
        self.assertEqual(index.score(profile, ("article", "d")), 0)

    def test_weighted_history_changes_candidate_score(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1, shrinkage=0)
        equal = UserProfile(positive_item_keys=frozenset({("article", "a"), ("article", "c")}))
        weighted = UserProfile(
            positive_item_keys=frozenset({("article", "a"), ("article", "c")}),
            positive_item_weights=((("article", "a"), 1.0), (("article", "c"), 0.1)),
        )
        self.assertGreater(index.score(weighted, ("article", "b")), index.score(equal, ("article", "b")))

    def test_same_id_other_type_is_distinct(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1, shrinkage=0)
        profile = UserProfile(positive_item_keys=frozenset({("article", "a")}))
        self.assertEqual(index.score(profile, ("course", "a")), 0)

    def test_empty_history(self):
        index = ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1)
        self.assertEqual(index.score(UserProfile(), ("article", "b")), 0)

    def test_user_ids_not_retained(self):
        self.assertFalse(hasattr(ItemItemIndex.fit(self.events, self.catalog, min_cooccurrence=1), "user_ids"))


if __name__ == "__main__":
    unittest.main()
