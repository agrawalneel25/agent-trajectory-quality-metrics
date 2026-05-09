# Methodology

## Task Mapping

Task 1 asks for a command-line tool that reads a mini-SWE-agent-v2 trajectory JSON file and prints message-role counts. The implementation is intentionally small: `agent_metrics.metrics.compute_metrics` extracts the `messages` array, normalizes known schema variants, and returns counts for `system`, `user`, `assistant`, `tool`, and any extra roles.

Task 2 asks for top-five model observations. `scripts/process_top5.py` lists the public SWE-bench S3 prefixes for the five models named in the prompt, downloads each `.traj.json`, computes CLI-compatible metrics, and writes aggregate reports. Raw trajectories are not committed because the full set is large and reproducible from S3.

Task 3 asks for a summary of “Towards a Science of AI Agent Reliability”. The summary is in `reports/paper_summary.md` and focuses on pages 1 through 21, excluding the appendix.

## Data Sources

- SWE-bench leaderboard: `https://www.swebench.com/`
- Public trajectory bucket: `https://swe-bench-submissions.s3.amazonaws.com/`
- Paper: `https://arxiv.org/abs/2602.16666`

The top-five model names and leaderboard cost/resolved fields are taken from the public SWE-bench leaderboard as of May 11, 2026. The row-level message metrics are recomputed from downloaded trajectory JSON files.

For GPT-5-2-Codex, the raw per-trajectory metadata does not exactly match the leaderboard aggregate fields. The reports therefore use leaderboard fields only for leaderboard claims such as resolved rate and cost per instance, and raw trajectory files only for message-role counts.

## Schema Handling

Most trajectories use chat-style messages with a `role` field. GPT-5-2-Codex trajectories include Responses API response objects and `function_call_output` objects. The parser maps response objects to `assistant` turns and function call outputs to `tool` turns. It keeps unrecognized roles, such as `exit`, separate instead of folding them into required categories.

That choice matters because message counts are only useful if they preserve operational structure. Hiding `exit` would make totals match a simpler schema, but it would also lose a termination signal that appears in every processed trajectory.

## Validation

The tests cover:

- required role counts
- real `exit` role handling
- Responses API object normalization
- raw message-list inputs
- malformed trajectory rejection
- CLI pretty output

The full aggregation processed 2,500 public trajectories, 500 for each top-five model.

## Limits

This submission measures trajectory shape, not code correctness. The resolved rates come from the leaderboard, while this tool counts messages in the raw execution traces. Message count is a proxy for interaction depth, review burden, and cost pressure, not a replacement for SWE-bench pass rate.
