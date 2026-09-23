from __future__ import annotations

from typing import Dict, List


def build_optimization_checklist(result: Dict) -> List[Dict[str, str]]:
    default = result["results"]["default"]
    qos = result["results"]["qos"]
    cmp = result["comparison"]
    items: List[Dict[str, str]] = []

    if cmp["queue_wait_reduction_pct"] < 10:
        items.append(
            {
                "area": "排队侧",
                "recommendation": "增强按实时拥塞动态分流，避免单后端堆积",
                "expected_impact": "高",
                "complexity": "中",
            }
        )
    if cmp["cost_reduction_pct"] < 5:
        items.append(
            {
                "area": "成本侧",
                "recommendation": "引入成本-时延联合优化目标并动态调权",
                "expected_impact": "中",
                "complexity": "中",
            }
        )
    if cmp["success_rate_gain_pct"] < 3 or default["success_rate"] < 0.9 or qos["success_rate"] < 0.93:
        items.append(
            {
                "area": "可靠性侧",
                "recommendation": "把校准窗口与历史错误率纳入调度惩罚项",
                "expected_impact": "高",
                "complexity": "低",
            }
        )
    if cmp["throughput_gain_pct"] < 8:
        items.append(
            {
                "area": "调度侧",
                "recommendation": "加入作业时长预测与截止期优先级，降低长尾等待",
                "expected_impact": "高",
                "complexity": "中",
            }
        )
    if default["avg_compile_s"] > 2 or qos["avg_compile_s"] > 2:
        items.append(
            {
                "area": "编译侧",
                "recommendation": "复用相同/相近电路编译结果，降低重复编译开销",
                "expected_impact": "中",
                "complexity": "低",
            }
        )

    if not items:
        items.append(
            {
                "area": "持续优化",
                "recommendation": "当前收益达标，建议扩大负载规模并延长观测周期进行稳健性验证",
                "expected_impact": "中",
                "complexity": "低",
            }
        )
    return items


def render_markdown_report(result: Dict, checklist: List[Dict[str, str]]) -> str:
    default = result["results"]["default"]
    qos = result["results"]["qos"]
    cmp = result["comparison"]
    toolchain = result.get("toolchain") or {}
    toolchain_name = " + ".join(
        part for part in [toolchain.get("compiler"), toolchain.get("communication"), toolchain.get("platform")] if part
    )

    lines = [
        "# QOS A/B 对照实验报告",
        "",
        f"- 平台: {result['platform']}",
    ]
    if toolchain_name:
        lines.append(f"- 工具链: {toolchain_name}")
    lines.extend(
        [
            f"- 目标后端: {', '.join(b['name'] for b in result['target_backends'])}",
            f"- 负载分布: {result['workload_mix']}",
            f"- A/B 设置: {result['ab_setup']}",
            "",
            "## 核心指标（均值）",
            "",
            "| 指标 | Default | QOS | 变化 |",
            "|---|---:|---:|---:|",
            f"| Throughput (jobs/s) | {default['throughput_jobs_per_s']:.4f} | {qos['throughput_jobs_per_s']:.4f} | {cmp['throughput_gain_pct']:.2f}% |",
            f"| Avg Queue Wait (s) | {default['avg_queue_wait_s']:.4f} | {qos['avg_queue_wait_s']:.4f} | {cmp['queue_wait_reduction_pct']:.2f}% (reduction) |",
            f"| Success Rate | {default['success_rate']:.4f} | {qos['success_rate']:.4f} | {cmp['success_rate_gain_pct']:.2f}% |",
            f"| Makespan (s) | {default['makespan_s']:.4f} | {qos['makespan_s']:.4f} | {cmp['makespan_reduction_pct']:.2f}% (reduction) |",
            f"| Retry Count | {default['retry_count']:.2f} | {qos['retry_count']:.2f} | {cmp['retry_reduction_pct']:.2f}% (reduction) |",
            f"| Resource Utilization | {default['resource_utilization']:.4f} | {qos['resource_utilization']:.4f} | {cmp['resource_utilization_gain_pct']:.2f}% |",
            f"| Total Cost | {default['total_cost']:.4f} | {qos['total_cost']:.4f} | {cmp['cost_reduction_pct']:.2f}% (reduction) |",
            "",
            "## 优化清单（按建议顺序）",
        ]
    )
    for item in checklist:
        lines.append(
            f"- [{item['expected_impact']}/{item['complexity']}] {item['area']}：{item['recommendation']}"
        )
    lines.extend(
        [
            "",
            "## 交付物状态",
            "- [x] 可复现实验配置",
            "- [x] 默认策略 vs QOS 对照实验结果",
            "- [x] 优化建议清单",
        ]
    )
    return "\n".join(lines)

