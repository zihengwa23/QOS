from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from typing import MutableSet, Tuple

from .models import BackendProfile, Job


@dataclass(frozen=True)
class CompilationResult:
    compile_s: float
    reused: bool


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