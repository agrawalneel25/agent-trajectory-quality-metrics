from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_metrics import MessageMetrics, compute_metrics


S3_BUCKET = "swe-bench-submissions"
SWE_BENCH_HOME = "https://www.swebench.com/"

TOP5 = [
    {
        "model": "Claude 4.5 Opus high reasoning",
        "folder": "20260217_mini-v2.0.0_claude-4-5-opus-high",
        "resolved_pct": 76.8,
        "leaderboard_instance_calls": 32.896,
        "leaderboard_instance_cost": 0.753907997,
    },
    {
        "model": "Gemini 3 Flash high reasoning",
        "folder": "20260217_mini-v2.0.0_gemini-3-flash-high",
        "resolved_pct": 75.8,
        "leaderboard_instance_calls": 56.126,
        "leaderboard_instance_cost": 0.3559641308,
    },
    {
        "model": "MiniMax M2.5 high reasoning",
        "folder": "20260217_mini-v2.0.0_minimax-2-5-high",
        "resolved_pct": 75.8,
        "leaderboard_instance_calls": 60.45,
        "leaderboard_instance_cost": 0.073289987844,
    },
    {
        "model": "Claude Opus 4.6",
        "folder": "20260217_mini-v2.0.0_claude-4-6-opus",
        "resolved_pct": 75.6,
        "leaderboard_instance_calls": 28.932,
        "leaderboard_instance_cost": 0.5515226445,
    },
    {
        "model": "GPT-5-2 Codex",
        "folder": "20260219_mini-v2.0.0_gpt-5-2-codex",
        "resolved_pct": 72.8,
        "leaderboard_instance_calls": 28.072,
        "leaderboard_instance_cost": 0.4494238987,
    },
]


@dataclass(frozen=True)
class ModelResult:
    model: str
    folder: str
    resolved_pct: float
    leaderboard_instance_calls: float
    leaderboard_instance_cost: float
    trajectories: int
    mean_total_messages: float
    median_total_messages: float
    p90_total_messages: float
    max_total_messages: int
    mean_assistant_messages: float
    mean_tool_messages: float
    mean_other_messages: float
    exit_trajectories: int
    mean_api_calls: float | None
    mean_cost: float | None

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Process top-five mini-SWE-agent-v2 trajectories from SWE-bench S3.")
    parser.add_argument("--limit", type=int, default=0, help="limit trajectories per model for a fast smoke run")
    parser.add_argument("--workers", type=int, default=16, help="parallel downloads per model")
    parser.add_argument("--out-dir", default=str(ROOT / "reports"), help="directory for CSV and JSON outputs")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[ModelResult] = []
    row_path = out_dir / "top5_trajectory_metrics.csv"
    with row_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "model",
                "folder",
                "instance_id",
                "source",
                "system_messages",
                "user_messages",
                "assistant_messages",
                "tool_messages",
                "other_messages",
                "other_roles",
                "total_messages",
                "api_calls",
                "cost",
            ],
        )
        writer.writeheader()
        for model in TOP5:
            metrics = process_model(model, limit=args.limit, workers=args.workers)
            for item in metrics:
                row = item.as_dict()
                row["model"] = model["model"]
                row["folder"] = model["folder"]
                row["other_roles"] = json.dumps(row["other_roles"], sort_keys=True)
                row.pop("resolved", None)
                writer.writerow(row)
            results.append(summarize_model(model, metrics))
            print(f"{model['model']}: {len(metrics)} trajectories")

    summary = {
        "source": SWE_BENCH_HOME,
        "s3_bucket": S3_BUCKET,
        "note": "Aggregate message-role metrics computed from public SWE-bench trajectory JSON.",
        "models": [item.as_dict() for item in results],
    }
    (out_dir / "top5_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown_summary(out_dir / "top5_observations.md", results)
    return 0


def process_model(model: dict[str, object], limit: int, workers: int) -> list[MessageMetrics]:
    prefix = f"bash-only/{model['folder']}/trajs/"
    keys = [key for key in list_s3_keys(prefix) if key.endswith(".traj.json")]
    if limit:
        keys = keys[:limit]
    urls = [f"https://{S3_BUCKET}.s3.amazonaws.com/{quote(key)}" for key in keys]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        metrics = list(executor.map(fetch_metric, urls))
    return sorted(metrics, key=lambda item: item.instance_id or item.source)


def fetch_metric(url: str) -> MessageMetrics:
    with urlopen(url, timeout=90) as response:
        document = json.load(response)
    return compute_metrics(document, url)


def list_s3_keys(prefix: str) -> list[str]:
    token: str | None = None
    keys: list[str] = []
    while True:
        query = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            query["continuation-token"] = token
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/?{urlencode(query)}"
        with urlopen(url, timeout=60) as response:
            tree = ET.parse(response)
        root = tree.getroot()
        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        keys.extend(node.text or "" for node in root.findall("s3:Contents/s3:Key", ns))
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=ns)
        if truncated.lower() != "true":
            return keys
        token = root.findtext("s3:NextContinuationToken", default=None, namespaces=ns)
        if not token:
            return keys


