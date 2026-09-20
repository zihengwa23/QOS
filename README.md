# QOS

一个面向量子计算任务的初级批处理操作系统原型。

目标：通过批处理和流水线调度，让经典准备与量子执行并行，提升量子计算时间占比（quantum utilization），降低经典准备时间占比。

## 核心思路

- 任务模型：每个任务包含 `classical_prep_time` 和 `quantum_exec_time`
- 批处理优化：同一批内复用部分准备流程（`prep_reuse_factor`）
- 流水线执行：经典控制器持续准备下一个任务，量子处理器持续执行已就绪任务

## 运行示例

```bash
python /home/runner/work/QOS/QOS/qos_scheduler.py
```

## 运行测试

```bash
cd /home/runner/work/QOS/QOS
python -m unittest -q
```
