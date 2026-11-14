import unittest
from recommender.evaluation.cold_start import ColdStartCase,evaluate_cold_start_cases
from recommender.models import CatalogItem,UserProfile
class ColdStartTests(unittest.TestCase):
    def setUp(self):
        self.catalog=[
            CatalogItem("a","article","Маркетинг для магазина",topics=frozenset({"маркетинг"}),industries=frozenset({"retail"})),
            CatalogItem("b","article","Финансы бизнеса",topics=frozenset({"финансы"})),
            CatalogItem("c","course","Продажи",topics=frozenset({"продажи"}))]
    def test_onboarding_only_profiles_are_evaluated_without_history(self):
        cases=[ColdStartCase(UserProfile(topics=frozenset({"маркетинг"}),industries=frozenset({"retail"})),frozenset({("article","a")}))]
        result=evaluate_cold_start_cases(cases,self.catalog,k=1)
        self.assertEqual(result["baseline"]["profiles_evaluated"],1.0)
        self.assertEqual(result["baseline"]["recall@1"],1.0)
        self.assertGreater(result["hybrid"]["catalog_coverage"],0.0)
    def test_empty_cases_return_zero_metrics(self):
        result=evaluate_cold_start_cases([],self.catalog)
        self.assertEqual(result["baseline"]["profiles_evaluated"],0.0)
        self.assertEqual(result["baseline"]["catalog_coverage"],0.0)
if __name__=="__main__":unittest.main()
