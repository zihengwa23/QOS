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
