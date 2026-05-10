# Submission Message

GitHub repo:
https://github.com/agrawalneel25/agent-trajectory-quality-metrics

I implemented a Python CLI for counting message roles in mini-SWE-agent-v2 trajectory JSON files from SWE-bench. The tool reports system, user, assistant, tool, extra-role, and total message counts, with JSON/CSV modes for batch use.

I also processed the public SWE-bench trajectories for the five models named in the prompt:

- Claude 4.5 Opus high reasoning
- Gemini 3 Flash high reasoning
- MiniMax M2.5 high reasoning
- Claude Opus 4.6
- GPT-5-2 Codex

The batch run processed 2,500 trajectories from public S3, 500 per model. The repo includes aggregate CSV/JSON outputs and a one-page report with observations about message depth, cost, and schema differences. The parser handles both normal chat-style trajectories and GPT-5-2-Codex Responses API style entries.

I included the required paper summary for "Towards a Science of AI Agent Reliability" in `reports/paper_summary.md`.

Local verification:

```powershell
python -m pip install -e .
python -m unittest discover -s tests
python -m agent_metrics data\samples\with-exit.traj.json
python scripts\process_top5.py --workers 24 --out-dir reports
```

GitHub Actions is configured to install the package, run the tests, and execute the sample CLI command.
