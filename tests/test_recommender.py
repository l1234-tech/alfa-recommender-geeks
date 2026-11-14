import unittest
from recommender.data_processing.catalog import normalize_item
from recommender.models import CatalogItem,UserProfile
from recommender.ranking import recommend
class RecommenderTests(unittest.TestCase):
 def test_normalize_item(self):
  item=normalize_item({"item_id":"a1","item_type":"article","title":"Marketing basics","topics":["marketing","sales"],"tags":"beginner"})
  self.assertEqual(item.item_id,"a1"); self.assertEqual(item.topics,frozenset({"marketing","sales"})); self.assertEqual(item.tags,frozenset({"beginner"}))
 def test_metadata_ranking(self):
  p=UserProfile(topics=frozenset({"marketing"}),industries=frozenset({"retail"}))
  a=CatalogItem("1","article","Marketing",topics=frozenset({"marketing"}),industries=frozenset({"retail"}))
  b=CatalogItem("2","article","Accounting")
  result=recommend(p,[b,a]); self.assertEqual(result[0].item.item_id,"1"); self.assertGreater(result[0].score,result[1].score)
 def test_same_id_other_type_not_filtered(self):
  p=UserProfile(seen_item_keys=frozenset({("article","same")}))
  result=recommend(p,[CatalogItem("same","article","Seen"),CatalogItem("same","course","Different")])
  self.assertEqual([(r.item.item_type,r.item.item_id) for r in result],[("course","same")])
 def test_filters(self):
  p=UserProfile(seen_item_keys=frozenset({("article","seen")}),completed_item_keys=frozenset({("course","done")}))
  catalog=[CatalogItem("seen","article","Seen"),CatalogItem("done","course","Done"),CatalogItem("hidden","article","Hidden",is_available=False),CatalogItem("new","article","New")]
  self.assertEqual([r.item.item_id for r in recommend(p,catalog)],["new"])
 def test_limit(self):
  result=recommend(UserProfile(),[CatalogItem("b","article","B"),CatalogItem("a","article","A")],limit=1)
  self.assertEqual([r.item.item_id for r in result],["a"])
if __name__=="__main__":unittest.main()
