import unittest

from recommender.evaluation.metrics import (
    aggregate_diversity_metrics,
    catalog_coverage,
    intra_list_diversity,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from recommender.models import CatalogItem


class RankingMetricsTests(unittest.TestCase):
    def test_perfect_ranking(self):
        ranked = ["a", "b", "c"]
        relevant = {"a", "b"}
        self.assertAlmostEqual(precision_at_k(ranked, relevant, 2), 1.0)
        self.assertAlmostEqual(recall_at_k(ranked, relevant, 2), 1.0)
        self.assertAlmostEqual(ndcg_at_k(ranked, relevant, 2), 1.0)

    def test_relevant_item_below_cutoff(self):
        self.assertEqual(precision_at_k(["x", "a"], {"a"}, 1), 0.0)
        self.assertEqual(recall_at_k(["x", "a"], {"a"}, 1), 0.0)
        self.assertEqual(ndcg_at_k(["x", "a"], {"a"}, 1), 0.0)

    def test_empty_relevance(self):
        self.assertEqual(recall_at_k(["a"], set(), 5), 0.0)
        self.assertEqual(ndcg_at_k(["a"], set(), 5), 0.0)

    def test_catalog_coverage_uses_unique_available_items(self):
        result = catalog_coverage([["a", "a", "missing"], ["b"]], {"a", "b", "c"})
        self.assertEqual(result["recommended_unique_items"], 2.0)
        self.assertAlmostEqual(result["catalog_coverage"], 2 / 3)

    def test_empty_catalog_coverage_is_zero(self):
        self.assertEqual(catalog_coverage([["a"]], set())["catalog_coverage"], 0.0)

    def test_intra_list_diversity(self):
        same_a = CatalogItem("a", "article", "Маркетинг", topics=frozenset({"маркетинг"}))
        same_b = CatalogItem("b", "article", "Маркетинг", topics=frozenset({"маркетинг"}))
        other = CatalogItem("c", "course", "Финансы", topics=frozenset({"финансы"}))
        self.assertEqual(intra_list_diversity([same_a]), 0.0)
        self.assertLess(intra_list_diversity([same_a, same_b]), intra_list_diversity([same_a, other]))

    def test_aggregate_diversity_metrics(self):
        a = CatalogItem("a", "article", "Маркетинг", topics=frozenset({"маркетинг"}))
        b = CatalogItem("b", "course", "Финансы", topics=frozenset({"финансы"}))
        result = aggregate_diversity_metrics(
            [[a.key, b.key], [a.key]],
            {a.key: a, b.key: b},
        )
        self.assertEqual(result["avg_unique_topics_per_list"], 1.0)
        self.assertEqual(result["avg_unique_types_per_list"], 1.5)
        self.assertGreater(result["intra_list_diversity"], 0.0)


if __name__ == "__main__":
    unittest.main()
