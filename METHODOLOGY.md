# Methodology

## What this project measures

The task asks for metrics beyond pass/fail that can distinguish efficient agent behavior from costly trial-and-error. This repo treats message-role counts as a lightweight, always-available proxy for trajectory depth, and pairs them with cost and resolved-rate data from the public SWE-bench leaderboard.

## Why message roles

Mini-SWE-agent-v2 trajectories record every turn between the orchestrator and the model. The ratio of assistant turns to tool turns tells you whether the agent is thinking or acting — a model with many consecutive assistant messages without tool calls may be reasoning in place rather than making progress. Median and P90 message counts tell you how much the agent's behavior varies across tasks.

These are not the only metrics worth tracking. Rabanser et al. (arXiv 2602.16666) define four reliability dimensions: consistency, robustness, predictability, and safety. Message-role analysis sits closest to their consistency dimension — it measures whether the agent's interaction depth is stable across tasks and models, without requiring multi-run reruns.

## Metric definitions

| Metric | Definition | Why it matters |
|---|---|---|
| Total messages | All turns in the trajectory | Raw interaction depth |
| Assistant messages | Turns where the model generates text | Reasoning budget |
| Tool messages | Turns carrying tool output | Action count |
| Other messages | Non-standard roles (e.g., `exit`) | Schema signals |
| Median messages | 50th percentile across 500 trajectories | Typical cost proxy |
| P90 messages | 90th percentile | Tail cost exposure |
| Cost / instance | Leaderboard-reported average API cost | Operational cost |

## Comparison approach

Five models were selected from the public mini-SWE-agent-v2 SWE-bench leaderboard, chosen to represent different resolved-rate / cost tradeoffs. For each model, 500 trajectories were fetched from the public SWE-bench S3 bucket and processed with the CLI.

Resolved rate alone produces a tight ranking (72.8-76.8%). Adding median message count and cost per instance separates the models more usefully: two models that share a resolved rate can differ by 2x in median trajectory length and 5x in cost. The goal is to show that pass rate is an incomplete proxy for model value in a real agent deployment.

## What this methodology does not cover

- **Consistency**: requires running the same task multiple times. Single-trajectory data cannot measure run-to-run variation.
- **Robustness**: requires perturbation of prompts or environment. Not available from the existing trajectory files.
- **Predictability / calibration**: requires a model to report its own confidence. Not present in mini-SWE-agent-v2 trajectories.
- **Safety**: requires task-specific failure-mode labeling.

These gaps follow directly from what the public trajectory format exposes. A more complete evaluation would need multi-run data or task annotations that are not publicly available.

## Reproducing results

```powershell
python scripts\process_top5.py --workers 24 --out-dir reports
```

This fetches live from S3, recomputes the aggregate CSV (`reports/top5_trajectory_metrics.csv`) and summary JSON (`reports/top5_summary.json`), and writes a generated table to `reports/top5_observations_generated.md`. The hand-written analysis in `reports/top5_observations.md` is not overwritten.
