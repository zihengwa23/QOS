from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .models import BackendProfile, Job


@dataclass(frozen=True)
class ExecutionResult:
    execute_s: float
    success: bool
    cost: float
    failure_prob: float


class FusionLabExecutor:
    def execute(
        self,
        job: Job,
        backend: BackendProfile,
        queue_pressure: float,
        hour_slot: int,
        rng: Random,
    ) -> ExecutionResult:
        execute_s = (job.depth * job.shots) / backend.exec_rate
        execute_s *= rng.uniform(0.95, 1.1)

        failure_prob = backend.failure_rate + backend.congestion_sensitivity * queue_pressure
        if _in_calibration_window(hour_slot, backend):
            failure_prob += 0.08
        failure_prob = min(0.95, max(0.0, failure_prob))
        success = rng.random() >= failure_prob

        cost = execute_s * backend.cost_per_second
        return ExecutionResult(
            execute_s=execute_s,
            success=success,
            cost=cost,
            failure_prob=failure_prob,
        )


def _in_calibration_window(hour: int, backend: BackendProfile) -> bool:
    for window in backend.calibration_windows:
        if int(window["start_hour"]) <= hour < int(window["end_hour"]):
            return True
    return False