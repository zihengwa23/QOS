# QOS

一个最小可用的“量子云平台操作系统方式 + QOS 调度”验证框架。

## 目标

本仓库实现了两阶段能力：

1. **复现真机云平台运行链路（仿真）**  
   作业提交 → 排队 → 编译/映射 → 执行 → 结果回传 → 失败重试
2. **A/B 对照验证**  
   平台默认策略 vs QOS 策略，在统一负载和统一指标下可复现比较

并输出：
- 可复现实验配置（后端、负载、指标定义）
- 对照实验报告（默认策略 vs QOS）
- 优化清单（按收益/复杂度排序）

## 快速开始

```bash
python /home/runner/work/QOS/QOS/run_experiment.py \
  --config /home/runner/work/QOS/QOS/configs/ibm_like_baseline.json \
  --output-dir /home/runner/work/QOS/QOS/artifacts
```

运行后会生成：
- `/home/runner/work/QOS/QOS/artifacts/experiment_result.json`
- `/home/runner/work/QOS/QOS/artifacts/comparison_report.md`

## 目录结构

- `/home/runner/work/QOS/QOS/run_experiment.py`：CLI 入口
- `/home/runner/work/QOS/QOS/qos/config.py`：配置加载
- `/home/runner/work/QOS/QOS/qos/models.py`：核心数据模型
- `/home/runner/work/QOS/QOS/qos/workloads.py`：短突发/混合/长批量负载生成
- `/home/runner/work/QOS/QOS/qos/scheduler.py`：默认调度与 QOS 调度
- `/home/runner/work/QOS/QOS/qos/pipeline.py`：平台链路仿真与阶段计时
- `/home/runner/work/QOS/QOS/qos/experiment.py`：A/B 实验执行
- `/home/runner/work/QOS/QOS/qos/analysis.py`：优化建议生成
- `/home/runner/work/QOS/QOS/configs/ibm_like_baseline.json`：可复现实验配置
- `/home/runner/work/QOS/QOS/tests/test_experiment.py`：基础回归测试

## 配置说明（核心字段）

- `platform.name`：目标平台名称（例如 IBM Quantum Cloud）
- `platform.backends`：后端参数（稳定后端 + 高负载后端）
- `workloads`：三类负载定义（short_burst / mixed_scale / long_batch）
- `ab_test`：A/B 策略、轮次、时隙
- `policy`：QOS 优化权重（延迟/可靠性/成本）

## 说明

当前版本是**可执行验证框架**，默认以仿真方式复现真机云平台调度链路。  
后续接入真实 IBM 后端时，可保留同一套指标、负载与 A/B 方法进行真实场景验证。

## 兼容：原型调度器

仓库仍保留原型批处理调度器：

- `/home/runner/work/QOS/QOS/qos_scheduler.py`
- `/home/runner/work/QOS/QOS/tests/test_qos_scheduler.py`

运行示例：

```bash
python /home/runner/work/QOS/QOS/qos_scheduler.py
```

运行测试：

```bash
cd /home/runner/work/QOS/QOS
python -m unittest -q
```
