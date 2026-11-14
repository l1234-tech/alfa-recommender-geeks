import unittest

from recommender.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k


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


if __name__ == "__main__":
    unittest.main()
