from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Job:
    job_id: str
    workload_type: str
    qubits: int
    depth: int
    shots: int
    deadline_s: float


@dataclass(frozen=True)
class BackendProfile:
    name: str
    queue_capacity: int
    queue_delay_base_s: float
    compile_factor: float
    exec_rate: float
    failure_rate: float
    cost_per_second: float
    congestion_sensitivity: float
    calibration_windows: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class JobResult:
    job_id: str
    workload_type: str
    backend: str
    success: bool
    retries: int
    queue_wait_s: float
    compile_s: float
    execute_s: float
    return_s: float
    total_s: float
    cost: float

