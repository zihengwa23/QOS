from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError
from random import Random
import time

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
        artifact_path: str | None = None,
    ) -> ExecutionResult:
        del artifact_path
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


class RealFusionLabExecutor:
    """Submit compiled programs to a configured Fusion Lab HTTP endpoint."""

    def __init__(self, submit_url: str, token: str = "", timeout_s: float = 600.0) -> None:
        self.submit_url = submit_url
        self.token = token
        self.timeout_s = timeout_s

    def execute(self, job, backend, queue_pressure, hour_slot, rng, artifact_path=None) -> ExecutionResult:
        del queue_pressure, hour_slot, rng
        if not artifact_path:
            raise ValueError("Real Fusion Lab mode requires a compiled artifact")
        artifact = Path(artifact_path)
        if not artifact.is_file():
            raise FileNotFoundError(f"Compiled artifact does not exist: {artifact}")
        payload = json.dumps({
            "job_id": job.job_id,
            "backend": backend.name,
            "shots": job.shots,
            "program_path": artifact_path,
            "program_qasm": artifact.read_text(encoding="utf-8"),
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request_obj = request.Request(self.submit_url, data=payload, headers=headers, method="POST")
        started = time.perf_counter()
        try:
            with request.urlopen(request_obj, timeout=self.timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Fusion Lab submission failed: {exc}") from exc
        elapsed = time.perf_counter() - started
        success = bool(body.get("success", body.get("status") in {"completed", "success"}))
        execute_s = float(body.get("execute_s", elapsed))
        cost = float(body.get("cost", 0.0))
        return ExecutionResult(execute_s=execute_s, success=success, cost=cost, failure_prob=0.0)


def _in_calibration_window(hour: int, backend: BackendProfile) -> bool:
    for window in backend.calibration_windows:
        if int(window["start_hour"]) <= hour < int(window["end_hour"]):
            return True
    return False