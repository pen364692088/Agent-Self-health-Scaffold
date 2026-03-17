#!/usr/bin/env python3
"""
Operational Metrics Collector

收集和汇总运行指标：
- cold_start_success_rate
- memory_restore_success_rate
- writeback_success_rate
- warning_rate
- critical_rate
- block_accuracy
- recovery_success_rate

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json


@dataclass
class MetricSnapshot:
    """指标快照"""
    timestamp: str
    agent_id: str
    cold_start_success: bool = True
    memory_restore_success: bool = True
    writeback_success: bool = True
    health_status: str = "healthy"
    block_triggered: bool = False
    block_correct: bool = True
    recovery_triggered: bool = False
    recovery_success: bool = True


@dataclass
class MetricsSummary:
    """指标汇总"""
    agent_id: str
    window_type: str
    window_size: int
    cold_start_success_rate: float = 0.0
    memory_restore_success_rate: float = 0.0
    writeback_success_rate: float = 0.0
    warning_rate: float = 0.0
    critical_rate: float = 0.0
    block_accuracy: float = 0.0
    recovery_success_rate: float = 0.0
    total_executions: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "window_type": self.window_type,
            "window_size": self.window_size,
            "cold_start_success_rate": f"{self.cold_start_success_rate:.1%}",
            "memory_restore_success_rate": f"{self.memory_restore_success_rate:.1%}",
            "writeback_success_rate": f"{self.writeback_success_rate:.1%}",
            "warning_rate": f"{self.warning_rate:.1%}",
            "critical_rate": f"{self.critical_rate:.1%}",
            "block_accuracy": f"{self.block_accuracy:.1%}",
            "recovery_success_rate": f"{self.recovery_success_rate:.1%}",
            "total_executions": self.total_executions,
        }


class OperationalMetrics:
    """
    运行指标收集器
    """
    
    # 观察窗口定义
    SHORT_WINDOW = 20  # 最近 20 次任务
    MEDIUM_WINDOW = 50  # 最近 50 次任务
    
    # 阈值定义
    CRITICAL_RATE_THRESHOLD = 0.05  # 5%
    WARNING_RATE_THRESHOLD = 0.20  # 20%
    WRITEBACK_SUCCESS_THRESHOLD = 1.0  # 100%
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics_dir = project_root / "logs" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def record(self, snapshot: MetricSnapshot) -> None:
        """记录指标快照"""
        metrics_file = self.metrics_dir / f"{snapshot.agent_id}_metrics.jsonl"
        
        with open(metrics_file, "a") as f:
            f.write(json.dumps({
                "timestamp": snapshot.timestamp,
                "agent_id": snapshot.agent_id,
                "cold_start_success": snapshot.cold_start_success,
                "memory_restore_success": snapshot.memory_restore_success,
                "writeback_success": snapshot.writeback_success,
                "health_status": snapshot.health_status,
                "block_triggered": snapshot.block_triggered,
                "block_correct": snapshot.block_correct,
                "recovery_triggered": snapshot.recovery_triggered,
                "recovery_success": snapshot.recovery_success,
            }) + "\n")
    
    def summarize(self, agent_id: str, window_size: int = 20) -> MetricsSummary:
        """
        汇总指标
        
        Args:
            agent_id: Agent ID
            window_size: 窗口大小
        
        Returns:
            MetricsSummary
        """
        metrics_file = self.metrics_dir / f"{agent_id}_metrics.jsonl"
        
        if not metrics_file.exists():
            return MetricsSummary(
                agent_id=agent_id,
                window_type="short" if window_size <= 20 else "medium",
                window_size=window_size,
            )
        
        # 读取最近的记录
        records = []
        with open(metrics_file, "r") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except:
                    pass
        
        # 取最近 N 条
        records = records[-window_size:]
        
        if not records:
            return MetricsSummary(
                agent_id=agent_id,
                window_type="short" if window_size <= 20 else "medium",
                window_size=window_size,
            )
        
        # 计算各项指标
        total = len(records)
        
        cold_starts = sum(1 for r in records if r.get("cold_start_success", True))
        memory_restores = sum(1 for r in records if r.get("memory_restore_success", True))
        writebacks = sum(1 for r in records if r.get("writeback_success", True))
        warnings = sum(1 for r in records if r.get("health_status") == "warning")
        criticals = sum(1 for r in records if r.get("health_status") == "critical")
        
        blocks = [r for r in records if r.get("block_triggered", False)]
        correct_blocks = sum(1 for r in blocks if r.get("block_correct", True))
        
        recoveries = [r for r in records if r.get("recovery_triggered", False)]
        successful_recoveries = sum(1 for r in recoveries if r.get("recovery_success", True))
        
        return MetricsSummary(
            agent_id=agent_id,
            window_type="short" if window_size <= 20 else "medium",
            window_size=window_size,
            cold_start_success_rate=cold_starts / total if total > 0 else 0,
            memory_restore_success_rate=memory_restores / total if total > 0 else 0,
            writeback_success_rate=writebacks / total if total > 0 else 0,
            warning_rate=warnings / total if total > 0 else 0,
            critical_rate=criticals / total if total > 0 else 0,
            block_accuracy=correct_blocks / len(blocks) if blocks else 1.0,
            recovery_success_rate=successful_recoveries / len(recoveries) if recoveries else 1.0,
            total_executions=total,
        )
    
    def should_pause_rollout(self, agent_id: str) -> bool:
        """
        判断是否应该暂停 rollout
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否应该暂停
        """
        summary = self.summarize(agent_id)
        
        # critical_rate 超阈值
        if summary.critical_rate > self.CRITICAL_RATE_THRESHOLD:
            return True
        
        # writeback_success_rate 降低
        if summary.writeback_success_rate < self.WRITEBACK_SUCCESS_THRESHOLD:
            return True
        
        return False
    
    def is_healthy_for_rollout(self, agent_id: str) -> bool:
        """
        判断是否健康可以 rollout
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否健康
        """
        summary = self.summarize(agent_id)
        
        return (
            summary.cold_start_success_rate >= 1.0 and
            summary.writeback_success_rate >= 1.0 and
            summary.critical_rate <= self.CRITICAL_RATE_THRESHOLD and
            summary.warning_rate <= self.WARNING_RATE_THRESHOLD
        )
    
    def get_rollout_gating_report(self, agent_id: str) -> Dict[str, Any]:
        """
        获取 rollout gating 报告
        
        Args:
            agent_id: Agent ID
        
        Returns:
            报告字典
        """
        summary = self.summarize(agent_id)
        
        checks = {
            "cold_start_success_rate": {
                "value": summary.cold_start_success_rate,
                "threshold": 1.0,
                "pass": summary.cold_start_success_rate >= 1.0,
            },
            "writeback_success_rate": {
                "value": summary.writeback_success_rate,
                "threshold": 1.0,
                "pass": summary.writeback_success_rate >= 1.0,
            },
            "critical_rate": {
                "value": summary.critical_rate,
                "threshold": self.CRITICAL_RATE_THRESHOLD,
                "pass": summary.critical_rate <= self.CRITICAL_RATE_THRESHOLD,
            },
            "warning_rate": {
                "value": summary.warning_rate,
                "threshold": self.WARNING_RATE_THRESHOLD,
                "pass": summary.warning_rate <= self.WARNING_RATE_THRESHOLD,
            },
        }
        
        all_passed = all(c["pass"] for c in checks.values())
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "can_rollout": all_passed,
            "checks": checks,
            "summary": summary.to_dict(),
        }
