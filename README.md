# QOS

一个面向批处理量子工作负载的“量子 OS + QOS 调度”验证框架。

## 目标

本仓库实现了两阶段能力：

1. **复现工具链驱动的运行链路（仿真）**  
   作业提交 → 编译（QLLVM）→ 通信/编排（MPI-Q）→ 平台执行（Fusion Lab）→ 结果回传 → 失败重试
2. **A/B 对照验证**  
   平台默认策略 vs QOS 策略，在统一负载和统一指标下可复现比较

当前仿真实现也按三层拆分：

- 编译层：[qos/compiler.py](qos/compiler.py) 负责 QLLVM 编译与编译缓存复用
- 通信层：[qos/communication.py](qos/communication.py) 负责排队、调度等待与回传延迟
- 执行层：[qos/executor.py](qos/executor.py) 负责执行时长、失败概率和成本
- 编排层：[qos/pipeline.py](qos/pipeline.py) 负责把三层串起来并汇总指标

## 真实工具链运行

默认配置使用 `runtime.mode = simulated`，不会访问外部工具。切换到真实运行时，需要在配置中提供：

```json
{
   "runtime": {
      "mode": "real",
      "qllvm": {
         "command": "qllvm",
         "target_backend": "qasm-backend",
         "opt_level": 1
      },
      "mpiq": {
         "prepare_command": "mpirun -np 2 ./path/to/mpi_q_runner --program {program} --job {job_id} --shots {shots}",
         "timeout_s": 300
      },
      "fusion_lab": {
         "submit_url": "https://your-fusion-lab-api.example/jobs",
         "token": "",
         "timeout_s": 600
      }
   }
}
```

真实作业的 workload spec 还需要提供 `program_path`，指向 OpenQASM 文件。QLLVM 适配器会调用 `qllvm <program> -qrt nisq -qpu ...` 生成编译产物；MPI-Q 适配器会执行配置的 MPI-Q runner；Fusion Lab 适配器会向配置的 HTTP endpoint 提交编译产物路径和作业参数。

由于 Fusion Lab 登录页没有公开 REST API 文档，`submit_url` 和返回 JSON 字段需要按老师/平台管理员提供的实际接口调整。目前适配器支持 `success`、`status`、`execute_s` 和 `cost` 字段，未配置真实端点时会明确报错，不会伪装成真实执行。

可复制 [configs/real_toolchain.example.json](configs/real_toolchain.example.json) 作为真实运行配置模板。运行前需要确认本机有 `qllvm`、`mpirun` 和一个链接 MPI-Q 库的 runner；当前环境尚未安装这两个命令，因此这里只完成了适配器和调用契约，尚未进行真实硬件端到端运行。

### 真实环境准备步骤

1. 安装本地构建依赖（Ubuntu/Debian 示例）：

   ```bash
   sudo apt update
    sudo apt install -y build-essential cmake ninja-build mpich libmpich-dev \
       libeigen3-dev libantlr4-runtime-dev libcurl4-openssl-dev \
       libedit-dev libzstd-dev python3-dev
   ```

    在 Debian 12 上还需要安装 LLVM/MLIR 开发包，否则会出现 `Could not find MLIRConfig.cmake`：

    ```bash
    sudo apt install -y llvm-19-dev libmlir-19-dev llvm-19-tools clang-19 lld-19
    ```

2. 编译安装 QLLVM：

   ```bash
   git clone https://gitee.com/QCFlow/QLLVM.git /tmp/QLLVM
   cd /tmp/QLLVM
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
       -DMLIR_DIR=/usr/lib/llvm-19/lib/cmake/mlir \
       -DLLVM_ROOT=/usr/lib/llvm-19
   cmake --build build -j2
   cmake --install build
   export PATH="$HOME/.qllvm/bin:$PATH"
   qllvm --help
   ```

   如果 CMake 找不到 LLVM/MLIR 或 antlr4-runtime，应按 QLLVM 官方安装文档补充对应版本，而不是随意替换系统 LLVM。

