import unittest
from datetime import datetime,timedelta,timezone
from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile,group_events_by_user
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem,UserProfile
def event(user,item,event_type="rating",rating=None,completed=None,days=0,at=None,item_type="article"):
    return UserInteraction(user,item,item_type,event_type,rating,completed,at or datetime(2026,1,1)+timedelta(days=days))
class ProfileTests(unittest.TestCase):
    def test_profile_uses_positive_history_and_keeps_onboarding(self):
        catalog=[CatalogItem("a","article","A",topics=frozenset({"marketing"})),CatalogItem("b","article","B",topics=frozenset({"finance"}))]
        profile=build_user_profile([event("private-user","a",rating=5),event("private-user","b",rating=1)],catalog,onboarding=UserProfile(industries=frozenset({"retail"})))
        self.assertIn("marketing",profile.topics); self.assertNotIn("finance",profile.topics); self.assertIn("retail",profile.industries)
        self.assertEqual(profile.seen_item_keys,frozenset({("article","a"),("article","b")}))
        self.assertEqual(profile.positive_item_keys,frozenset({("article","a")}))
    def test_completed_lesson_is_positive(self):
        item=CatalogItem("lesson-1","lesson","Lesson",tags=frozenset({"basics"}))
        profile=build_user_profile([event("u","lesson-1","lesson_progress",completed=True,item_type="lesson")],[item])
        self.assertIn("basics",profile.tags); self.assertIn(("lesson","lesson-1"),profile.positive_item_keys)
    def test_same_id_different_type_maps_correctly(self):
        catalog=[CatalogItem("x","article","Article",topics=frozenset({"writing"})),CatalogItem("x","course","Course",topics=frozenset({"management"}))]
        profile=build_user_profile([event("u","x",rating=5,item_type="course")],catalog)
        self.assertEqual(profile.topics,frozenset({"management"}))
    def test_temporal_holdout_keeps_positive_event_types(self):
        splits=temporal_holdout([event("u","old",rating=5,days=1),event("u","new",event_type="lesson_progress",completed=True,days=2,item_type="lesson")])
        self.assertEqual(len(splits),1)
        self.assertEqual(splits[0].test_relevant_item_keys,frozenset({("lesson","new")}))
        self.assertEqual(splits[0].test_positive_events[0].event_type,"lesson_progress")
        self.assertFalse(hasattr(splits[0],"user_id"))
    def test_mixed_naive_and_aware_timestamps_sort_safely(self):
        rows=[event("u","a",rating=5,at=datetime(2026,1,1)),event("u","b",rating=5,at=datetime(2026,1,2,tzinfo=timezone.utc))]
        self.assertEqual(len(temporal_holdout(rows)),1); self.assertEqual(len(group_events_by_user(rows)["u"]),2)
if __name__=="__main__":unittest.main()
