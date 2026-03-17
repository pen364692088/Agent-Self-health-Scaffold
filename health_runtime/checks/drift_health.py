"""
Drift Health Checker

检查 Agent 漂移风险：
- repo drift: 工作目录是否漂移
- state drift: 状态文件是否漂移
- context drift: 上下文是否漂移

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import yaml
import subprocess

from health_runtime.health_checker import (
    HealthCheckResult,
    HealthStatus,
    HealthCategory,
    HealthConfig,
)


class DriftHealthChecker:
    """漂移健康检查器"""
    
    def __init__(self, config: HealthConfig):
        self.config = config
        self.project_root = config.project_root
        self.memory_root = config.project_root / "memory" / "agents" / config.agent_id
    
    def check(self) -> HealthCheckResult:
        """执行漂移健康检查"""
        issues: List[str] = []
        details: Dict[str, Any] = {}
        
        # 1. 检查 repo drift
        repo_drift = self._check_repo_drift()
        details["repo_drift"] = repo_drift
        
        if repo_drift.get("has_drift"):
            issues.append(f"Repo drift detected: {repo_drift.get('message', 'unknown')}")
        
        # 2. 检查 state drift
        state_drift = self._check_state_drift()
        details["state_drift"] = state_drift
        
        if state_drift.get("has_drift"):
            issues.append(f"State drift detected: {state_drift.get('message', 'unknown')}")
        
        # 3. 检查 context drift
        context_drift = self._check_context_drift()
        details["context_drift"] = context_drift
        
        if context_drift.get("has_drift"):
            issues.append(f"Context drift detected: {context_drift.get('message', 'unknown')}")
        
        # 确定状态
        if any(d.get("has_drift") and d.get("severity") == "critical" for d in [repo_drift, state_drift, context_drift]):
            status = HealthStatus.CRITICAL
            message = "Drift critical: severe drift detected"
        elif issues:
            status = HealthStatus.WARNING
            message = f"Drift warning: {len(issues)} drift issues"
        else:
            status = HealthStatus.HEALTHY
            message = "Drift healthy: no drift detected"
        
        return HealthCheckResult(
            category=HealthCategory.DRIFT,
            status=status,
            message=message,
            details=details,
            issues=issues,
        )
    
    def _check_repo_drift(self) -> Dict[str, Any]:
        """检查仓库漂移"""
        result = {"has_drift": False, "message": "", "severity": "none"}
        
        try:
            # 检查是否在 git 仓库内
            git_dir = self.project_root / ".git"
            if not git_dir.exists():
                result["has_drift"] = True
                result["message"] = "Not a git repository"
                result["severity"] = "warning"
                return result
            
            # 检查是否有未提交的变更
            result_git = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result_git.returncode == 0:
                changes = result_git.stdout.strip()
                if changes:
                    result["has_drift"] = True
                    result["message"] = f"Uncommitted changes: {len(changes.splitlines())} files"
                    result["severity"] = "warning"
                    result["uncommitted_files"] = len(changes.splitlines())
            
            # 检查当前分支
            result_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result_branch.returncode == 0:
                result["current_branch"] = result_branch.stdout.strip()
        
        except Exception as e:
            result["has_drift"] = True
            result["message"] = f"Git check failed: {e}"
            result["severity"] = "warning"
        
        return result
    
    def _check_state_drift(self) -> Dict[str, Any]:
        """检查状态漂移"""
        result = {"has_drift": False, "message": "", "severity": "none"}
        
        # 检查 SESSION-STATE.md 是否存在
        session_state_path = self.project_root / "SESSION-STATE.md"
        if not session_state_path.exists():
            result["has_drift"] = True
            result["message"] = "SESSION-STATE.md not found"
            result["severity"] = "warning"
            return result
        
        # 检查 execution_state 与 SESSION-STATE 是否一致
        execution_path = self.memory_root / "execution_state.yaml"
        if execution_path.exists():
            try:
                with open(execution_path, "r") as f:
                    exec_state = yaml.safe_load(f) or {}
                
                # 简单检查：状态是否为 error
                if exec_state.get("status") == "error":
                    result["has_drift"] = True
                    result["message"] = "Execution state in error"
                    result["severity"] = "critical"
            except Exception as e:
                result["has_drift"] = True
                result["message"] = f"Failed to check execution state: {e}"
                result["severity"] = "warning"
        
        return result
    
    def _check_context_drift(self) -> Dict[str, Any]:
        """检查上下文漂移"""
        result = {"has_drift": False, "message": "", "severity": "none"}
        
        # 检查 handoff 是否存在且有效
        handoff_path = self.memory_root / "handoff_state.yaml"
        if not handoff_path.exists():
            result["has_drift"] = True
            result["message"] = "No handoff state - potential context loss"
            result["severity"] = "warning"
            return result
        
        try:
            with open(handoff_path, "r") as f:
                handoff = yaml.safe_load(f) or {}
            
            # 检查是否有 blocker 未处理
            blockers = handoff.get("blockers", [])
            if blockers:
                result["has_drift"] = True
                result["message"] = f"Unhandled blockers: {len(blockers)}"
                result["severity"] = "warning"
                result["blockers"] = blockers
            
            # 检查 objective 是否为空
            if not handoff.get("objective"):
                result["has_drift"] = True
                result["message"] = "No objective in handoff"
                result["severity"] = "warning"
        
        except Exception as e:
            result["has_drift"] = True
            result["message"] = f"Failed to check handoff: {e}"
            result["severity"] = "warning"
        
        return result
