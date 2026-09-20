from __future__ import annotations

import argparse
import json
from pathlib import Path

from qos.analysis import build_optimization_checklist, render_markdown_report
from qos.config import load_config
from qos.experiment import run_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QOS A/B validation experiment.")
    parser.add_argument("--config", required=True, help="Path to experiment config JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    result = run_experiment(config)
    checklist = build_optimization_checklist(result)
    report_md = render_markdown_report(result, checklist)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "experiment_result.json"
    report_path = out_dir / "comparison_report.md"

    with result_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                **result,
                "optimization_checklist": checklist,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Generated: {result_path}")
    print(f"Generated: {report_path}")


if __name__ == "__main__":
    main()

