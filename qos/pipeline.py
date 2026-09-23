from __future__ import annotations

import random
from typing import Dict, List, Tuple

from .communication import MPIQCommunicator
from .compiler import QLLVMCompiler
from .executor import FusionLabExecutor
from .models import BackendProfile, Job, JobResult


class QuantumPipelineSimulator:
    def __init__(
        self,
        backends: List[BackendProfile],
        max_retries: int,
        reuse_factor: float,
        compiler: QLLVMCompiler | None = None,
        communicator: MPIQCommunicator | None = None,
        executor: FusionLabExecutor | None = None,
    ) -> None:
        self.backends = backends
        self.max_retries = max_retries
        self.reuse_factor = reuse_factor
        self.compiler = compiler or QLLVMCompiler(reuse_factor)
        self.communicator = communicator or MPIQCommunicator()
        self.executor = executor or FusionLabExecutor()

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
                communication = self.communicator.prepare(backend, state, rng)
                compilation = self.compiler.compile(job, backend, compile_cache, rng)
                execution = self.executor.execute(job, backend, communication.queue_pressure, hour_slot, rng)
                queue_wait = communication.queue_wait_s
                compile_s = compilation.compile_s
                execute_s = execution.execute_s
                return_s = communication.return_s
                total_s = queue_wait + compile_s + execute_s + return_s

                success = execution.success

                backend_finish = state["time_cursor"] + total_s
                state[f"{backend.name}:available_at"] = max(state[f"{backend.name}:available_at"], backend_finish)

                cost = compilation.compile_s * backend.cost_per_second + execution.cost
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
