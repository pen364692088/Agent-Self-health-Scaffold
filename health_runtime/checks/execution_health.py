"""
Execution Health Checker

检查 Agent 执行链健康状态：
- 写回是否成功
- 执行状态是否正常
- 运行时是否可用

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import yaml
from datetime import datetime, timezone, timedelta

from health_runtime.health_checker import (
    HealthCheckResult,
    HealthStatus,
    HealthCategory,
    HealthConfig,
)


class ExecutionHealthChecker:
    """执行健康检查器"""
    
    def __init__(self, config: HealthConfig):
        self.config = config
        self.memory_root = config.project_root / "memory" / "agents" / config.agent_id
    
    def check(self) -> HealthCheckResult:
        """执行执行健康检查"""
        issues: List[str] = []
        details: Dict[str, Any] = {}
        
        # 1. 检查执行状态文件
        execution_path = self.memory_root / "execution_state.yaml"
        
        if not execution_path.exists():
            issues.append("execution_state.yaml not found")
            return HealthCheckResult(
                category=HealthCategory.EXECUTION,
                status=HealthStatus.CRITICAL,
                message="Execution state not initialized",
                details={},
                issues=issues,
            )
        
        # 2. 解析执行状态
        try:
            with open(execution_path, "r") as f:
                state = yaml.safe_load(f) or {}
        except Exception as e:
            issues.append(f"Failed to parse execution_state: {e}")
            return HealthCheckResult(
                category=HealthCategory.EXECUTION,
                status=HealthStatus.CRITICAL,
                message="Failed to parse execution state",
                details={"error": str(e)},
                issues=issues,
            )
        
        details["status"] = state.get("status", "unknown")
        details["task_id"] = state.get("task_id")
        details["step"] = state.get("step")
        
        # 3. 检查 agent_id 匹配
        if state.get("agent_id") != self.config.agent_id:
            issues.append(f"Execution state agent_id mismatch: expected {self.config.agent_id}, got {state.get('agent_id')}")
        
        # 4. 检查时间戳（是否过期）
        timestamp_str = state.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                age = datetime.now(timezone.utc) - timestamp
                
                details["state_age_hours"] = age.total_seconds() / 3600
                
                # 超过 24 小时未更新视为 warning
                if age > timedelta(hours=24):
                    issues.append(f"Execution state stale: {age.total_seconds() / 3600:.1f} hours old")
            except Exception:
                issues.append("Invalid timestamp in execution_state")
        
        # 5. 检查写回能力
        writeback_ok = self._test_writeback(state)
        details["writeback_ok"] = writeback_ok
        
        if not writeback_ok:
            issues.append("State writeback test failed")
        
        # 6. 检查运行时模块
        runtime_available = self._check_runtime_modules()
        details["runtime_modules_available"] = runtime_available
        
        if not runtime_available:
            issues.append("Runtime modules not available")
        
        # 确定状态
        if "Failed to parse" in str(issues) or not writeback_ok:
            status = HealthStatus.CRITICAL
            message = "Execution critical: state parse/writeback failed"
        elif issues:
            status = HealthStatus.WARNING
            message = f"Execution warning: {issues[0]}"
        else:
            status = HealthStatus.HEALTHY
            message = "Execution healthy: state valid and writeback ok"
        
        return HealthCheckResult(
            category=HealthCategory.EXECUTION,
            status=status,
            message=message,
            details=details,
            issues=issues,
        )
    
    def _test_writeback(self, state: Dict[str, Any]) -> bool:
        """测试写回能力"""
        try:
            import tempfile
            import shutil
            
            execution_path = self.memory_root / "execution_state.yaml"
            
            # 备份原文件
            backup_path = execution_path.with_suffix(".yaml.bak")
            shutil.copy(execution_path, backup_path)
            
            # 尝试写入
            state["_health_check_timestamp"] = datetime.now(timezone.utc).isoformat()
            with open(execution_path, "w") as f:
                yaml.dump(state, f)
            
            # 恢复原文件
            shutil.move(backup_path, execution_path)
            
            return True
            
        except Exception:
            return False
    
    def _check_runtime_modules(self) -> bool:
        """检查运行时模块是否可用"""
        try:
            import sys
            sys.path.insert(0, str(self.config.project_root))
            
            from execution_runtime.preflight import PreflightChecker
            from execution_runtime.mutation_guard import MutationGuard
            
            return True
        except ImportError:
            return False
