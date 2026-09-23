# 周报（2026-09-21 至 2026-09-27）

## 本周进展

本周主要完成了 QOS 项目的方向切换与仿真框架重构，目标是把原来偏“单一参数驱动”的实验框架，调整成更像“量子批处理 OS”的分层结构。

### 1. 从 IBM 基线切换到工具链基线

- 将默认实验配置从 IBM 相关命名与表述切换为 QLLVM / MPI-Q / Fusion Lab。
- 新增工具链基线配置 [configs/toolchain_baseline.json](configs/toolchain_baseline.json)，把编译器、通信层和平台元数据显式写入配置。
- 更新实验结果输出，让报告中可以直接看到工具链信息，而不是只显示平台参数。

### 2. 将仿真逻辑拆成三层

- 新增 [qos/compiler.py](qos/compiler.py)，抽出编译层，模拟 QLLVM 风格的编译与编译缓存复用。
- 新增 [qos/communication.py](qos/communication.py)，抽出通信层，模拟 MPI-Q 风格的排队等待、通信回传和拥塞压力。
- 新增 [qos/executor.py](qos/executor.py)，抽出执行层，模拟 Fusion Lab 风格的平台执行、失败概率和执行成本。
- 重构 [qos/pipeline.py](qos/pipeline.py)，让它变成编排层，把编译、通信、执行三个阶段串起来，而不是把所有逻辑揉在一起。

### 3. 同步更新文档、测试与产物

- 更新 [README.md](README.md)，补充了当前仿真结构和三层职责说明。
- 更新回归测试 [tests/test_experiment.py](tests/test_experiment.py)，改为读取新的工具链基线配置，并验证工具链字段。
- 重新生成了 [artifacts/comparison_report.md](artifacts/comparison_report.md) 和 [artifacts/experiment_result.json](artifacts/experiment_result.json)，确保示例产物与新结构一致。
- 已完成一次回归验证，确认实验可正常运行。

## 本周结论

当前项目已经从“参数驱动的单体仿真”升级为“带有编译层、通信层、执行层的分层仿真框架”。这比最开始更接近量子批处理 OS 的表达方式，也更方便后续继续接真实工具链或真实 trace。

不过目前仍然是仿真，不是实际接入 QLLVM、MPI-Q 和 Fusion Lab 的真实运行链路。现在这些工具更多是作为概念映射和接口预留，而不是已经完成真实集成。

## 后续计划

### 1. 继续抽象成可插拔接口

- 把编译层、通信层、执行层再进一步抽象成适配器接口。
- 为后续接入真实 QLLVM、MPI-Q、Fusion Lab 留出替换点。

### 2. 增加 OS 风格调度层

- 把作业队列管理、资源分配、重试与优先级控制单独拆出来。
- 让“量子 OS”职责更清晰，而不只是一个 pipeline 仿真器。

### 3. 增强实验可信度

- 增加更明确的对比实验设计。
- 如果能拿到真实工具链输出或 trace，尝试把仿真参数替换为实际观测数据。
- 补充更多负载场景，重点观察吞吐、等待、成功率和重复编译收益。
