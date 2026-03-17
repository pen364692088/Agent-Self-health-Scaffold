#!/usr/bin/env python3
"""
Lifecycle Hooks

统一生命周期触发点：
- 启动后
- 任务前
- 任务后
- 定期巡检

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


class HookPoint(str, Enum):
    """触发点"""
    AFTER_STARTUP = "after_startup"
    BEFORE_TASK = "before_task"
    AFTER_TASK = "after_task"
    PERIODIC_CHECK = "periodic_check"


@dataclass
class HookResult:
    """钩子执行结果"""
    hook_point: HookPoint
    agent_id: str
    success: bool
    actions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


class LifecycleHooks:
    """
    生命周期钩子
    
    统一管理 Agent 的生命周期触发点。
    """
    
    def __init__(self, agent_id: str, project_root: Path):
        self.agent_id = agent_id
        self.project_root = project_root
        self.memory_root = project_root / "memory" / "agents" / agent_id
    
    def after_startup(self) -> HookResult:
        """
        启动后钩子
        
        确保记忆恢复、规则加载、repo/path/canonical guard 已成立。
        """
        result = HookResult(
            hook_point=HookPoint.AFTER_STARTUP,
            agent_id=self.agent_id,
            success=True,
        )
        
        # 1. Session Bootstrap
        try:
            from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
            
            config = BootstrapConfig(
                agent_id=self.agent_id,
                memory_root=self.memory_root,
            )
            
            bootstrap = SessionBootstrap(config)
            bootstrap_result = bootstrap.run()
            
            if bootstrap_result.success:
                result.actions.append("session_bootstrap: success")
                result.data["rules_loaded"] = bootstrap_result.instruction_rules is not None
            else:
                result.errors.append(f"session_bootstrap: failed - {bootstrap_result.errors}")
                result.success = False
                
        except Exception as e:
            result.errors.append(f"session_bootstrap: error - {e}")
            result.success = False
        
        # 2. Instruction Rules Resolve
        try:
            from core.instruction_rules_merger import InstructionRulesMerger
            
            merger = InstructionRulesMerger(self.project_root)
            merge_result = merger.merge(self.agent_id)
            
            result.actions.append("instruction_rules: resolved")
            result.data["hard_constraints"] = merge_result.merge_summary.get("hard_constraints", 0)
            
        except Exception as e:
            result.errors.append(f"instruction_rules: error - {e}")
        
        # 3. Repo/Path Guard
        try:
            from execution_runtime.canonical_guard import CanonicalGuard, CanonicalConfig
            
            config = CanonicalConfig(
                agent_id=self.agent_id,
                canonical_repo=self.project_root,
            )
            
            guard = CanonicalGuard(config)
            guard_result = guard.verify()
            
            if guard_result.valid:
                result.actions.append("canonical_guard: verified")
            else:
                result.warnings.append(f"canonical_guard: {guard_result.message}")
                
        except Exception as e:
            result.errors.append(f"canonical_guard: error - {e}")
        
        # 记录钩子执行
        self._log_hook(result)
        
        return result
    
    def before_task(self, task_id: str, task_context: Optional[Dict] = None) -> HookResult:
        """
        任务前钩子
        
        确保 preflight、mutation guard、instruction rules 已命中。
        """
        result = HookResult(
            hook_point=HookPoint.BEFORE_TASK,
            agent_id=self.agent_id,
            success=True,
        )
        
        result.data["task_id"] = task_id
        
        # 1. Preflight Check
        try:
            from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
            
            config = PreflightConfig(
                agent_id=self.agent_id,
                checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
                canonical_repo=self.project_root,
            )
            
            checker = PreflightChecker(config)
            preflight_result = checker.check_all()
            
            if preflight_result.success:
                result.actions.append("preflight: passed")
            else:
                failed = [c.check.value for c in preflight_result.get_failed_checks()]
                result.actions.append(f"preflight: warnings - {failed}")
                
        except Exception as e:
            result.errors.append(f"preflight: error - {e}")
        
        # 2. Mutation Guard
        try:
            from execution_runtime.mutation_guard import MutationGuard, MutationConfig
            
            config = MutationConfig(
                agent_id=self.agent_id,
                protected_paths=[self.project_root / ".git"],
            )
            
            guard = MutationGuard(config)
            result.data["mutation_guard_ready"] = True
            result.actions.append("mutation_guard: ready")
            
        except Exception as e:
            result.errors.append(f"mutation_guard: error - {e}")
        
        # 3. Instruction Rules Check
        try:
            from core.instruction_rules_merger import InstructionRulesMerger
            
            merger = InstructionRulesMerger(self.project_root)
            merge_result = merger.merge(self.agent_id)
            
            result.data["active_rules"] = merge_result.merge_summary.get("workflow_rules", 0)
            result.actions.append("instruction_rules: checked")
            
        except Exception as e:
            result.errors.append(f"instruction_rules: error - {e}")
        
        # 记录钩子执行
        self._log_hook(result)
        
        return result
    
    def after_task(self, task_id: str, task_result: Optional[Dict] = None) -> HookResult:
        """
        任务后钩子
        
        确保写回、receipt、health 判定完成。
        """
        result = HookResult(
            hook_point=HookPoint.AFTER_TASK,
            agent_id=self.agent_id,
            success=True,
        )
        
        result.data["task_id"] = task_id
        result.data["task_result"] = task_result
        
        # 1. Memory Writeback
        try:
            from memory_runtime.execution_state_manager import ExecutionStateManager
            
            manager = ExecutionStateManager(
                agent_id=self.agent_id,
                memory_root=self.memory_root,
            )
            
            manager.save(
                task_id=task_id,
                status="completed",
                step="after_task_hook",
            )
            
            result.actions.append("writeback: success")
            
        except Exception as e:
            result.errors.append(f"writeback: error - {e}")
            result.success = False
        
        # 2. Health Check
        try:
            from health_runtime.health_checker import HealthChecker, HealthConfig
            
            config = HealthConfig(
                agent_id=self.agent_id,
                project_root=self.project_root,
            )
            
            checker = HealthChecker(config)
            health_result = checker.check_all()
            
            result.data["health_status"] = health_result.overall_status.value
            result.actions.append(f"health_check: {health_result.overall_status.value}")
            
            # 3. Health Action
            from runtime.health_action_matrix import HealthActionMatrix
            
            matrix = HealthActionMatrix(self.project_root)
            decision = matrix.decide(health_result.overall_status.value)
            
            result.data["health_action"] = decision.action.value
            result.data["allow_continue"] = decision.allow_continue
            
            if decision.require_intervention:
                result.actions.append(f"health_action: {decision.action.value}")
                matrix.execute(decision, self.agent_id)
                
        except Exception as e:
            result.errors.append(f"health_check: error - {e}")
        
        # 4. Receipt
        try:
            receipt = {
                "receipt_id": f"{self.agent_id}_{task_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "agent_id": self.agent_id,
                "task_id": task_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hook_result": result.actions,
            }
            
            receipts_dir = self.project_root / "receipts"
            receipts_dir.mkdir(exist_ok=True)
            
            receipt_path = receipts_dir / f"{receipt['receipt_id']}.json"
            with open(receipt_path, "w") as f:
                json.dump(receipt, f, indent=2)
            
            result.data["receipt_id"] = receipt["receipt_id"]
            result.actions.append("receipt: generated")
            
        except Exception as e:
            result.errors.append(f"receipt: error - {e}")
        
        # 记录钩子执行
        self._log_hook(result)
        
        return result
    
    def periodic_check(self) -> HookResult:
        """
        定期巡检钩子
        
        发现：记忆链断裂、状态漂移、repo drift、evidence 缺失、执行链异常。
        """
        result = HookResult(
            hook_point=HookPoint.PERIODIC_CHECK,
            agent_id=self.agent_id,
            success=True,
        )
        
        # 1. Full Health Check
        try:
            from health_runtime.health_checker import HealthChecker, HealthConfig
            
            config = HealthConfig(
                agent_id=self.agent_id,
                project_root=self.project_root,
            )
            
            checker = HealthChecker(config)
            health_result = checker.check_all()
            
            result.data["health_status"] = health_result.overall_status.value
            
            # 收集所有问题
            all_issues = []
            for check_name, check_result in health_result.checks.items():
                if check_result.issues:
                    all_issues.extend(check_result.issues)
            
            result.data["issues_count"] = len(all_issues)
            result.data["issues"] = all_issues[:10]  # 最多记录 10 个
            
            if health_result.overall_status.value == "healthy":
                result.actions.append("health: healthy")
            else:
                result.actions.append(f"health: {health_result.overall_status.value} ({len(all_issues)} issues)")
                
        except Exception as e:
            result.errors.append(f"health_check: error - {e}")
            result.success = False
        
        # 2. Check Memory Chain
        try:
            # 检查关键文件是否存在
            critical_files = [
                self.memory_root / "instruction_rules.yaml",
                self.memory_root / "handoff_state.yaml",
                self.memory_root / "execution_state.yaml",
            ]
            
            missing = [str(f.name) for f in critical_files if not f.exists()]
            
            if missing:
                result.data["memory_chain_broken"] = True
                result.errors.append(f"Memory chain broken: missing {missing}")
                result.success = False
            else:
                result.actions.append("memory_chain: intact")
                
        except Exception as e:
            result.errors.append(f"memory_chain: error - {e}")
        
        # 3. Check Evidence
        try:
            receipts_dir = self.project_root / "receipts"
            if receipts_dir.exists():
                recent_receipts = list(receipts_dir.glob(f"{self.agent_id}_*.json"))
                result.data["recent_receipts"] = len(recent_receipts)
                result.actions.append(f"evidence: {len(recent_receipts)} receipts")
            else:
                result.data["evidence_missing"] = True
                result.actions.append("evidence: no receipts yet")
                
        except Exception as e:
            result.errors.append(f"evidence: error - {e}")
        
        # 记录钩子执行
        self._log_hook(result)
        
        # 保存巡检报告
        self._save_periodic_report(result)
        
        return result
    
    def _log_hook(self, result: HookResult) -> None:
        """记录钩子执行"""
        try:
            logs_dir = self.project_root / "logs" / "lifecycle_hooks"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            log_path = logs_dir / f"{result.hook_point.value}_{self.agent_id}_{timestamp}.json"
            
            log_entry = {
                "hook_point": result.hook_point.value,
                "agent_id": result.agent_id,
                "success": result.success,
                "actions": result.actions,
                "errors": result.errors,
                "data": result.data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            with open(log_path, "w") as f:
                json.dump(log_entry, f, indent=2)
                
        except Exception:
            pass
    
    def _save_periodic_report(self, result: HookResult) -> None:
        """保存巡检报告"""
        try:
            reports_dir = self.project_root / "reports" / "periodic"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"periodic_{self.agent_id}_{timestamp}.json"
            
            with open(report_path, "w") as f:
                json.dump({
                    "hook_point": result.hook_point.value,
                    "agent_id": result.agent_id,
                    "success": result.success,
                    "data": result.data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }, f, indent=2)
                
        except Exception:
            pass
