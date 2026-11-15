import unittest

from recommender.algorithms.content_baseline import score_item
from recommender.algorithms.tfidf import TfidfIndex, tokenize
from recommender.models import CatalogItem, UserProfile


class FeatureQualityTests(unittest.TestCase):
    def test_missing_metadata_is_not_treated_as_mismatch(self):
        profile = UserProfile(
            topics=frozenset({"marketing"}),
            tags=frozenset({"beginner"}),
            industries=frozenset({"retail"}),
        )
        full = CatalogItem(
            "full", "article", "Marketing",
            topics=frozenset({"marketing"}),
            tags=frozenset({"beginner"}),
            industries=frozenset({"retail"}),
        )
        partial = CatalogItem(
            "partial", "article", "Marketing",
            topics=frozenset({"marketing"}),
        )
        self.assertEqual(score_item(profile, full), 1.0)
        self.assertEqual(score_item(profile, partial), 1.0)

    def test_no_comparable_fields_returns_zero(self):
        profile = UserProfile(topics=frozenset({"marketing"}))
        item = CatalogItem("x", "article", "Untyped title")
        self.assertEqual(score_item(profile, item), 0.0)

    def test_tfidf_includes_type_and_boosts_title(self):
        title_match = CatalogItem("a", "article", "Маркетинг стратегия", "Общий текст")
        description_match = CatalogItem("b", "article", "Другое", "Маркетинг стратегия")
        index = TfidfIndex.fit([title_match, description_match])
        profile = UserProfile(current_goal="маркетинг стратегия")
        self.assertGreater(index.score(profile, title_match), index.score(profile, description_match))

    def test_duplicate_typed_keys_are_rejected(self):
        items = [
            CatalogItem("same", "article", "First"),
            CatalogItem("same", "article", "Duplicate"),
        ]
        with self.assertRaises(ValueError):
            TfidfIndex.fit(items)

    def test_same_raw_id_different_types_are_allowed(self):
        items = [
            CatalogItem("same", "article", "Article"),
            CatalogItem("same", "course", "Course"),
        ]
        index = TfidfIndex.fit(items)
        self.assertEqual(len(index.item_keys), 2)

    def test_tokenizer_handles_mixed_case_and_unicode(self):
        self.assertEqual(tokenize("ML-инструменты AND бизнес"), ["ml-инструменты", "бизнес"])


if __name__ == "__main__":
    unittest.main()
