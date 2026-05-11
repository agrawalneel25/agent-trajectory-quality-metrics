# Agent Trajectory Quality Metrics

This repository contains a small Python CLI for counting message roles in mini-SWE-agent-v2 trajectory JSON files from SWE-bench. It also includes a batch processor for the top five models named in the JetBrains task prompt and the two required writeups.

## Deliverables

- CLI tool: `src/agent_metrics/`
- Tests: `tests/test_metrics.py`
- Top-five report: `reports/top5_observations.md`
- Paper summary: `reports/paper_summary.md`
- Aggregate summary: `reports/top5_summary.json`

## Quick Start

```powershell
python -m pip install -e .
python -m unittest discover -s tests
python -m agent_metrics data\samples\with-exit.traj.json
```

Expected sample output:

```text
System messages:       1
User messages:         1
Assistant messages:    1
Tool messages:         1
Exit messages:         1
======================
Total messages:        5
```

The task only requires `system`, `user`, `assistant`, and `tool`. Real mini-SWE-agent-v2 trajectories also include `exit` messages and, for GPT-5-2-Codex, Responses API objects. The CLI counts the required roles and surfaces extra roles separately.

## CLI Usage

Single file:

```powershell
python -m agent_metrics path\to\trajectory.traj.json
```

Directory of JSON files:

```powershell
python -m agent_metrics path\to\trajectories
```

Machine-readable output:

```powershell
python -m agent_metrics data\samples --json
python -m agent_metrics data\samples --csv
```

Input can be a local file, a directory, `-` for stdin, or an `https://` URL.

## Reproduce the Top-Five Analysis

The committed reports were generated from public SWE-bench S3 trajectory objects on May 11, 2026.

```powershell
python scripts\process_top5.py --workers 24 --out-dir reports
```

For a fast network smoke run:

```powershell
python scripts\process_top5.py --limit 2 --workers 8 --out-dir reports\smoke
```

The full run processes 2,500 trajectories and writes a compact JSON summary plus a per-trajectory CSV. The report in `reports/top5_observations.md` contains the submitted analysis.

## Continuous Integration

GitHub Actions runs:

```bash
python -m pip install -e .
python -m unittest discover -s tests
agent-metrics data/samples/with-exit.traj.json
```
