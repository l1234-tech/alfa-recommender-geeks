import unittest

from recommender.algorithms.collaborative import ItemItemIndex
from recommender.algorithms.tfidf import TfidfIndex
from recommender.algorithms.hybrid import score_hybrid
from recommender.data_processing.interactions import UserInteraction
from recommender.models import CatalogItem, UserProfile
from recommender.ranking import recommend


class TfidfTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            CatalogItem("m1", "article", "Маркетинг для малого бизнеса",
                        "Продвижение и продажи", topics=frozenset({"маркетинг"})),
            CatalogItem("m2", "article", "Финансовый учет",
                        "Бюджет и денежный поток", topics=frozenset({"финансы"})),
            CatalogItem("m3", "course", "Продвижение интернет-магазина",
                        "Маркетинг и продажи", topics=frozenset({"маркетинг"})),
        ]
        self.index = TfidfIndex.fit(self.catalog)

    def test_relevant_text_scores_higher(self):
        profile = UserProfile(topics=frozenset({"маркетинг"}), current_goal="продвижение продажи")
        self.assertGreater(self.index.score(profile, "m1"), self.index.score(profile, "m2"))

    def test_hybrid_score_is_bounded(self):
        profile = UserProfile(topics=frozenset({"маркетинг"}))
        score = score_hybrid(profile, self.catalog[0], self.index)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_hybrid_ranking_prefers_matching_topic(self):
        profile = UserProfile(topics=frozenset({"маркетинг"}), current_goal="продвижение")
        ranked = recommend(profile, self.catalog, strategy="hybrid", tfidf_index=self.index)
        self.assertIn(ranked[0].item.item_id, {"m1", "m3"})

    def test_hybrid_requires_valid_strategy(self):
        with self.assertRaises(ValueError):
            recommend(UserProfile(), self.catalog, strategy="unknown")

    def test_content_cf_hybrid_falls_back_without_cf_history(self):
        cf = ItemItemIndex.fit([], self.catalog)
        profile = UserProfile(topics=frozenset({"маркетинг"}))
        ranked = recommend(
            profile, self.catalog, strategy="content_cf_hybrid",
            tfidf_index=self.index, collaborative_index=cf,
        )
        self.assertEqual(ranked[0].item.item_id, "m1")


if __name__ == "__main__":
    unittest.main()
