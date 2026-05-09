import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportArtifactsTest(unittest.TestCase):
    def test_top_five_summary_has_expected_scope(self) -> None:
        summary = json.loads((ROOT / "reports/top5_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(len(summary["models"]), 5)
        self.assertEqual(sum(model["trajectories"] for model in summary["models"]), 2500)
        self.assertTrue(all(model["exit_trajectories"] == 500 for model in summary["models"]))

    def test_required_reports_exist(self) -> None:
        self.assertIn("Top-Five", (ROOT / "reports/top5_observations.md").read_text(encoding="utf-8"))
        self.assertIn("Towards a Science", (ROOT / "reports/paper_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

