"""
Real Executor Factory - 真实执行器工厂

为 autonomous_runner 提供真实执行能力。
"""

from typing import Optional
from runtime.step_executor import StepExecutor


def create_real_executor_factory(slot_registry=None):
    """
    创建真实执行器工厂函数
    
    Args:
        slot_registry: slot 注册表（用于释放 slot）
    
    Returns:
        工厂函数
    """
    def factory(dossier):
        return RealExecutorAdapter(dossier, slot_registry)
    
    return factory


class RealExecutorAdapter:
    """
    真实执行器适配器
    
    将 StepExecutor 适配到 autonomous_runner 期望的接口。
    """
    
    def __init__(self, dossier, slot_registry=None):
        self.dossier = dossier
        self.slot_registry = slot_registry
        self.executor = StepExecutor(dossier)
    
    def execute_step(self, step_packet):
        """
        执行步骤
        
        Args:
            step_packet: 步骤执行包
            
        Returns:
            ExecutionResult
        """
        from runtime.minimal_executor import ExecutionResult
        
        # 使用真实执行器
        result = self.executor.execute_step(step_packet)
        
        # 保存 result.json（供依赖检查）
        import json
        result_path = self.dossier.steps_dir / step_packet["step_id"] / "result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with open(result_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        # 更新任务状态
        from datetime import datetime
        self.dossier.update_step_status(
            step_packet["step_id"],
            result.status,
            completed_at=datetime.utcnow().isoformat() + "Z" if result.status == "success" else None
        )
        
        # 追加 ledger
        self.dossier.append_ledger({
            "event": "step_executed",
            "step_id": step_packet["step_id"],
            "status": result.status,
            "executor": "step_executor",
            "exit_code": result.exit_code,
            "command": result.command,
        })
        
        # 释放 slot
        if self.slot_registry:
            for slot_id, slot in self.slot_registry.slots.items():
                if slot.task_id == self.dossier.task_id:
                    self.slot_registry.release_slot(slot_id, slot.worker_id, "completed")
                    break
        
        return result
