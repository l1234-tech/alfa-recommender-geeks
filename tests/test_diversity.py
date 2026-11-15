import unittest

from recommender.algorithms.diversity import item_similarity, mmr_rerank
from recommender.models import CatalogItem


class DiversityTests(unittest.TestCase):
    def test_identical_metadata_is_more_similar(self):
        first = CatalogItem("a", "article", "Маркетинг для бизнеса",
                            topics=frozenset({"маркетинг", "продажи"}))
        similar = CatalogItem("b", "article", "Маркетинг для бизнеса",
                              topics=frozenset({"маркетинг", "продажи"}))
        different = CatalogItem("c", "course", "Финансовый учет",
                                topics=frozenset({"финансы", "бюджет"}))
        self.assertGreater(item_similarity(first, similar), item_similarity(first, different))

    def test_mmr_reduces_redundant_top_k(self):
        first = CatalogItem("a", "article", "Маркетинг и продажи",
                            topics=frozenset({"маркетинг", "продажи"}))
        near_duplicate = CatalogItem("b", "article", "Продвижение и маркетинг",
                                     topics=frozenset({"маркетинг", "продажи"}))
        diverse = CatalogItem("c", "course", "Финансовое планирование",
                              topics=frozenset({"финансы", "бюджет"}))
        candidates = [first, near_duplicate, diverse]
        scores = {"a": 0.95, "b": 0.94, "c": 0.75}
        relevance = lambda item: scores[item.item_id]
        plain = sorted(candidates, key=lambda item: -relevance(item))[:2]
        diversified = mmr_rerank(candidates, relevance, limit=2, diversity_weight=0.5)
        self.assertEqual([item.item_id for item in plain], ["a", "b"])
        self.assertEqual([item.item_id for item in diversified], ["a", "c"])

    def test_zero_diversity_weight_preserves_relevance_order(self):
        items = [CatalogItem("b", "article", "B"), CatalogItem("a", "article", "A")]
        result = mmr_rerank(items, lambda item: 1.0 if item.item_id == "a" else 0.5,
                            limit=2, diversity_weight=0.0)
        self.assertEqual([item.item_id for item in result], ["a", "b"])

    def test_invalid_weight(self):
        with self.assertRaises(ValueError):
            mmr_rerank([], lambda item: 0.0, limit=2, diversity_weight=1.1)


if __name__ == "__main__":
    unittest.main()
