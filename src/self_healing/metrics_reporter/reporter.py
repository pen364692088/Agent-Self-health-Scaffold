#!/usr/bin/env python3
"""
Metrics Reporter - 指标运营系统

职责：
1. 收集自愈系统运行指标
2. 生成日报/周报
3. 监控趋势和异常
4. 提供数据支撑决策
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class DailyMetrics:
    """每日指标"""
    date: str
    
    # 失败相关
    total_failures: int
    captured_failures: int
    failure_capture_rate: float
    
    # 修复相关
    auto_remediation_attempts: int
    auto_remediation_successes: int
    auto_remediation_success_rate: float
    
    # 质量相关
    false_fixes: int
    false_fix_rate: float
    rollbacks: int
    
    # 预防相关
    prevention_hits: int
    prevention_hit_rate: float
    
    # 效率相关
    mean_time_to_recover_ms: int
    
    # 签名相关
    recurrence_by_signature: Dict[str, int]
    new_signatures: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsReporter:
    """指标报告器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.metrics_dir = self.workspace / "artifacts" / "self_healing" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储
        self.daily_metrics_file = self.metrics_dir / "daily_metrics.jsonl"
    
    def collect_daily_metrics(self, date: Optional[str] = None) -> DailyMetrics:
        """收集每日指标"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 从各个模块收集数据
        failures = self._count_failures(date)
        remediations = self._count_remediations(date)
        preventions = self._count_preventions(date)
        
        metrics = DailyMetrics(
            date=date,
            total_failures=failures["total"],
            captured_failures=failures["captured"],
            failure_capture_rate=failures["capture_rate"],
            auto_remediation_attempts=remediations["attempts"],
            auto_remediation_successes=remediations["successes"],
            auto_remediation_success_rate=remediations["success_rate"],
            false_fixes=remediations["false_fixes"],
            false_fix_rate=remediations["false_fix_rate"],
            rollbacks=remediations["rollbacks"],
            prevention_hits=preventions["hits"],
            prevention_hit_rate=preventions["hit_rate"],
            mean_time_to_recover_ms=remediations["mttr"],
            recurrence_by_signature=failures["recurrence"],
            new_signatures=failures["new_signatures"]
        )
        
        # 保存
        self._save_daily_metrics(metrics)
        
        return metrics
    
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """生成日报"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        metrics = self.collect_daily_metrics(date)
        
        report = f"""# Self-Healing Daily Report - {date}

## Summary

| Metric | Value |
|--------|-------|
| Total Failures | {metrics.total_failures} |
| Failure Capture Rate | {metrics.failure_capture_rate:.1%} |
| Auto Remediation Success Rate | {metrics.auto_remediation_success_rate:.1%} |
| False Fix Rate | {metrics.false_fix_rate:.1%} |
| Prevention Hit Rate | {metrics.prevention_hit_rate:.1%} |
| Mean Time to Recover | {metrics.mean_time_to_recover_ms / 1000:.1f}s |

## Details

### Failures
- Total: {metrics.total_failures}
- Captured: {metrics.captured_failures}
- New Signatures: {metrics.new_signatures}

### Remediation
- Attempts: {metrics.auto_remediation_attempts}
- Successes: {metrics.auto_remediation_successes}
- False Fixes: {metrics.false_fixes}
- Rollbacks: {metrics.rollbacks}

### Prevention
- Hits: {metrics.prevention_hits}

### Recurrence by Signature
"""
        
        for sig, count in sorted(metrics.recurrence_by_signature.items(), key=lambda x: -x[1]):
            report += f"- {sig}: {count}\n"
        
        # 保存报告
        report_file = self.metrics_dir / f"report_{date}.md"
        report_file.write_text(report)
        
        return report
    
    def generate_weekly_report(self, week_start: Optional[str] = None) -> str:
        """生成周报"""
        if week_start is None:
            # 本周一
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        # 收集一周数据
        week_metrics = []
        for i in range(7):
            date = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = self._load_daily_metrics(date)
            if metrics:
                week_metrics.append(metrics)
        
        if not week_metrics:
            return "No data for the week"
        
        # 汇总
        total_failures = sum(m.total_failures for m in week_metrics)
        avg_capture_rate = sum(m.failure_capture_rate for m in week_metrics) / len(week_metrics)
        avg_success_rate = sum(m.auto_remediation_success_rate for m in week_metrics) / len(week_metrics)
        
        report = f"""# Self-Healing Weekly Report - Week of {week_start}

## Summary

| Metric | Weekly Total | Daily Average |
|--------|--------------|---------------|
| Total Failures | {total_failures} | {total_failures / 7:.1f} |
| Avg Capture Rate | - | {avg_capture_rate:.1%} |
| Avg Success Rate | - | {avg_success_rate:.1%} |

## Daily Breakdown

| Date | Failures | Capture Rate | Success Rate | False Fixes |
|------|----------|--------------|--------------|-------------|
"""
        
        for m in week_metrics:
            report += f"| {m.date} | {m.total_failures} | {m.failure_capture_rate:.1%} | {m.auto_remediation_success_rate:.1%} | {m.false_fixes} |\n"
        
        # 保存报告
        report_file = self.metrics_dir / f"report_week_{week_start}.md"
        report_file.write_text(report)
        
        return report
    
    def check_red_flags(self) -> List[str]:
        """检查红线指标"""
        alerts = []
        
        # 获取最近7天数据
        recent_metrics = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = self._load_daily_metrics(date)
            if metrics:
                recent_metrics.append(metrics)
        
        if not recent_metrics:
            return alerts
        
        # 检查1: 捕获率下降
        capture_rates = [m.failure_capture_rate for m in recent_metrics]
        if len(capture_rates) >= 3:
            if capture_rates[0] < capture_rates[1] < capture_rates[2]:
                alerts.append(f"🚨 Failure capture rate declining: {capture_rates[2]:.1%} -> {capture_rates[0]:.1%}")
        
        # 检查2: 误修率过高
        avg_false_fix_rate = sum(m.false_fix_rate for m in recent_metrics) / len(recent_metrics)
        if avg_false_fix_rate > 0.1:
            alerts.append(f"🚨 False fix rate too high: {avg_false_fix_rate:.1%} (threshold: 10%)")
        
        # 检查3: 成功率过低
        avg_success_rate = sum(m.auto_remediation_success_rate for m in recent_metrics) / len(recent_metrics)
        if avg_success_rate < 0.5:
            alerts.append(f"🚨 Auto-remediation success rate too low: {avg_success_rate:.1%} (threshold: 50%)")
        
        # 检查4: 复发率过高
        total_recurrence = sum(sum(m.recurrence_by_signature.values()) for m in recent_metrics)
        if total_recurrence > 10:
            alerts.append(f"🚨 High recurrence: {total_recurrence} cases in last 7 days")
        
        return alerts
    
    def _count_failures(self, date: str) -> Dict:
        """统计失败"""
        # 简化实现
        return {
            "total": 0,
            "captured": 0,
            "capture_rate": 0.0,
            "recurrence": {},
            "new_signatures": 0
        }
    
    def _count_remediations(self, date: str) -> Dict:
        """统计修复"""
        # 简化实现
        return {
            "attempts": 0,
            "successes": 0,
            "success_rate": 0.0,
            "false_fixes": 0,
            "false_fix_rate": 0.0,
            "rollbacks": 0,
            "mttr": 0
        }
    
    def _count_preventions(self, date: str) -> Dict:
        """统计预防"""
        # 简化实现
        return {
            "hits": 0,
            "hit_rate": 0.0
        }
    
    def _save_daily_metrics(self, metrics: DailyMetrics):
        """保存每日指标"""
        with open(self.daily_metrics_file, "a") as f:
            f.write(json.dumps(metrics.to_dict(), ensure_ascii=False) + "\n")
    
    def _load_daily_metrics(self, date: str) -> Optional[DailyMetrics]:
        """加载每日指标"""
        if not self.daily_metrics_file.exists():
            return None
        
        with open(self.daily_metrics_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("date") == date:
                        return DailyMetrics(**record)
                except:
                    pass
        return None


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Metrics Reporter")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--daily", action="store_true", help="Generate daily report")
    parser.add_argument("--weekly", action="store_true", help="Generate weekly report")
    parser.add_argument("--check", action="store_true", help="Check red flags")
    
    args = parser.parse_args()
    
    reporter = MetricsReporter(Path(args.workspace))
    
    if args.daily:
        report = reporter.generate_daily_report()
        print(report)
    
    if args.weekly:
        report = reporter.generate_weekly_report()
        print(report)
    
    if args.check:
        alerts = reporter.check_red_flags()
        if alerts:
            print("\n".join(alerts))
        else:
            print("✅ All metrics within normal range")
