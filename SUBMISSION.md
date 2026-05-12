# Submission

## What I built

A Python CLI (`agent-metrics`) that counts message roles in mini-SWE-agent-v2 trajectory JSON files from SWE-bench, plus a batch script that fetched and processed 2,500 public trajectories (500 per model) for the top five models.

Two reports:
- `reports/top5_observations.md` — per-model message and cost analysis
- `reports/paper_summary.md` — summary of "Towards a Science of AI Agent Reliability" (Rabanser et al., arXiv 2602.16666)

## CLI

```powershell
python -m pip install -e .
python -m agent_metrics path\to\trajectory.traj.json
python -m agent_metrics path\to\trajectories --json
python -m agent_metrics path\to\trajectories --csv
```

Accepts a file, directory, `-` for stdin, or an `https://` URL. Counts `system`, `user`, `assistant`, and `tool` roles. Surfaces non-standard roles (like `exit` in mini-SWE-agent-v2) separately rather than silently folding them in.

## Top-five results

| Model | Resolved | Trajectories | Median messages | P90 messages | Mean assistant | Mean tool | Cost / instance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude 4.5 Opus high reasoning | 76.8% | 500 | 64.0 | 125.0 | 32.9 | 37.5 | $0.754 |
| Gemini 3 Flash high reasoning | 75.8% | 500 | 110.0 | 166.2 | 56.1 | 55.1 | $0.356 |
| MiniMax M2.5 high reasoning | 75.8% | 500 | 106.0 | 212.0 | 60.4 | 59.4 | $0.073 |
| Claude Opus 4.6 | 75.6% | 500 | 50.0 | 117.1 | 28.9 | 29.9 | $0.552 |
| GPT-5-2 Codex | 72.8% | 500 | 66.0 | 122.0 | 35.0 | 35.8 | $0.449 |

Pass rates are tight (72.8-76.8%), but trajectory length separates the models much more. Claude Opus 4.6 reaches a similar resolved rate to the top two models with roughly half the median message count of Gemini 3 Flash and MiniMax M2.5. MiniMax M2.5 has the same resolved rate as Gemini 3 Flash but costs about 5x less per instance.

To regenerate the aggregate CSV and JSON from S3 (requires a live network connection to the public SWE-bench bucket):

```powershell
python scripts\process_top5.py --workers 24 --out-dir reports
```

## Design choices

The CLI accepts both the `{"messages": [...]}` envelope format and raw message lists, because real SWE-bench trajectories use the envelope but the spec only requires a messages array. It also normalizes Responses API objects (used by GPT-5-2 Codex) as `assistant` turns rather than failing on an unexpected shape.

## Limits

The trajectory analysis counts messages and extracts cost metadata from `info.model_stats`. It does not measure consistency, robustness, or calibration — those require multi-run data that is not in the single-trajectory format. The paper summary covers why those dimensions matter; the implementation handles what the public trajectory data makes measurable.
