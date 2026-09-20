from __future__ import annotations

import random
from typing import Dict, List, Tuple

from .models import BackendProfile, Job, JobResult


def _in_calibration_window(hour: int, backend: BackendProfile) -> bool:
    for window in backend.calibration_windows:
        if int(window["start_hour"]) <= hour < int(window["end_hour"]):
            return True
    return False


class QuantumPipelineSimulator:
    def __init__(self, backends: List[BackendProfile], max_retries: int, reuse_factor: float) -> None:
        self.backends = backends
        self.max_retries = max_retries
        self.reuse_factor = reuse_factor

    def run(
        self,
        jobs: List[Job],
        scheduler,
        policy: Dict,
        seed: int,
        hour_slot: int,
    ) -> Tuple[List[JobResult], Dict[str, float]]:
        rng = random.Random(seed)
        state: Dict[str, float] = {"time_cursor": 0.0}
        for b in self.backends:
            state[f"{b.name}:available_at"] = 0.0

        compile_cache = set()
        results: List[JobResult] = []
        total_execution = 0.0
        total_compile = 0.0
        total_queue = 0.0
        total_return = 0.0
        success_count = 0
        retry_count = 0
        total_cost = 0.0

        for job in jobs:
            retries = 0
            final_result: JobResult | None = None
            while retries <= self.max_retries:
                backend = scheduler.choose_backend(job, self.backends, state, policy)
                available_at = state[f"{backend.name}:available_at"]
                queue_wait = max(0.0, available_at - state["time_cursor"])
                queue_noise = rng.uniform(0.0, backend.queue_delay_base_s)
                queue_wait += queue_noise

                compile_key = (job.qubits, round(job.depth, -1), backend.name)
                compile_s = backend.compile_factor * ((job.qubits * job.depth) ** 0.5)
                if compile_key in compile_cache:
                    compile_s *= self.reuse_factor
                compile_cache.add(compile_key)
                compile_s *= rng.uniform(0.95, 1.05)

                execute_s = (job.depth * job.shots) / backend.exec_rate
                execute_s *= rng.uniform(0.95, 1.1)
                return_s = rng.uniform(0.1, 0.5)
                total_s = queue_wait + compile_s + execute_s + return_s

                queue_pressure = queue_wait / max(backend.queue_capacity, 1)
                fail_prob = backend.failure_rate + backend.congestion_sensitivity * queue_pressure
                if _in_calibration_window(hour_slot, backend):
                    fail_prob += 0.08
                fail_prob = min(0.95, max(0.0, fail_prob))
                success = rng.random() >= fail_prob

                backend_finish = state["time_cursor"] + total_s
                state[f"{backend.name}:available_at"] = max(state[f"{backend.name}:available_at"], backend_finish)

                cost = (compile_s + execute_s) * backend.cost_per_second
                total_cost += cost

                final_result = JobResult(
                    job_id=job.job_id,
                    workload_type=job.workload_type,
                    backend=backend.name,
                    success=success,
                    retries=retries,
                    queue_wait_s=queue_wait,
                    compile_s=compile_s,
                    execute_s=execute_s,
                    return_s=return_s,
                    total_s=total_s,
                    cost=cost,
                )
                if success:
                    break
                retries += 1
                retry_count += 1

            assert final_result is not None
            success_count += 1 if final_result.success else 0
            total_queue += final_result.queue_wait_s
            total_compile += final_result.compile_s
            total_execution += final_result.execute_s
            total_return += final_result.return_s
            results.append(final_result)

        makespan = max(state[f"{b.name}:available_at"] for b in self.backends) if self.backends else 0.0
        summary = {
            "total_jobs": float(len(results)),
            "success_jobs": float(success_count),
            "success_rate": (success_count / len(results)) if results else 0.0,
            "avg_queue_wait_s": (total_queue / len(results)) if results else 0.0,
            "avg_compile_s": (total_compile / len(results)) if results else 0.0,
            "avg_execute_s": (total_execution / len(results)) if results else 0.0,
            "avg_return_s": (total_return / len(results)) if results else 0.0,
            "retry_count": float(retry_count),
            "total_cost": total_cost,
            "makespan_s": makespan,
            "throughput_jobs_per_s": (len(results) / makespan) if makespan > 0 else 0.0,
            "resource_utilization": (
                total_execution / (makespan * max(len(self.backends), 1))
                if makespan > 0
                else 0.0
            ),
        }
        return results, summary

