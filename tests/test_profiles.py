import unittest
from datetime import datetime, timedelta, timezone

from recommender.data_processing.interactions import UserInteraction
from recommender.data_processing.profiles import build_user_profile, group_events_by_user
from recommender.evaluation.temporal import temporal_holdout
from recommender.models import CatalogItem, UserProfile


def event(user, item, event_type="rating", rating=None, completed=None, days=0, at=None):
    return UserInteraction(
        user_id=user, item_id=item, item_type="article", event_type=event_type,
        rating_value=rating, is_completed=completed,
        event_at=at or datetime(2026, 1, 1) + timedelta(days=days),
    )


class ProfileTests(unittest.TestCase):
    def test_profile_uses_positive_history_and_keeps_onboarding(self):
        catalog = [
            CatalogItem("a", "article", "A", topics=frozenset({"marketing"})),
            CatalogItem("b", "article", "B", topics=frozenset({"finance"})),
        ]
        profile = build_user_profile(
            [event("private-user", "a", rating=5), event("private-user", "b", rating=1)],
            catalog,
            onboarding=UserProfile(industries=frozenset({"retail"})),
        )
        self.assertIn("marketing", profile.topics)
        self.assertNotIn("finance", profile.topics)
        self.assertIn("retail", profile.industries)
        self.assertEqual(profile.seen_item_ids, frozenset({"a", "b"}))
        self.assertEqual(profile.positive_item_ids, frozenset({"a"}))

    def test_completed_lesson_is_positive(self):
        item = CatalogItem("lesson-1", "lesson", "Lesson", tags=frozenset({"basics"}))
        profile = build_user_profile(
            [UserInteraction("u", "lesson-1", "lesson", "lesson_progress", None, True, None)],
            [item],
        )
        self.assertIn("basics", profile.tags)
        self.assertIn("lesson-1", profile.positive_item_ids)

    def test_temporal_holdout_returns_no_user_id(self):
        splits = temporal_holdout([
            event("secret", "old", rating=5, days=1),
            event("secret", "new", rating=5, days=2),
        ])
        self.assertEqual(len(splits), 1)
        self.assertEqual(splits[0].test_relevant_item_ids, frozenset({"new"}))
        self.assertFalse(hasattr(splits[0], "user_id"))

    def test_mixed_naive_and_aware_timestamps_sort_safely(self):
        events = [
            event("u", "a", rating=5, at=datetime(2026, 1, 1)),
            event("u", "b", rating=5, at=datetime(2026, 1, 2, tzinfo=timezone.utc)),
        ]
        self.assertEqual(len(temporal_holdout(events)), 1)
        self.assertEqual(len(group_events_by_user(events)["u"]), 2)


if __name__ == "__main__":
    unittest.main()
