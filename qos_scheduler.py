from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class QuantumJob:
    name: str
    classical_prep_time: float
    quantum_exec_time: float


@dataclass(frozen=True)
class JobExecution:
    name: str
    prep_start: float
    prep_end: float
    quantum_start: float
    quantum_end: float


@dataclass(frozen=True)
class ScheduleResult:
    timeline: List[JobExecution]
    total_classical_prep_time: float
    total_quantum_exec_time: float
    makespan: float

    @property
    def quantum_utilization(self) -> float:
        if self.makespan == 0:
            return 0.0
        return self.total_quantum_exec_time / self.makespan


class BatchQuantumScheduler:
    """Batch-like scheduler that overlaps classical prep with quantum execution."""

    def __init__(self, *, batch_size: int = 4, prep_reuse_factor: float = 0.75) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if not (0 < prep_reuse_factor <= 1):
            raise ValueError("prep_reuse_factor must be in (0, 1]")
        self.batch_size = batch_size
        self.prep_reuse_factor = prep_reuse_factor

    def naive(self, jobs: Iterable[QuantumJob]) -> ScheduleResult:
        return self._simulate(jobs, apply_batch_reuse=False)

    def batched(self, jobs: Iterable[QuantumJob]) -> ScheduleResult:
        return self._simulate(jobs, apply_batch_reuse=True)

    def _simulate(self, jobs: Iterable[QuantumJob], *, apply_batch_reuse: bool) -> ScheduleResult:
        timeline: List[JobExecution] = []
        classical_clock = 0.0
        quantum_clock = 0.0
        total_classical = 0.0
        total_quantum = 0.0

        for index, job in enumerate(jobs):
            prep_time = job.classical_prep_time
            if apply_batch_reuse and index % self.batch_size != 0:
                prep_time *= self.prep_reuse_factor

            prep_start = classical_clock
            prep_end = prep_start + prep_time
            classical_clock = prep_end

            quantum_start = max(prep_end, quantum_clock)
            quantum_end = quantum_start + job.quantum_exec_time
            quantum_clock = quantum_end

            total_classical += prep_time
            total_quantum += job.quantum_exec_time
            timeline.append(
                JobExecution(
                    name=job.name,
                    prep_start=prep_start,
                    prep_end=prep_end,
                    quantum_start=quantum_start,
                    quantum_end=quantum_end,
                )
            )

        makespan = timeline[-1].quantum_end if timeline else 0.0
        return ScheduleResult(
            timeline=timeline,
            total_classical_prep_time=total_classical,
            total_quantum_exec_time=total_quantum,
            makespan=makespan,
        )


def demo() -> None:
    jobs = [
        QuantumJob("state-prepare", 8, 4),
        QuantumJob("variational-step", 8, 4),
        QuantumJob("error-mitigation", 8, 4),
        QuantumJob("measurement", 8, 4),
    ]
    scheduler = BatchQuantumScheduler(batch_size=2, prep_reuse_factor=0.5)
    naive = scheduler.naive(jobs)
    batched = scheduler.batched(jobs)

    print(f"naive quantum utilization: {naive.quantum_utilization:.2%}")
    print(f"batched quantum utilization: {batched.quantum_utilization:.2%}")


if __name__ == "__main__":
    demo()
