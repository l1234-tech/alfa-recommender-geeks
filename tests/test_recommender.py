import unittest

from recommender.data_processing.catalog import normalize_item
from recommender.models import CatalogItem, UserProfile
from recommender.ranking import recommend


class RecommenderTests(unittest.TestCase):
    def test_normalize_item(self):
        item = normalize_item({
            "item_id": "a1",
            "item_type": "article",
            "title": "Marketing basics",
            "topics": ["marketing", "sales"],
            "tags": "beginner",
        })
        self.assertEqual(item.item_id, "a1")
        self.assertEqual(item.topics, frozenset({"marketing", "sales"}))
        self.assertEqual(item.tags, frozenset({"beginner"}))

    def test_ranking_prefers_metadata_overlap(self):
        profile = UserProfile(
            topics=frozenset({"marketing"}),
            industries=frozenset({"retail"}),
        )
        matching = CatalogItem(
            item_id="1", item_type="article", title="Marketing",
            topics=frozenset({"marketing"}),
            industries=frozenset({"retail"}),
        )
        unrelated = CatalogItem(item_id="2", item_type="article", title="Accounting")
        result = recommend(profile, [unrelated, matching])
        self.assertEqual(result[0].item.item_id, "1")
        self.assertGreater(result[0].score, result[1].score)

    def test_unavailable_seen_and_completed_are_filtered(self):
        profile = UserProfile(
            seen_item_ids=frozenset({"seen"}),
            completed_item_ids=frozenset({"done"}),
        )
        catalog = [
            CatalogItem(item_id="seen", item_type="article", title="Seen"),
            CatalogItem(item_id="done", item_type="course", title="Done"),
            CatalogItem(item_id="hidden", item_type="article", title="Hidden", is_available=False),
            CatalogItem(item_id="new", item_type="article", title="New"),
        ]
        result = recommend(profile, catalog)
        self.assertEqual([item.item.item_id for item in result], ["new"])

    def test_limit_and_empty_profile(self):
        catalog = [
            CatalogItem(item_id="b", item_type="article", title="B"),
            CatalogItem(item_id="a", item_type="article", title="A"),
        ]
        result = recommend(UserProfile(), catalog, limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].item.item_id, "a")


if __name__ == "__main__":
    unittest.main()
