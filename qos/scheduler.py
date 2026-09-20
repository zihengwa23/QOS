from __future__ import annotations

from typing import Dict, List

from .models import BackendProfile, Job


class DefaultScheduler:
    def choose_backend(
        self,
        job: Job,
        backends: List[BackendProfile],
        state: Dict[str, float],
        policy: Dict,
    ) -> BackendProfile:
        del job, policy
        return min(backends, key=lambda b: state[f"{b.name}:available_at"])


class QosScheduler:
    def choose_backend(
        self,
        job: Job,
        backends: List[BackendProfile],
        state: Dict[str, float],
        policy: Dict,
    ) -> BackendProfile:
        latency_weight = policy["latency_weight"]
        reliability_weight = policy["reliability_weight"]
        cost_weight = policy["cost_weight"]
        deadline_weight = policy["deadline_weight"]
        congestion_weight = policy["congestion_weight"]

        def score(backend: BackendProfile) -> float:
            available_at = state[f"{backend.name}:available_at"]
            queue_pressure = max(0.0, available_at - state["time_cursor"])
            compile_est = backend.compile_factor * ((job.qubits * job.depth) ** 0.5)
            execute_est = (job.depth * job.shots) / backend.exec_rate
            latency_est = queue_pressure + compile_est + execute_est
            reliability_risk = backend.failure_rate + (
                backend.congestion_sensitivity * queue_pressure / max(backend.queue_capacity, 1)
            )
            deadline_penalty = max(0.0, latency_est - job.deadline_s) / max(job.deadline_s, 1.0)
            cost_est = (compile_est + execute_est) * backend.cost_per_second
            return (
                latency_weight * latency_est
                + reliability_weight * reliability_risk
                + cost_weight * cost_est
                + deadline_weight * deadline_penalty
                + congestion_weight * queue_pressure
            )

        return min(backends, key=score)

