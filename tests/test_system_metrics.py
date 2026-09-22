import unittest

from src.web.system_metrics import get_host_metrics


class HostMetricsTests(unittest.TestCase):
    def test_returns_expected_keys(self) -> None:
        metrics = get_host_metrics(sample_cpu=False)
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_used_gb", metrics)
        self.assertIn("memory_total_gb", metrics)
        self.assertGreater(metrics["memory_total_gb"], 0)


if __name__ == "__main__":
    unittest.main()
