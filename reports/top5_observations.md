# Top-Five mini-SWE-agent-v2 Trajectory Observations

Processed the public SWE-bench trajectory JSON files for the top five mini-SWE-agent-v2 models listed in the task prompt. Raw trajectories are not committed because they are large; `scripts/process_top5.py` regenerates the aggregate CSV and JSON files from S3.

| Model | Resolved | Trajectories | Median messages | P90 messages | Mean assistant | Mean tool | Cost / instance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude 4.5 Opus high reasoning | 76.8% | 500 | 64.0 | 125.0 | 32.9 | 37.5 | $0.754 |
| Gemini 3 Flash high reasoning | 75.8% | 500 | 110.0 | 166.2 | 56.1 | 55.1 | $0.356 |
| MiniMax M2.5 high reasoning | 75.8% | 500 | 106.0 | 212.0 | 60.4 | 59.4 | $0.073 |
| Claude Opus 4.6 | 75.6% | 500 | 50.0 | 117.1 | 28.9 | 29.9 | $0.552 |
| GPT-5-2 Codex | 72.8% | 500 | 66.0 | 122.0 | 35.0 | 35.8 | $0.449 |

The top-five pass rates are tightly grouped, from 72.8% to 76.8%, but the interaction budgets differ much more. MiniMax M2.5 and Gemini 3 Flash use the longest trajectories by the message-count proxy, while Claude Opus 4.6 reaches a similar resolved rate with shorter conversations. This makes message depth a useful companion metric to pass rate when comparing operational cost and review burden.

Each processed trajectory includes the expected system and user setup plus assistant/tool exchanges. Real mini-SWE-agent-v2 files also contain an `exit` role carrying the final patch or termination payload, so the CLI surfaces non-standard roles instead of hiding them inside assistant/tool counts. That choice keeps the required role counts faithful while preserving schema drift signals.

The cost column also changes the ranking. MiniMax M2.5 has roughly the same resolved rate as Gemini 3 Flash and Claude Opus 4.6, but the leaderboard-reported cost per instance is much lower. Claude 4.5 Opus high reasoning leads on pass rate, yet it is the most expensive among these five. A model choice based only on resolved percentage would miss that tradeoff.
