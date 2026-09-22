import unittest

from src.config_loader import Settings, SuggestionsConfig
from src.web.jobs import plan_cycle


class CyclePlanTests(unittest.TestCase):
    def _settings(self, threshold: int = 10, normal: int = 3, backlog: int = 5) -> Settings:
        return Settings(
            suggestions=SuggestionsConfig(
                max_articles_per_run=normal,
                backlog_skip_ingest_threshold=threshold,
                backlog_max_articles_per_run=backlog,
            )
        )

    def test_normal_mode_below_threshold(self) -> None:
        plan = plan_cycle(self._settings(), unanalyzed=9)
        self.assertFalse(plan.skip_ingest)
        self.assertEqual(plan.analysis_limit, 3)

    def test_backlog_mode_at_threshold(self) -> None:
        plan = plan_cycle(self._settings(), unanalyzed=10)
        self.assertTrue(plan.skip_ingest)
        self.assertEqual(plan.analysis_limit, 5)

    def test_backlog_mode_large_queue(self) -> None:
        plan = plan_cycle(self._settings(), unanalyzed=115)
        self.assertTrue(plan.backlog_mode)
        self.assertEqual(plan.analysis_limit, 5)


if __name__ == "__main__":
    unittest.main()
