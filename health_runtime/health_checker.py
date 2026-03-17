"""
Health Checker - Core Health Monitoring

核心健康检查器，整合四类健康检查。

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum
from datetime import datetime, timezone
import json


class HealthStatus(str, Enum):
    """健康状态分级"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthCategory(str, Enum):
    """健康检查类别"""
    MEMORY = "memory_health"
    EXECUTION = "execution_health"
    DRIFT = "drift_health"
    INTEGRITY = "integrity_health"


@dataclass
class HealthCheckResult:
    """单项健康检查结果"""
    category: HealthCategory
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class HealthReport:
    """
    健康报告
    
    包含所有类别的检查结果和综合状态。
    """
    agent_id: str
    timestamp: str
    overall_status: HealthStatus
    checks: Dict[str, HealthCheckResult]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "checks": {
                k: {
                    "category": v.category.value,
                    "status": v.status.value,
                    "message": v.message,
                    "details": v.details,
                    "issues": v.issues,
                }
                for k, v in self.checks.items()
            },
            "summary": self.summary,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def save(self, path: Path) -> None:
        """保存到文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())


@dataclass
class HealthConfig:
    """健康检查配置"""
    agent_id: str
    project_root: Path
    check_memory: bool = True
    check_execution: bool = True
    check_drift: bool = True
    check_integrity: bool = True


class HealthChecker:
    """
    核心健康检查器
    
    整合四类健康检查，输出结构化报告。
    """
    
    def __init__(self, config: HealthConfig):
        self.config = config
        self.project_root = config.project_root
        self.memory_root = config.project_root / "memory" / "agents" / config.agent_id
    
    def check_all(self) -> HealthReport:
        """
        执行所有健康检查
        
        Returns:
            HealthReport
        """
        checks: Dict[str, HealthCheckResult] = {}
        issues: List[str] = []
        
        # 1. Memory Health
        if self.config.check_memory:
            from health_runtime.checks.memory_health import MemoryHealthChecker
            
            checker = MemoryHealthChecker(self.config)
            result = checker.check()
            checks["memory_health"] = result
            issues.extend(result.issues)
        
        # 2. Execution Health
        if self.config.check_execution:
            from health_runtime.checks.execution_health import ExecutionHealthChecker
            
            checker = ExecutionHealthChecker(self.config)
            result = checker.check()
            checks["execution_health"] = result
            issues.extend(result.issues)
        
        # 3. Drift Health
        if self.config.check_drift:
            from health_runtime.checks.drift_health import DriftHealthChecker
            
            checker = DriftHealthChecker(self.config)
            result = checker.check()
            checks["drift_health"] = result
            issues.extend(result.issues)
        
        # 4. Integrity Health
        if self.config.check_integrity:
            from health_runtime.checks.integrity_health import IntegrityHealthChecker
            
            checker = IntegrityHealthChecker(self.config)
            result = checker.check()
            checks["integrity_health"] = result
            issues.extend(result.issues)
        
        # 确定综合状态
        overall_status = self._determine_overall_status(checks)
        
        # 生成摘要
        summary = self._generate_summary(checks, overall_status)
        
        return HealthReport(
            agent_id=self.config.agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_status=overall_status,
            checks=checks,
            summary=summary,
        )
    
    def _determine_overall_status(self, checks: Dict[str, HealthCheckResult]) -> HealthStatus:
        """确定综合状态"""
        if not checks:
            return HealthStatus.WARNING
        
        statuses = [c.status for c in checks.values()]
        
        # 有 critical 则 overall critical
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        
        # 有 warning 则 overall warning
        if HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        
        return HealthStatus.HEALTHY
    
    def _generate_summary(
        self,
        checks: Dict[str, HealthCheckResult],
        overall_status: HealthStatus,
    ) -> str:
        """生成摘要"""
        lines = [
            f"Health Report: {self.config.agent_id}",
            f"Overall: {overall_status.value.upper()}",
            "",
        ]
        
        for name, result in checks.items():
            status_icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.WARNING: "⚠️",
                HealthStatus.CRITICAL: "❌",
            }.get(result.status, "❓")
            
            lines.append(f"{status_icon} {name}: {result.message}")
            
            if result.issues:
                for issue in result.issues[:3]:
                    lines.append(f"  - {issue}")
        
        return "\n".join(lines)
