# 周报（2026-09-14 至 2026-09-20）

## 本周进展

本周主要完成了 QOS 项目的初步搭建，重点是先把“量子批处理调度”这件事做成一个可运行、可验证的仿真原型，并围绕 IBM 平台风格的基线建立最小实验框架。

### 1. 搭建批处理量子调度原型

- 新增 [qos_scheduler.py](qos_scheduler.py)，实现了一个最小可用的批处理量子调度器原型。
- 新增 [tests/test_qos_scheduler.py](tests/test_qos_scheduler.py)，对调度器的基础行为做了回归验证。
- 补充 [README.md](README.md) 和 [.gitignore](.gitignore)，让仓库结构更完整，也方便后续继续扩展。

### 2. 搭建 IBM 基线下的验证框架

- 新建了 QOS 验证框架骨架，包括 [run_experiment.py](run_experiment.py) 和 [qos/](qos) 下的核心模块。
- 新增 [configs/ibm_like_baseline.json](configs/ibm_like_baseline.json)，用于描述 IBM 风格的仿真平台、后端参数、负载分布和评估指标。
- 新增 [qos/models.py](qos/models.py)、[qos/workloads.py](qos/workloads.py)、[qos/scheduler.py](qos/scheduler.py)、[qos/pipeline.py](qos/pipeline.py)、[qos/experiment.py](qos/experiment.py) 和 [qos/analysis.py](qos/analysis.py)，把作业建模、负载生成、调度、链路仿真、实验执行和结果分析串成了一个完整流程。
- 新增 [tests/test_experiment.py](tests/test_experiment.py)，用于验证整套实验管线的输出结构。

### 3. 初步调通实验闭环

- 完成了 IBM 相关基线下的首轮仿真跑通，能生成实验结果和对照报告。
- 后续又对失败压力模型做了小幅调整，并生成了 [artifacts/comparison_report.md](artifacts/comparison_report.md) 与 [artifacts/experiment_result.json](artifacts/experiment_result.json)，说明这套框架已经具备“配置 - 仿真 - 输出报告”的最小闭环。

## 本周结论

这周的工作重点不是做复杂优化，而是先把项目骨架搭出来：一方面有了一个可以运行的批处理调度原型，另一方面也有了一个围绕 IBM 风格平台参数的验证框架。整体上已经从“想法”进入到“可执行原型”的阶段。

不过目前这套框架仍然是仿真性质，更多是在模拟 IBM 云平台风格的作业提交、排队、编译、执行和回传过程，还没有接入真实平台或真实工具链。

## 下周计划

### 1. 继续完善仿真模型

- 细化失败率、排队压力、编译开销等参数，让仿真结果更稳定、更可解释。
- 进一步检查调度策略在不同负载下的表现，看看是否能体现出 QOS 思路的收益。

### 2. 提升实验可复现性

- 固化更多实验配置，减少手工改参数的成本。
- 补充更多测试和示例输出，确保每次改动后都能快速验证。

### 3. 为后续平台接入做准备

- 先保持 IBM 基线不变，把仿真和实验框架稳定下来。
- 等框架稳定后，再考虑是否需要接入更真实的平台接口或进一步扩展调度逻辑。