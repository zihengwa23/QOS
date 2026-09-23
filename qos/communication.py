from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .models import BackendProfile


@dataclass(frozen=True)
class CommunicationResult:
    queue_wait_s: float
    return_s: float
    queue_pressure: float


class MPIQCommunicator:
    def prepare(self, backend: BackendProfile, state: dict, rng: Random) -> CommunicationResult:
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