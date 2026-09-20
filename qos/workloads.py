from __future__ import annotations

import random
from typing import Dict, Iterable, List

from .models import Job


def _build_job(rng: random.Random, workload_type: str, index: int, spec: Dict[str, int]) -> Job:
    qubits = rng.randint(spec["qubits_min"], spec["qubits_max"])
    depth = rng.randint(spec["depth_min"], spec["depth_max"])
    shots = rng.randint(spec["shots_min"], spec["shots_max"])
    deadline_s = float(spec["deadline_s"])
    return Job(
        job_id=f"{workload_type}-{index}",
        workload_type=workload_type,
        qubits=qubits,
        depth=depth,
        shots=shots,
        deadline_s=deadline_s,
    )


def generate_workloads(config: Dict, seed: int) -> List[Job]:
    rng = random.Random(seed)
    jobs: List[Job] = []
    for workload in config["workloads"]:
        wtype = workload["type"]
        count = workload["count"]
        spec = workload["spec"]
        jobs.extend(_build_job(rng, wtype, i, spec) for i in range(count))
    return jobs


def group_by_type(jobs: Iterable[Job]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for job in jobs:
        counts[job.workload_type] = counts.get(job.workload_type, 0) + 1
    return counts

