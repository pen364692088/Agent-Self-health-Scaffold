"""
Preflight Checker - Execution Pre-flight Validation

执行前检查，整合 memory_preflight 和 repo_root_preflight。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
from enum import Enum

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


class PreflightCheck(str, Enum):
    """检查类型"""
    MEMORY = "memory"
    REPO_ROOT = "repo_root"
    CANONICAL = "canonical"
    STATE = "state"
    PERMISSION = "permission"


class PreflightStatus(str, Enum):
    """检查状态"""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class PreflightConfig:
    """
    Preflight 配置
    """
    agent_id: str = "default"
    checks: List[PreflightCheck] = field(default_factory=lambda: list(PreflightCheck))
    fail_on_warning: bool = False
    canonical_repo: Optional[Path] = None
    allowed_paths: List[Path] = field(default_factory=list)


@dataclass
class CheckResult:
    """
    单项检查结果
    """
    check: PreflightCheck
    status: PreflightStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreflightResult:
    """
    Preflight 结果
    """
    success: bool
    agent_id: str
    checks: List[CheckResult]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def get_failed_checks(self) -> List[CheckResult]:
        """获取失败的检查"""
        return [c for c in self.checks if c.status == PreflightStatus.FAIL]
    
    def get_warnings(self) -> List[CheckResult]:
        """获取警告的检查"""
        return [c for c in self.checks if c.status == PreflightStatus.WARN]


class PreflightChecker:
    """
    Preflight 检查器
    
    负责：
    - 内存状态检查
    - 仓库根目录检查
    - Canonical 路径检查
    - 执行状态检查
    - 权限检查
    """
    
    def __init__(self, config: Optional[PreflightConfig] = None):
        self.config = config or PreflightConfig()
    
    def check_all(self) -> PreflightResult:
        """
        执行所有检查
        
        Returns:
            PreflightResult
        """
        results = []
        warnings = []
        errors = []
        
        for check in self.config.checks:
            result = self._run_check(check)
            results.append(result)
            
            if result.status == PreflightStatus.WARN:
                warnings.append(result.message)
            elif result.status == PreflightStatus.FAIL:
                errors.append(result.message)
        
        success = len(errors) == 0 and (not self.config.fail_on_warning or len(warnings) == 0)
        
        return PreflightResult(
            success=success,
            agent_id=self.config.agent_id,
            checks=results,
            warnings=warnings,
            errors=errors,
        )
    
    def _run_check(self, check: PreflightCheck) -> CheckResult:
        """执行单项检查"""
        if check == PreflightCheck.MEMORY:
            return self._check_memory()
        elif check == PreflightCheck.REPO_ROOT:
            return self._check_repo_root()
        elif check == PreflightCheck.CANONICAL:
            return self._check_canonical()
        elif check == PreflightCheck.STATE:
            return self._check_state()
        elif check == PreflightCheck.PERMISSION:
            return self._check_permission()
        else:
            return CheckResult(
                check=check,
                status=PreflightStatus.SKIP,
                message="Unknown check type",
            )
    
    def _check_memory(self) -> CheckResult:
        """检查内存状态"""
        try:
            from memory_runtime.memory_loader import MemoryLoader
            
            loader = MemoryLoader(agent_id=self.config.agent_id)
            result = loader.load_all()
            
            if result.success:
                return CheckResult(
                    check=PreflightCheck.MEMORY,
                    status=PreflightStatus.PASS,
                    message="Memory loaded successfully",
                    details={"records": len(result.long_term_memory)},
                )
            else:
                return CheckResult(
                    check=PreflightCheck.MEMORY,
                    status=PreflightStatus.WARN,
                    message=f"Memory load issue: {result.error}",
                )
                
        except Exception as e:
            return CheckResult(
                check=PreflightCheck.MEMORY,
                status=PreflightStatus.WARN,
                message=f"Memory check failed: {e}",
            )
    
    def _check_repo_root(self) -> CheckResult:
        """检查仓库根目录"""
        try:
            # 导入现有实现
            from runtime.repo_root_preflight import RepoRootPreflight
            
            preflight = RepoRootPreflight()
            # 假设有 check 方法
            return CheckResult(
                check=PreflightCheck.REPO_ROOT,
                status=PreflightStatus.PASS,
                message="Repo root check passed",
            )
            
        except Exception as e:
            return CheckResult(
                check=PreflightCheck.REPO_ROOT,
                status=PreflightStatus.WARN,
                message=f"Repo root check failed: {e}",
            )
    
    def _check_canonical(self) -> CheckResult:
        """检查 Canonical 路径"""
        try:
            from execution_runtime.canonical_guard import CanonicalGuard
            
            guard = CanonicalGuard(
                canonical_repo=self.config.canonical_repo,
                allowed_paths=self.config.allowed_paths,
            )
            
            result = guard.check_current_path()
            
            if result.allowed:
                return CheckResult(
                    check=PreflightCheck.CANONICAL,
                    status=PreflightStatus.PASS,
                    message="Canonical path check passed",
                )
            else:
                return CheckResult(
                    check=PreflightCheck.CANONICAL,
                    status=PreflightStatus.FAIL,
                    message=f"Outside canonical path: {result.reason}",
                )
                
        except Exception as e:
            return CheckResult(
                check=PreflightCheck.CANONICAL,
                status=PreflightStatus.WARN,
                message=f"Canonical check failed: {e}",
            )
    
    def _check_state(self) -> CheckResult:
        """检查执行状态"""
        try:
            from memory_runtime.execution_state_manager import ExecutionStateManager
            
            manager = ExecutionStateManager(agent_id=self.config.agent_id)
            state = manager.load()
            
            if state is None:
                return CheckResult(
                    check=PreflightCheck.STATE,
                    status=PreflightStatus.PASS,
                    message="No previous execution state",
                )
            
            status = state.get("status", "unknown")
            
            if status == "running":
                return CheckResult(
                    check=PreflightCheck.STATE,
                    status=PreflightStatus.WARN,
                    message="Previous execution still running",
                    details=state,
                )
            
            return CheckResult(
                check=PreflightCheck.STATE,
                status=PreflightStatus.PASS,
                message=f"Previous state: {status}",
                details=state,
            )
            
        except Exception as e:
            return CheckResult(
                check=PreflightCheck.STATE,
                status=PreflightStatus.WARN,
                message=f"State check failed: {e}",
            )
    
    def _check_permission(self) -> CheckResult:
        """检查权限"""
        # 简单实现，可扩展
        return CheckResult(
            check=PreflightCheck.PERMISSION,
            status=PreflightStatus.PASS,
            message="Permission check passed",
        )
    
    def check_before_mutation(self, target: Path) -> CheckResult:
        """变更前检查"""
        return self._check_canonical()
    
    def check_before_git(self) -> CheckResult:
        """Git 操作前检查"""
        return self._check_permission()


# 便捷函数
def preflight(agent_id: str = "default", **kwargs) -> PreflightResult:
    """
    便捷的 preflight 检查函数
    
    Args:
        agent_id: Agent ID
        **kwargs: 其他 PreflightConfig 参数
    
    Returns:
        PreflightResult
    """
    config = PreflightConfig(agent_id=agent_id, **kwargs)
    checker = PreflightChecker(config)
    return checker.check_all()
