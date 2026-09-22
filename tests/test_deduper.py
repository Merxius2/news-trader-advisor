import unittest

from src.ingest.deduper import content_hash, filter_new, normalize_url
from src.storage.models import NewArticle


class DeduperTests(unittest.TestCase):
    def test_normalize_url_strips_utm(self) -> None:
        raw = "https://example.com/a?utm_source=x&id=1"
        clean = normalize_url(raw)
        self.assertNotIn("utm_source", clean)
        self.assertIn("id=1", clean)

    def test_filter_new(self) -> None:
        article = NewArticle(
            url="https://example.com/b",
            title="Bitcoin rises",
            summary="",
            source="CoinDesk",
            published_at=None,
            content_hash=content_hash("Bitcoin rises", None, "CoinDesk"),
        )
        out = filter_new([article], set(), set())
        self.assertEqual(len(out), 1)
        out2 = filter_new([article], {article.url}, set())
        self.assertEqual(len(out2), 0)


if __name__ == "__main__":
    unittest.main()
