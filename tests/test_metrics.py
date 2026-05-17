import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_metrics import TrajectoryError, compute_metrics, format_metrics
from agent_metrics.cli import main
from agent_metrics.metrics import _int_or_none


ROOT = Path(__file__).resolve().parents[1]


class MessageMetricsTest(unittest.TestCase):
    def test_counts_required_roles(self) -> None:
        document = json.loads((ROOT / "data/samples/simple.traj.json").read_text(encoding="utf-8"))
        metrics = compute_metrics(document, "simple")

        self.assertEqual(metrics.system_messages, 1)
        self.assertEqual(metrics.user_messages, 1)
        self.assertEqual(metrics.assistant_messages, 2)
        self.assertEqual(metrics.tool_messages, 1)
        self.assertEqual(metrics.total_messages, 5)
        self.assertEqual(metrics.api_calls, 1)
        self.assertEqual(metrics.cost, 0.01)

    def test_surfaces_exit_role_as_other(self) -> None:
        document = json.loads((ROOT / "data/samples/with-exit.traj.json").read_text(encoding="utf-8"))
        metrics = compute_metrics(document, "exit")

        self.assertEqual(metrics.other_messages, 1)
        self.assertEqual(metrics.other_roles, {"exit": 1})
        self.assertIn("Exit messages:", format_metrics(metrics))

    def test_normalizes_responses_api_entries(self) -> None:
        metrics = compute_metrics(
            {
                "messages": [
                    {"role": "system"},
                    {"object": "response", "output": [{"type": "reasoning"}]},
                    {"type": "function_call_output", "output": "ok"},
                ]
            }
        )

        self.assertEqual(metrics.system_messages, 1)
        self.assertEqual(metrics.assistant_messages, 1)
        self.assertEqual(metrics.tool_messages, 1)
        self.assertEqual(metrics.other_messages, 0)

    def test_accepts_raw_message_list(self) -> None:
        metrics = compute_metrics([{"role": "system"}, {"role": "user"}])

        self.assertEqual(metrics.total_messages, 2)
        self.assertEqual(metrics.system_messages, 1)
        self.assertEqual(metrics.user_messages, 1)

    def test_rejects_missing_messages(self) -> None:
        with self.assertRaises(TrajectoryError):
            compute_metrics({"not_messages": []})

    def test_cli_pretty_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_metrics",
                str(ROOT / "data/samples/with-exit.traj.json"),
            ],
            check=True,
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertIn("System messages:", completed.stdout)
        self.assertIn("Exit messages:", completed.stdout)
        self.assertIn("Total messages:", completed.stdout)

    def test_csv_empty_input_no_crash(self) -> None:
        """--csv with an empty directory should return 0 without crashing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(["--csv", tmpdir])
        self.assertEqual(result, 0)

    def test_int_or_none_float_integer(self) -> None:
        """_int_or_none should coerce whole-number floats to int."""
        self.assertEqual(_int_or_none(32.0), 32)
        self.assertEqual(_int_or_none(0.0), 0)
        self.assertIsNone(_int_or_none(32.5))

    def test_responses_api_output_list_only_not_assistant(self) -> None:
        """A message with only output as a list but no object=='response' should NOT become assistant."""
        with self.assertRaises(TrajectoryError):
            compute_metrics(
                {
                    "messages": [
                        {"output": [{"type": "text", "text": "hello"}]},
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
