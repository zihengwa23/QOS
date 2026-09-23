# QOS A/B 对照实验报告

- 平台: Fusion Lab (simulated batch runtime)
- 工具链: QLLVM + MPI-Q + Fusion Lab
- 目标后端: fusionlab_stable_runtime, fusionlab_high_load_runtime
- 负载分布: {'short_burst': 24, 'mixed_scale': 18, 'long_batch': 12}
- A/B 设置: {'strategies': ['default', 'qos'], 'time_slots': [3, 11, 19], 'rounds_per_slot': 3}

## 核心指标（均值）

| 指标 | Default | QOS | 变化 |
|---|---:|---:|---:|
| Throughput (jobs/s) | 0.0037 | 0.0038 | 1.12% |
| Avg Queue Wait (s) | 3178.3275 | 3163.9395 | 0.45% (reduction) |
| Success Rate | 0.2449 | 0.2263 | -7.56% |
| Makespan (s) | 14518.0922 | 14357.9713 | 1.10% (reduction) |
| Retry Count | 129.22 | 134.56 | -4.13% (reduction) |
| Resource Utilization | 0.3404 | 0.3471 | 1.97% |
| Total Cost | 11497.5447 | 11336.0591 | 1.40% (reduction) |

## 优化清单（按建议顺序）
- [高/中] 排队侧：增强按实时拥塞动态分流，避免单后端堆积
- [中/中] 成本侧：引入成本-时延联合优化目标并动态调权
- [高/低] 可靠性侧：把校准窗口与历史错误率纳入调度惩罚项
- [高/中] 调度侧：加入作业时长预测与截止期优先级，降低长尾等待
- [中/低] 编译侧：复用相同/相近电路编译结果，降低重复编译开销

## 交付物状态
- [x] 可复现实验配置
- [x] 默认策略 vs QOS 对照实验结果
- [x] 优化建议清单