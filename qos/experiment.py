from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from .models import BackendProfile
from .pipeline import QuantumPipelineSimulator
from .scheduler import DefaultScheduler, QosScheduler
from .workloads import generate_workloads, group_by_type


def _build_backends(config: Dict) -> List[BackendProfile]:
    return [BackendProfile(**item) for item in config["platform"]["backends"]]


def _avg_summary(summaries: List[Dict[str, float]]) -> Dict[str, float]:
    if not summaries:
        return {}
    keys = summaries[0].keys()
    return {k: sum(s[k] for s in summaries) / len(summaries) for k in keys}


def run_experiment(config: Dict) -> Dict:
    jobs = generate_workloads(config, seed=config["seed"])
    by_type = group_by_type(jobs)
    backends = _build_backends(config)
    simulator = QuantumPipelineSimulator(
        backends=backends,
        max_retries=config["platform"]["max_retries"],
        reuse_factor=config["policy"]["compile_reuse_factor"],
    )

    rounds = config["ab_test"]["rounds_per_slot"]
    time_slots = config["ab_test"]["time_slots"]
    strategies = {
        "default": DefaultScheduler(),
        "qos": QosScheduler(),
    }
    strategy_summaries: Dict[str, List[Dict[str, float]]] = {k: [] for k in strategies}

    for slot in time_slots:
        for r in range(rounds):
            for strategy_name, scheduler in strategies.items():
                _, summary = simulator.run(
                    jobs=jobs,
                    scheduler=scheduler,
                    policy=config["policy"],
                    seed=config["seed"] + slot * 100 + r * 10 + (1 if strategy_name == "qos" else 0),
                    hour_slot=slot,
                )
                strategy_summaries[strategy_name].append(summary)

    averaged = {k: _avg_summary(v) for k, v in strategy_summaries.items()}
    default = averaged["default"]
    qos = averaged["qos"]
    comparison = {
        "throughput_gain_pct": _pct_change(default["throughput_jobs_per_s"], qos["throughput_jobs_per_s"]),
        "queue_wait_reduction_pct": _pct_change(default["avg_queue_wait_s"], qos["avg_queue_wait_s"], reverse=True),
        "success_rate_gain_pct": _pct_change(default["success_rate"], qos["success_rate"]),
        "makespan_reduction_pct": _pct_change(default["makespan_s"], qos["makespan_s"], reverse=True),
        "cost_reduction_pct": _pct_change(default["total_cost"], qos["total_cost"], reverse=True),
        "retry_reduction_pct": _pct_change(default["retry_count"], qos["retry_count"], reverse=True),
        "resource_utilization_gain_pct": _pct_change(default["resource_utilization"], qos["resource_utilization"]),
    }

    return {
        "platform": config["platform"]["name"],
        "toolchain": config.get("toolchain", {}),
        "target_backends": [asdict(b) for b in backends],
        "workload_mix": by_type,
        "metric_definitions": config["metric_definitions"],
        "ab_setup": config["ab_test"],
        "results": averaged,
        "comparison": comparison,
    }


def _pct_change(base: float, new: float, reverse: bool = False) -> float:
    if base == 0:
        return 0.0
    delta = (new - base) / base * 100.0
    return -delta if reverse else delta

