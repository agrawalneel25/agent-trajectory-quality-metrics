from __future__ import annotations

import argparse
import csv
import json
import sys

from .metrics import TrajectoryError, compute_metrics, format_metrics, iter_input_files, load_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-metrics",
        description="Count message roles in mini-SWE-agent-v2 trajectory JSON files.",
    )
    parser.add_argument("inputs", nargs="+", help="trajectory file, directory, URL, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="emit JSON for one or more trajectories")
    parser.add_argument("--csv", action="store_true", help="emit CSV for one or more trajectories")
    args = parser.parse_args(argv)

    if args.csv and args.json:
        print("agent-metrics: --csv and --json are mutually exclusive", file=sys.stderr)
        return 2

    try:
        metrics = [compute_metrics(load_json(path), path) for path in iter_input_files(args.inputs)]
    except (OSError, json.JSONDecodeError, TrajectoryError) as error:
        print(f"agent-metrics: {error}", file=sys.stderr)
        return 2

    if args.csv:
        if not metrics:
            return 0
        writer = csv.DictWriter(sys.stdout, fieldnames=list(metrics[0].as_dict().keys()))
        writer.writeheader()
        for item in metrics:
            row = item.as_dict()
            row["other_roles"] = json.dumps(row["other_roles"], sort_keys=True)
            writer.writerow(row)
        return 0

    if args.json:
        print(json.dumps([item.as_dict() for item in metrics], indent=2, sort_keys=True))
        return 0

    for index, item in enumerate(metrics):
        if len(metrics) > 1:
            if index:
                print()
            print(item.source)
        print(format_metrics(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

