from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check prerequisites for real QOS execution.")
    parser.add_argument("--config", default="configs/real_toolchain.example.json")
    args = parser.parse_args()

    required_commands = ["qllvm", "mpirun"]
    missing = [command for command in required_commands if shutil.which(command) is None]
    for command in required_commands:
        status = "OK" if command not in missing else "MISSING"
        print(f"{status}: {command}")

    config_path = Path(args.config).resolve()
    if not config_path.is_file():
        print(f"MISSING: config file {config_path}")
        return 1
    config = json.loads(config_path.read_text(encoding="utf-8"))
    runtime = config.get("runtime", {})
    for key in ("qllvm", "mpiq", "fusion_lab"):
        if key not in runtime:
            print(f"MISSING: runtime.{key}")
    program_paths = {
        spec.get("program_path")
        for workload in config.get("workloads", [])
        for spec in [workload.get("spec", {})]
        if spec.get("program_path")
    }
    for program_path in program_paths:
        path = Path(program_path)
        if not path.is_absolute():
            path = config_path.parent.parent / path
        status = "OK" if path.is_file() else "MISSING"
        print(f"{status}: program {path.resolve()}")

    submit_url = runtime.get("fusion_lab", {}).get("submit_url", "")
    if not submit_url or "example" in submit_url:
        print("ACTION REQUIRED: set runtime.fusion_lab.submit_url to the real Fusion Lab API")
    if missing:
        print("ACTION REQUIRED: install the missing local commands before real execution")
    return 1 if missing or not submit_url or "example" in submit_url else 0


if __name__ == "__main__":
    raise SystemExit(main())
