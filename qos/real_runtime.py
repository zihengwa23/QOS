from __future__ import annotations

from typing import Any, Dict, Tuple

from .communication import MPIQCommunicator, RealMPIQCommunicator
from .compiler import QLLVMCompiler, RealQLLVMCompiler
from .executor import FusionLabExecutor, RealFusionLabExecutor


def build_runtime_components(config: Dict[str, Any]) -> Tuple[Any, Any, Any]:
    runtime = config.get("runtime", {})
    mode = runtime.get("mode", "simulated")
    if mode == "simulated":
        reuse_factor = config["policy"]["compile_reuse_factor"]
        return (
            QLLVMCompiler(reuse_factor),
            MPIQCommunicator(),
            FusionLabExecutor(),
        )
    if mode != "real":
        raise ValueError(f"Unsupported runtime mode: {mode}")

    compiler = runtime.get("qllvm", {})
    mpiq = runtime.get("mpiq", {})
    fusion_lab = runtime.get("fusion_lab", {})
    missing = []
    if not compiler.get("command"):
        missing.append("runtime.qllvm.command")
    if not mpiq.get("prepare_command"):
        missing.append("runtime.mpiq.prepare_command")
    if not fusion_lab.get("submit_url"):
        missing.append("runtime.fusion_lab.submit_url")
    if missing:
        raise ValueError("Real runtime configuration is incomplete: " + ", ".join(missing))

    return (
        RealQLLVMCompiler(
            command=compiler["command"],
            target_backend=compiler.get("target_backend", "qasm-backend"),
            opt_level=int(compiler.get("opt_level", 1)),
        ),
        RealMPIQCommunicator(
            command=mpiq["prepare_command"],
            timeout_s=float(mpiq.get("timeout_s", 300.0)),
        ),
        RealFusionLabExecutor(
            submit_url=fusion_lab["submit_url"],
            token=fusion_lab.get("token", ""),
            timeout_s=float(fusion_lab.get("timeout_s", 600.0)),
        ),
    )