def summarize_model(model: dict[str, object], metrics: list[MessageMetrics]) -> ModelResult:
    totals = [item.total_messages for item in metrics]
    assistant = [item.assistant_messages for item in metrics]
    tool = [item.tool_messages for item in metrics]
    other = [item.other_messages for item in metrics]
    api_calls = [item.api_calls for item in metrics if item.api_calls is not None]
    costs = [item.cost for item in metrics if item.cost is not None]

    return ModelResult(
        model=str(model["model"]),
        folder=str(model["folder"]),
        resolved_pct=float(model["resolved_pct"]),
        leaderboard_instance_calls=float(model["leaderboard_instance_calls"]),
        leaderboard_instance_cost=float(model["leaderboard_instance_cost"]),
        trajectories=len(metrics),
        mean_total_messages=round(statistics.fmean(totals), 3),
        median_total_messages=round(statistics.median(totals), 3),
        p90_total_messages=round(_percentile(totals, 90), 3),
        max_total_messages=max(totals),
        mean_assistant_messages=round(statistics.fmean(assistant), 3),
        mean_tool_messages=round(statistics.fmean(tool), 3),
        mean_other_messages=round(statistics.fmean(other), 3),
        exit_trajectories=sum(1 for item in metrics if item.other_roles.get("exit", 0) > 0),
        mean_api_calls=round(statistics.fmean(api_calls), 3) if api_calls else None,
        mean_cost=round(statistics.fmean(costs), 6) if costs else None,
    )


def _percentile(values: list[int], percentile: int) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * percentile / 100
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def write_markdown_summary(path: Path, results: list[ModelResult]) -> None:
    lines = [
        "# Top-Five mini-SWE-agent-v2 Trajectory Observations",
        "",
        "Processed the public SWE-bench trajectory JSON files for the top five mini-SWE-agent-v2 models listed in the task prompt. Raw trajectories are not committed because they are large; `scripts/process_top5.py` regenerates the aggregate CSV and JSON files from S3.",
        "",
        "| Model | Resolved | Trajectories | Median messages | P90 messages | Mean assistant | Mean tool | Cost / instance |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in results:
        lines.append(
            f"| {item.model} | {item.resolved_pct:.1f}% | {item.trajectories} | "
            f"{item.median_total_messages:.1f} | {item.p90_total_messages:.1f} | "
            f"{item.mean_assistant_messages:.1f} | {item.mean_tool_messages:.1f} | "
            f"${item.leaderboard_instance_cost:.3f} |"
        )
    lines.extend(
        [
            "",
            "The top-five pass rates are tightly grouped, from 72.8% to 76.8%, but the interaction budgets differ much more. MiniMax M2.5 and Gemini 3 Flash use the longest trajectories by the message-count proxy, while Claude Opus 4.6 reaches a similar resolved rate with shorter conversations. This makes message depth a useful companion metric to pass rate when comparing operational cost and review burden.",
            "",
            "Each processed trajectory includes the expected system and user setup plus assistant/tool exchanges. Real mini-SWE-agent-v2 files also contain an `exit` role carrying the final patch or termination payload, so the CLI surfaces non-standard roles instead of hiding them inside assistant/tool counts. That choice keeps the required role counts faithful while preserving schema drift signals.",
            "",
            "The cost column also changes the ranking. MiniMax M2.5 has roughly the same resolved rate as Gemini 3 Flash and Claude Opus 4.6, but the leaderboard-reported cost per instance is much lower. Claude 4.5 Opus high reasoning leads on pass rate, yet it is the most expensive among these five. A model choice based only on resolved percentage would miss that tradeoff.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
