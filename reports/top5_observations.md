# Top-Five mini-SWE-agent-v2 Trajectory Observations

I processed the public SWE-bench trajectory JSON files for the five mini-SWE-agent-v2 models named in the task prompt: 2,500 trajectories total, 500 per model. The raw trajectories and row-level CSV are left out of the repository because they are generated data; `scripts/process_top5.py` regenerates them from S3.

| Model | Resolved | Trajectories | Median messages | P90 messages | Mean assistant | Mean tool | Cost / instance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude 4.5 Opus high reasoning | 76.8% | 500 | 64.0 | 125.0 | 32.9 | 37.5 | $0.754 |
| Gemini 3 Flash high reasoning | 75.8% | 500 | 110.0 | 166.2 | 56.1 | 55.1 | $0.356 |
| MiniMax M2.5 high reasoning | 75.8% | 500 | 106.0 | 212.0 | 60.4 | 59.4 | $0.073 |
| Claude Opus 4.6 | 75.6% | 500 | 50.0 | 117.1 | 28.9 | 29.9 | $0.552 |
| GPT-5-2 Codex | 72.8% | 500 | 66.0 | 122.0 | 35.0 | 35.8 | $0.449 |

The resolved rates are close, from 72.8% to 76.8%, but trajectory length separates the models much more clearly. Claude Opus 4.6 has the shortest median trajectory among this group while staying within 1.2 percentage points of the highest resolved rate. Gemini 3 Flash and MiniMax M2.5 solve a similar share of tasks but usually take longer interaction traces.

The `exit` role appears in every processed trajectory. I kept it separate from the required four categories because it is a termination payload rather than an assistant/tool turn. GPT-5-2-Codex also uses Responses API objects in the message array, so the parser normalizes response objects as assistant turns and function-call outputs as tool turns.

The cost column changes the practical ranking. Claude 4.5 Opus high reasoning leads on resolved rate but is the most expensive model here. MiniMax M2.5 has the same resolved rate as Gemini 3 Flash and nearly matches Claude Opus 4.6, while costing much less per instance. For agent evaluation, pass rate alone hides both interaction depth and cost pressure.
