from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from pathlib import Path
import subprocess
import time
from typing import MutableSet, Tuple

from .models import BackendProfile, Job


@dataclass(frozen=True)
class CompilationResult:
    compile_s: float
    reused: bool
    artifact_path: str | None = None


class QLLVMCompiler:
    def __init__(self, reuse_factor: float) -> None:
        self.reuse_factor = reuse_factor

    def compile(
        self,
        job: Job,
        backend: BackendProfile,
        compile_cache: MutableSet[Tuple[int, int, str]],
        rng: Random,
    ) -> CompilationResult:
        compile_key = (job.qubits, round(job.depth, -1), backend.name)
        compile_s = backend.compile_factor * sqrt(job.qubits * job.depth)
        reused = compile_key in compile_cache
        if reused:
            compile_s *= self.reuse_factor
        compile_cache.add(compile_key)
        compile_s *= rng.uniform(0.95, 1.05)
        return CompilationResult(compile_s=compile_s, reused=reused)


class RealQLLVMCompiler:
    """Compile a job with the installed QLLVM command line compiler."""

    def __init__(self, command: str, target_backend: str, opt_level: int = 1) -> None:
        self.command = command
        self.target_backend = target_backend
        self.opt_level = opt_level

    def compile(
        self,
        job: Job,
        backend: BackendProfile,
        compile_cache: MutableSet[Tuple[int, int, str]],
        rng: Random,
    ) -> CompilationResult:
        del rng
        if not job.program_path:
            raise ValueError(f"Real QLLVM mode requires program_path for job {job.job_id}")
        source = Path(job.program_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"QASM program does not exist: {source}")

        cache_key = (job.qubits, round(job.depth, -1), backend.name, str(source))
        output = source.with_name(f"{source.stem}_{job.job_id}_compiled.qasm")
        if cache_key in compile_cache and output.is_file():
            return CompilationResult(compile_s=0.0, reused=True, artifact_path=str(output))

        command = [
            self.command,
            str(source),
            "-qrt",
            "nisq",
            "-qpu",
            self.target_backend or backend.name,
            f"-O{self.opt_level}",
            "-o",
            str(output.with_suffix("")),
        ]
        started = time.perf_counter()
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        elapsed = time.perf_counter() - started
        if completed.returncode != 0:
            raise RuntimeError(
                "QLLVM compilation failed: "
                + (completed.stderr.strip() or completed.stdout.strip() or "unknown error")
            )
        if not output.is_file():
            candidates = list(output.parent.glob(f"{output.stem}*"))
            if candidates:
                output = candidates[0]
            else:
                raise RuntimeError(f"QLLVM completed but produced no artifact at {output}")
        compile_cache.add(cache_key)
        return CompilationResult(compile_s=elapsed, reused=False, artifact_path=str(output))