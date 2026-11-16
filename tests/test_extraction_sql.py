from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExtractionSqlTests(unittest.TestCase):
    def test_catalog_uses_timestamp_publication_checks(self):
        sql = (ROOT / "recommender/data_processing/catalog.sql").read_text(encoding="utf-8")
        self.assertIn('"Published" IS NOT NULL', sql)
        self.assertNotIn('COALESCE(cs."Published", false)', sql)
        self.assertNotIn('COALESCE(c."Published", false)', sql)

    def test_catalog_does_not_select_private_content(self):
        sql = (ROOT / "recommender/data_processing/catalog.sql").read_text(encoding="utf-8")
        self.assertNotIn('a."Content"', sql)
        self.assertNotIn('l."Content"', sql)

    def test_anonymous_ratings_are_not_user_events(self):
        sql = (ROOT / "recommender/data_processing/interactions.sql").read_text(encoding="utf-8")
        self.assertIn('ur."UserId" IS NOT NULL', sql)
        self.assertIn('(culb."Completed" IS NOT NULL)', sql)

    def test_user_rating_entity_mapping_is_explicit(self):
        sql = (ROOT / "recommender/data_processing/interactions.sql").read_text(encoding="utf-8")
        self.assertIn("THEN 'lesson'", sql)
        self.assertIn("THEN 'calculator'", sql)


if __name__ == "__main__":
    unittest.main()
