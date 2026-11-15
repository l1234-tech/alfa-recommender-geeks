import unittest
from recommender.evaluation.cold_start import ColdStartCase, build_expert_cold_start_benchmark, evaluate_cold_start_cases
from recommender.models import CatalogItem, UserProfile

class ColdStartTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            CatalogItem("a","article","Маркетинг для магазина",topics=frozenset({"маркетинг"}),industries=frozenset({"retail"})),
            CatalogItem("b","article","Финансы бизнеса",topics=frozenset({"финансы"})),
            CatalogItem("c","course","Продажи",topics=frozenset({"продажи"})),
        ]

    def test_onboarding_only_profile_and_metrics(self):
        cases=[ColdStartCase(UserProfile(topics=frozenset({"маркетинг"}),industries=frozenset({"retail"})),frozenset({("article","a")}))]
        result=evaluate_cold_start_cases(cases,self.catalog,k=1)
        self.assertEqual(result["baseline"]["profiles_evaluated"],1.0)
        self.assertEqual(result["baseline"]["recall@1"],1.0)
        self.assertEqual(result["baseline"]["hit_rate@1"],1.0)
        self.assertEqual(result["baseline"]["mrr@1"],1.0)
        self.assertEqual(result["hybrid"]["explanation_coverage"],1.0)

    def test_expert_benchmark_contains_varied_history_free_profiles(self):
        catalog,cases=build_expert_cold_start_benchmark()
        self.assertEqual(len(cases),5)
        self.assertTrue(all(not c.profile.positive_item_keys and not c.profile.seen_item_keys for c in cases))
        result=evaluate_cold_start_cases(cases,catalog,k=3)
        self.assertEqual(result["baseline"]["profiles_evaluated"],5.0)
        self.assertIn("hit_rate@3",result["hybrid"])
        self.assertIn("mrr@3",result["hybrid"])
        self.assertGreater(result["hybrid"]["explanation_coverage"],0.0)

    def test_interaction_history_is_rejected(self):
        case=ColdStartCase(UserProfile(positive_item_keys=frozenset({("article","a")})),frozenset({("article","a")}))
        with self.assertRaises(ValueError):
            evaluate_cold_start_cases([case],self.catalog,k=1)

    def test_empty_cases_and_invalid_k(self):
        result=evaluate_cold_start_cases([],self.catalog)
        self.assertEqual(result["baseline"]["profiles_evaluated"],0.0)
        self.assertEqual(result["baseline"]["hit_rate@5"],0.0)
        with self.assertRaises(ValueError):
            evaluate_cold_start_cases([],self.catalog,k=0)

if __name__=="__main__":
    unittest.main()
