import unittest

from recommender.data_processing.catalog import normalize_item
from recommender.data_processing.interactions import UserInteraction


class DataProcessingTests(unittest.TestCase):
    def test_normalize_boolean_values(self):
        item = normalize_item({"item_id": "x", "item_type": "article",
                               "title": "X", "is_available": "false"})
        self.assertFalse(item.is_available)

    def test_normalize_missing_metadata(self):
        item = normalize_item({"item_id": "x", "item_type": "article", "title": "X"})
        self.assertEqual(item.topics, frozenset())
        self.assertEqual(item.tags, frozenset())
        self.assertTrue(item.is_available)

    def test_interaction_contract_keeps_signal_types_separate(self):
        interaction = UserInteraction(
            user_id="internal", item_id="lesson-1", item_type="lesson",
            event_type="rating", rating_value=5, is_completed=None, event_at=None)
        self.assertEqual(interaction.event_type, "rating")
        self.assertEqual(interaction.rating_value, 5)
        self.assertIsNone(interaction.is_completed)
        self.assertEqual(interaction.item_key, ("lesson", "lesson-1"))


if __name__ == "__main__":
    unittest.main()
