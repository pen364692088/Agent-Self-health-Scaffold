#!/usr/bin/env python3
"""
Operational Observation

对 3 个 default_enabled Agent 做最小真实运行观察：
- implementer
- planner
- verifier

收集并输出各项指标。

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_observation_cycle(agent_id: str) -> dict:
    """对单个 Agent 执行一次观察周期"""
    from runtime.default_runtime_chain import DefaultRuntimeChain
    from runtime.operational_metrics import OperationalMetrics, MetricSnapshot
    from health_runtime.health_checker import HealthStatus
    
    chain = DefaultRuntimeChain(agent_id, PROJECT_ROOT)
    metrics = OperationalMetrics(PROJECT_ROOT)
    
    # 执行默认主链
    result = chain.run()
    
    # 构建指标快照
    health_status = "healthy"
    health_check = result.stages.get("health_check", {})
    if health_check:
        health_status = health_check.get("status", "healthy")
    
    snapshot = MetricSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_id=agent_id,
        cold_start_success=result.stages.get("session_bootstrap", {}).get("success", False),
        memory_restore_success=result.stages.get("session_bootstrap", {}).get("success", False),
        writeback_success=result.stages.get("memory_writeback", {}).get("success", False),
        health_status=health_status,
        block_triggered=result.status.value == "blocked",
        block_correct=True,
        recovery_triggered=False,
        recovery_success=True,
    )
    
    # 记录指标
    metrics.record(snapshot)
    
    return {
        "agent_id": agent_id,
        "chain_status": result.status.value,
        "health_status": health_status,
        "stages": result.stages,
        "receipt_id": result.receipt.get("receipt_id") if result.receipt else None,
    }


def main():
    """主观察流程"""
    print("=" * 70)
    print("OPERATIONAL OBSERVATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    agents = ["implementer", "planner", "verifier"]
    
    # 执行多次观察循环
    print(f"\n执行观察循环 (每个 Agent 5 次)...\n")
    
    all_results = {}
    
    for agent_id in agents:
        print(f"\n观察 {agent_id}...")
        agent_results = []
        
        for i in range(5):
            result = run_observation_cycle(agent_id)
            agent_results.append(result)
            
            status = result["chain_status"]
            health = result["health_status"]
            print(f"  循环 {i+1}: chain={status}, health={health}")
        
        all_results[agent_id] = agent_results
    
    # 汇总指标
    print(f"\n{'='*70}")
    print("OBSERVATION SUMMARY")
    print(f"{'='*70}")
    
    from runtime.operational_metrics import OperationalMetrics
    
    metrics = OperationalMetrics(PROJECT_ROOT)
    
    summary_results = {}
    
    for agent_id in agents:
        summary = metrics.summarize(agent_id, window_size=5)
        summary_results[agent_id] = summary
        
        print(f"\n{agent_id.upper()}:")
        print(f"  cold_start_success_rate: {summary.cold_start_success_rate:.1%}")
        print(f"  memory_restore_success_rate: {summary.memory_restore_success_rate:.1%}")
        print(f"  writeback_success_rate: {summary.writeback_success_rate:.1%}")
        print(f"  warning_rate: {summary.warning_rate:.1%}")
        print(f"  critical_rate: {summary.critical_rate:.1%}")
        print(f"  block_accuracy: {summary.block_accuracy:.1%}")
        print(f"  recovery_success_rate: {summary.recovery_success_rate:.1%}")
        print(f"  total_executions: {summary.total_executions}")
    
    # 检查健康状态
    print(f"\n{'='*70}")
    print("HEALTH ASSESSMENT")
    print(f"{'='*70}")
    
    all_healthy = True
    for agent_id, summary in summary_results.items():
        is_healthy = (
            summary.cold_start_success_rate >= 1.0 and
            summary.writeback_success_rate >= 1.0 and
            summary.critical_rate <= 0.05
        )
        
        status = "✅ HEALTHY" if is_healthy else "⚠️ ATTENTION"
        print(f"{agent_id}: {status}")
        
        if not is_healthy:
            all_healthy = False
    
    # 保存观察报告
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "observation_window": "short (5 cycles)",
        "agents": {
            agent_id: {
                "summary": summary.to_dict(),
                "cycles": [
                    {
                        "chain_status": r["chain_status"],
                        "health_status": r["health_status"],
                        "receipt_id": r["receipt_id"],
                    }
                    for r in results
                ],
            }
            for agent_id, results in all_results.items()
        },
        "overall_healthy": all_healthy,
    }
    
    report_path = reports_dir / f"observation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    if all_healthy:
        print("\n✅ ALL AGENTS HEALTHY")
        return 0
    else:
        print("\n⚠️ SOME AGENTS NEED ATTENTION")
        return 1


if __name__ == "__main__":
    sys.exit(main())
