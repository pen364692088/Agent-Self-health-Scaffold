#!/usr/bin/env python3
"""
Health Check CLI

对指定 Agent 执行健康检查并输出报告。

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Agent Health Check")
    parser.add_argument("--agent-id", required=True, help="Agent ID to check")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save-report", help="Save report to file")
    
    args = parser.parse_args()
    
    from health_runtime.health_checker import HealthChecker, HealthConfig
    
    config = HealthConfig(
        agent_id=args.agent_id,
        project_root=PROJECT_ROOT,
    )
    
    checker = HealthChecker(config)
    report = checker.check_all()
    
    # 输出
    if args.json:
        output = report.to_json()
    else:
        output = report.summary
    
    print(output)
    
    # 保存报告
    if args.save_report:
        report_path = Path(args.save_report)
        report.save(report_path)
        print(f"\n📄 Report saved to: {report_path}")
    
    # 返回状态码
    if report.overall_status.value == "critical":
        return 2
    elif report.overall_status.value == "warning":
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
