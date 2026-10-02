from __future__ import annotations

from dataclasses import dataclass
import shlex
import subprocess
import time
from random import Random

from .models import BackendProfile


@dataclass(frozen=True)
class CommunicationResult:
    queue_wait_s: float
    return_s: float
    queue_pressure: float


class MPIQCommunicator:
    def prepare(self, backend: BackendProfile, state: dict, rng: Random, job=None, artifact_path=None) -> CommunicationResult:
        del job, artifact_path
        available_at = state[f"{backend.name}:available_at"]
        queue_wait = max(0.0, available_at - state["time_cursor"])
        queue_wait += rng.uniform(0.0, backend.queue_delay_base_s)
        queue_pressure = queue_wait / max(backend.queue_delay_base_s * backend.queue_capacity, 1.0)
        return_s = rng.uniform(0.1, 0.5)
        return CommunicationResult(
            queue_wait_s=queue_wait,
            return_s=return_s,
            queue_pressure=queue_pressure,
        )


class RealMPIQCommunicator:
    """Invoke an MPI-Q preparation program built against the MPI-Q library."""

    def __init__(self, command: str, timeout_s: float = 300.0) -> None:
        self.command = command
        self.timeout_s = timeout_s

    def prepare(self, backend: BackendProfile, state: dict, rng: Random, job=None, artifact_path=None) -> CommunicationResult:
        del backend, state, rng
        if not job or not artifact_path:
            raise ValueError("Real MPI-Q mode requires a job and compiled artifact")
        command = shlex.split(self.command.format(
            job_id=job.job_id,
            program=artifact_path,
            shots=job.shots,
        ))
        started = time.perf_counter()
        completed = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout_s, check=False)
        elapsed = time.perf_counter() - started
        if completed.returncode != 0:
            raise RuntimeError(
                "MPI-Q preparation failed: "
                + (completed.stderr.strip() or completed.stdout.strip() or "unknown error")
            )
        return CommunicationResult(queue_wait_s=0.0, return_s=elapsed, queue_pressure=0.0)