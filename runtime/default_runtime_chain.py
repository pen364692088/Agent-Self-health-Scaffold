#!/usr/bin/env python3
"""
Default Runtime Chain

所有已接入 Agent 的默认运行主链。不是"可选能力"，而是"默认运行路径"。

主链：
Agent Start → Session Bootstrap → Instruction Rules Resolve → 
Runtime Preflight → Task Runtime → Memory Writeback → 
Health Check → Receipt / Evidence

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from enum import Enum
from datetime import datetime, timezone
import json
import traceback


class ChainStage(str, Enum):
    """主链阶段"""
    SESSION_BOOTSTRAP = "session_bootstrap"
    INSTRUCTION_RULES = "instruction_rules"
    RUNTIME_PREFLIGHT = "runtime_preflight"
    TASK_RUNTIME = "task_runtime"
    MEMORY_WRITEBACK = "memory_writeback"
    HEALTH_CHECK = "health_check"
    RECEIPT = "receipt"


class ChainStatus(str, Enum):
    """链路状态"""
    SUCCESS = "success"
    WARNING = "warning"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class ChainResult:
    """链路执行结果"""
    agent_id: str
    status: ChainStatus
    stages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    receipt: Optional[Dict[str, Any]] = None
    health_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "stages": self.stages,
            "errors": self.errors,
            "warnings": self.warnings,
            "receipt": self.receipt,
            "health_action": self.health_action,
        }


class DefaultRuntimeChain:
    """
    默认运行主链
    
    所有 Agent 必须经过此链路才能执行任务。
    """
    
    def __init__(self, agent_id: str, project_root: Path):
        self.agent_id = agent_id
        self.project_root = project_root
        self.memory_root = project_root / "memory" / "agents" / agent_id
        
        # 链路结果
        self.result = ChainResult(agent_id=agent_id, status=ChainStatus.SUCCESS)
        
        # 阶段状态
        self.bootstrap_result = None
        self.rules_result = None
        self.preflight_result = None
        self.health_result = None
    
    def run(self, task_fn: Optional[Callable] = None, task_context: Optional[Dict] = None) -> ChainResult:
        """
        执行完整默认主链
        
        Args:
            task_fn: 可选的任务函数
            task_context: 任务上下文
        
        Returns:
            ChainResult
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Stage 1: Session Bootstrap
        if not self._run_session_bootstrap():
            self.result.status = ChainStatus.FAILED
            return self._finalize()
        
        # Stage 2: Instruction Rules Resolve
        if not self._run_instruction_rules():
            self.result.status = ChainStatus.FAILED
            return self._finalize()
        
        # Stage 3: Runtime Preflight
        preflight_ok = self._run_preflight()
        if not preflight_ok:
            self.result.status = ChainStatus.BLOCKED
            return self._finalize()
        
        # Stage 4: Task Runtime (if provided)
        if task_fn:
            if not self._run_task(task_fn, task_context):
                self.result.status = ChainStatus.FAILED
                return self._finalize()
        
        # Stage 5: Memory Writeback
        self._run_writeback()
        
        # Stage 6: Health Check
        self._run_health_check()
        
        # Stage 7: Receipt / Evidence
        self._run_receipt()
        
        return self._finalize()
    
    def _run_session_bootstrap(self) -> bool:
        """执行 Session Bootstrap"""
        stage_name = ChainStage.SESSION_BOOTSTRAP.value
        
        try:
            from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
            
            config = BootstrapConfig(
                agent_id=self.agent_id,
                memory_root=self.memory_root,
            )
            
            bootstrap = SessionBootstrap(config)
            self.bootstrap_result = bootstrap.run()
            
            self.result.stages[stage_name] = {
                "success": self.bootstrap_result.success,
                "rules_loaded": self.bootstrap_result.instruction_rules is not None,
                "errors": self.bootstrap_result.errors,
            }
            
            if not self.bootstrap_result.success:
                self.result.errors.append(f"Session bootstrap failed: {self.bootstrap_result.errors}")
                return False
            
            return True
            
        except Exception as e:
            self.result.errors.append(f"Session bootstrap error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
            return False
    
    def _run_instruction_rules(self) -> bool:
        """执行 Instruction Rules Resolve"""
        stage_name = ChainStage.INSTRUCTION_RULES.value
        
        try:
            from core.instruction_rules_merger import InstructionRulesMerger
            
            merger = InstructionRulesMerger(self.project_root)
            self.rules_result = merger.merge(self.agent_id)
            
            self.result.stages[stage_name] = {
                "success": True,
                "hard_constraints": self.rules_result.merge_summary.get("hard_constraints", 0),
                "workflow_rules": self.rules_result.merge_summary.get("workflow_rules", 0),
                "errors": self.rules_result.errors,
            }
            
            if self.rules_result.errors:
                self.result.warnings.extend(self.rules_result.errors)
            
            return True
            
        except Exception as e:
            self.result.errors.append(f"Instruction rules error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
            return False
    
    def _run_preflight(self) -> bool:
        """执行 Runtime Preflight"""
        stage_name = ChainStage.RUNTIME_PREFLIGHT.value
        
        try:
            from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
            
            config = PreflightConfig(
                agent_id=self.agent_id,
                checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
                canonical_repo=self.project_root,
            )
            
            checker = PreflightChecker(config)
            self.preflight_result = checker.check_all()
            
            failed = self.preflight_result.get_failed_checks()
            
            self.result.stages[stage_name] = {
                "success": self.preflight_result.success,
                "failed_checks": [c.check.value for c in failed],
            }
            
            # Preflight 失败不一定是 block，取决于检查类型
            if failed:
                self.result.warnings.append(f"Preflight warnings: {[c.message for c in failed]}")
            
            return True
            
        except Exception as e:
            self.result.warnings.append(f"Preflight error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
            return True  # Warning, not block
    
    def _run_task(self, task_fn: Callable, context: Optional[Dict] = None) -> bool:
        """执行任务"""
        stage_name = ChainStage.TASK_RUNTIME.value
        
        try:
            result = task_fn(context or {})
            
            self.result.stages[stage_name] = {
                "success": True,
                "result": str(result) if result else None,
            }
            
            return True
            
        except Exception as e:
            self.result.errors.append(f"Task error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
            return False
    
    def _run_writeback(self) -> None:
        """执行 Memory Writeback"""
        stage_name = ChainStage.MEMORY_WRITEBACK.value
        
        try:
            from memory_runtime.execution_state_manager import ExecutionStateManager
            
            manager = ExecutionStateManager(
                agent_id=self.agent_id,
                memory_root=self.memory_root,
            )
            
            # 更新执行状态
            manager.save(
                task_id=f"chain_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                status="chain_executed",
                step="completed",
            )
            
            self.result.stages[stage_name] = {"success": True}
            
        except Exception as e:
            self.result.warnings.append(f"Writeback error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
    
    def _run_health_check(self) -> None:
        """执行 Health Check"""
        stage_name = ChainStage.HEALTH_CHECK.value
        
        try:
            from health_runtime.health_checker import HealthChecker, HealthConfig
            
            config = HealthConfig(
                agent_id=self.agent_id,
                project_root=self.project_root,
            )
            
            checker = HealthChecker(config)
            self.health_result = checker.check_all()
            
            self.result.stages[stage_name] = {
                "success": True,
                "status": self.health_result.overall_status.value,
                "issues_count": sum(len(c.issues) for c in self.health_result.checks.values()),
            }
            
            # 设置 health action
            self.result.health_action = self._get_health_action()
            
            # 根据健康状态调整链路状态
            from health_runtime.health_checker import HealthStatus
            if self.health_result.overall_status == HealthStatus.CRITICAL:
                self.result.status = ChainStatus.BLOCKED
            elif self.health_result.overall_status == HealthStatus.WARNING:
                if self.result.status == ChainStatus.SUCCESS:
                    self.result.status = ChainStatus.WARNING
            
        except Exception as e:
            self.result.warnings.append(f"Health check error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
    
    def _get_health_action(self) -> str:
        """根据健康状态获取治理动作"""
        if not self.health_result:
            return "none"
        
        status = self.health_result.overall_status.value
        
        if status == "healthy":
            return "continue_with_evidence"
        elif status == "warning":
            return "continue_with_monitoring"
        elif status == "critical":
            return "block_and_recover"
        else:
            return "unknown"
    
    def _run_receipt(self) -> None:
        """生成 Receipt / Evidence"""
        stage_name = ChainStage.RECEIPT.value
        
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            receipt = {
                "receipt_id": f"{self.agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "agent_id": self.agent_id,
                "timestamp": timestamp,
                "chain_status": self.result.status.value,
                "stages_completed": list(self.result.stages.keys()),
                "errors": self.result.errors,
                "warnings": self.result.warnings,
                "health_action": self.result.health_action,
            }
            
            self.result.receipt = receipt
            
            # 保存 receipt
            receipts_dir = self.project_root / "receipts"
            receipts_dir.mkdir(exist_ok=True)
            
            receipt_path = receipts_dir / f"{receipt['receipt_id']}.json"
            with open(receipt_path, "w") as f:
                json.dump(receipt, f, indent=2)
            
            self.result.stages[stage_name] = {
                "success": True,
                "receipt_id": receipt["receipt_id"],
            }
            
        except Exception as e:
            self.result.warnings.append(f"Receipt error: {e}")
            self.result.stages[stage_name] = {"success": False, "error": str(e)}
    
    def _finalize(self) -> ChainResult:
        """完成链路"""
        return self.result


def run_default_chain(
    agent_id: str,
    project_root: Path,
    task_fn: Optional[Callable] = None,
    task_context: Optional[Dict] = None,
) -> ChainResult:
    """
    便捷函数：运行默认主链
    
    Args:
        agent_id: Agent ID
        project_root: 项目根目录
        task_fn: 可选的任务函数
        task_context: 任务上下文
    
    Returns:
        ChainResult
    """
    chain = DefaultRuntimeChain(agent_id, project_root)
    return chain.run(task_fn, task_context)