3. 编译 MPI-Q：

   ```bash
   git clone https://github.com/SchordingersDogCat/MPI-Q.git /tmp/MPI-Q
   cd /tmp/MPI-Q
   make PY_DIR=/usr/include/python3.11 \
        PY_LIB=/usr/lib/x86_64-linux-gnu \
        LDPYLIBS=-lpython3.11
   ```

   MPI-Q 仓库提供通信库和示例程序，但没有一个可直接作为本项目 runner 的统一命令。需要根据实验室的量子控制卡/服务端程序，编写一个调用 `MPIQ_Init`、`MPIQ_qasm` 或 `qasm_to_pulse_waveforms` 的 runner，再把它填入 `runtime.mpiq.prepare_command`。

4. 放置并检查真实 QASM：

   项目内提供了最小示例 [programs/bell.qasm](programs/bell.qasm)。复制 [configs/real_toolchain.example.json](configs/real_toolchain.example.json)，将 `program_path`、MPI-Q runner 路径和 Fusion Lab API 地址改成真实值。

5. 执行环境检查：

   ```bash
   /usr/bin/python3 scripts/check_real_toolchain.py \
     --config configs/real_toolchain.example.json
   ```

6. 通过检查后运行：

   ```bash
   /usr/bin/python3 run_experiment.py \
     --config configs/real_toolchain.example.json \
     --output-dir artifacts/real
   ```

   如果 Fusion Lab 使用的不是本文档中的 JSON 字段，需要在 [qos/executor.py](qos/executor.py) 的 `RealFusionLabExecutor` 中按平台接口调整请求路径、认证和返回字段。

并输出：
- 可复现实验配置（后端、负载、指标定义）
- 对照实验报告（默认策略 vs QOS）
- 优化清单（按收益/复杂度排序）

## 快速开始

```bash
python run_experiment.py \
   --config configs/toolchain_baseline.json \
   --output-dir artifacts
```

运行后会生成：
- `/home/runner/work/QOS/QOS/artifacts/experiment_result.json`
- `/home/runner/work/QOS/QOS/artifacts/comparison_report.md`

## 目录结构

- [run_experiment.py](run_experiment.py)：CLI 入口
- [qos/config.py](qos/config.py)：配置加载
- [qos/models.py](qos/models.py)：核心数据模型
- [qos/workloads.py](qos/workloads.py)：短突发/混合/长批量负载生成
- [qos/scheduler.py](qos/scheduler.py)：默认调度与 QOS 调度
- [qos/pipeline.py](qos/pipeline.py)：平台链路仿真与阶段计时
- [qos/compiler.py](qos/compiler.py)：编译层
- [qos/communication.py](qos/communication.py)：通信层
- [qos/executor.py](qos/executor.py)：执行层
- [qos/experiment.py](qos/experiment.py)：A/B 实验执行
- [qos/analysis.py](qos/analysis.py)：优化建议生成
- [configs/toolchain_baseline.json](configs/toolchain_baseline.json)：可复现实验配置
- [tests/test_experiment.py](tests/test_experiment.py)：基础回归测试

## 配置说明（核心字段）

- `toolchain`：工具链元数据（编译器、通信层、平台）
- `platform.name`：目标平台名称（例如 Fusion Lab 执行平台）
- `platform.backends`：后端参数（稳定后端 + 高负载后端）
- `workloads`：三类负载定义（short_burst / mixed_scale / long_batch）
- `ab_test`：A/B 策略、轮次、时隙
- `policy`：QOS 优化权重（延迟/可靠性/成本）

## 说明

当前版本是**可执行验证框架**，默认以仿真方式复现工具链驱动的批处理调度链路。  
后续接入真实 QLLVM / MPI-Q / Fusion Lab 运行环境时，可保留同一套指标、负载与 A/B 方法进行真实场景验证。

## 兼容：原型调度器

仓库仍保留原型批处理调度器：

- [qos_scheduler.py](qos_scheduler.py)
- [tests/test_qos_scheduler.py](tests/test_qos_scheduler.py)

运行示例：

```bash
python qos_scheduler.py
```

运行测试：

```bash
python -m unittest -q
```
