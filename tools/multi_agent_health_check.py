#!/usr/bin/env python3
"""
Multi-Agent Health Check

对所有已接入 Agent 执行健康检查并输出汇总报告。

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    print("=" * 70)
    print("MULTI-AGENT HEALTH CHECK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    from core.agent_profile import AgentProfileRegistry
    from health_runtime.health_checker import HealthChecker, HealthConfig
    
    # 加载所有 pilot agents
    registry = AgentProfileRegistry(PROJECT_ROOT)
    registry.load_all()
    
    pilots = registry.get_pilot_agents()
    
    if not pilots:
        print("❌ No pilot agents found")
        return 1
    
    results = {}
    
    for profile in pilots:
        print(f"\n{'='*60}")
        print(f"Agent: {profile.agent_id.upper()}")
        print(f"{'='*60}")
        
        config = HealthConfig(
            agent_id=profile.agent_id,
            project_root=PROJECT_ROOT,
        )
        
        checker = HealthChecker(config)
        report = checker.check_all()
        
        results[profile.agent_id] = report
        
        # 打印摘要
        print(report.summary)
    
    # 汇总
    print(f"\n{'='*70}")
    print("HEALTH CHECK SUMMARY")
    print(f"{'='*70}")
    
    status_counts = {"healthy": 0, "warning": 0, "critical": 0}
    
    for agent_id, report in results.items():
        status = report.overall_status.value
        status_counts[status] += 1
        
        icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
        }.get(status, "❓")
        
        print(f"{icon} {agent_id}: {status.upper()}")
    
    print(f"\nTotal: {len(results)} agents")
    print(f"  ✅ Healthy: {status_counts['healthy']}")
    print(f"  ⚠️  Warning: {status_counts['warning']}")
    print(f"  ❌ Critical: {status_counts['critical']}")
    
    # 保存报告
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"health_report_{timestamp}.json"
    
    combined_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": {
            agent_id: report.to_dict()
            for agent_id, report in results.items()
        },
        "summary": status_counts,
    }
    
    with open(report_path, "w") as f:
        json.dump(combined_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    # 返回状态码
    if status_counts["critical"] > 0:
        return 2
    elif status_counts["warning"] > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
