"""
Minimal Step Executor - 最小执行器 Stub

为 B0-1.5 最小可运行链提供执行能力。
当前实现：模拟执行，记录状态变化。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ExecutionResult:
    """执行结果"""
    step_id: str
    status: str  # success, failed, blocked
    message: str = ""
    outputs: Dict[str, Any] = None
    error: Optional[Dict[str, Any]] = None  # 兼容 autonomous_runner 的期望
    
    def __post_init__(self):
        if self.outputs is None:
            self.outputs = {}
        if self.error is None and self.status != "success":
            self.error = {"message": self.message}


class MinimalStepExecutor:
    """
    最小步骤执行器
    
    不执行实际操作，只更新状态并生成证据。
    用于验证 autonomous_runner 推进链路。
    """
    
    def __init__(self, dossier):
        self.dossier = dossier
        self.evidence_dir = dossier.evidence_dir
        self.steps_dir = dossier.steps_dir
    
    def execute_step(self, step_packet: Dict[str, Any]) -> ExecutionResult:
        """
        执行步骤（模拟）
        
        Args:
            step_packet: 步骤执行包
            
        Returns:
            ExecutionResult
        """
        step_id = step_packet.get("step_id", "unknown")
        execution_type = step_packet.get("execution_type", "manual")
        
        # 创建证据目录
        evidence_path = Path(step_packet.get("evidence_path", self.evidence_dir / step_id))
        evidence_path.mkdir(parents=True, exist_ok=True)
        
        # 生成执行证据
        evidence = {
            "step_id": step_id,
            "execution_type": execution_type,
            "executed_at": datetime.utcnow().isoformat() + "Z",
            "status": "success",
            "message": f"[MINIMAL EXECUTOR] Step {step_id} executed (simulated)",
            "inputs": step_packet.get("inputs", {}),
            "outputs": {
                "evidence_file": str(evidence_path / "execution.json"),
            }
        }
        
        # 写入证据
        with open(evidence_path / "execution.json", 'w') as f:
            json.dump(evidence, f, indent=2)
        
        # 更新任务状态
        self.dossier.update_step_status(
            step_id, 
            "success",
            completed_at=datetime.utcnow().isoformat() + "Z"
        )
        
        # 追加 ledger
        self.dossier.append_ledger({
            "event": "step_executed",
            "step_id": step_id,
            "status": "success",
            "executor": "minimal_executor",
        })
        
        return ExecutionResult(
            step_id=step_id,
            status="success",
            message=f"Step {step_id} executed successfully (simulated)",
            outputs=evidence["outputs"]
        )


def create_executor_factory():
    """
    创建执行器工厂函数
    
    Returns:
        工厂函数
    """
    def factory(dossier):
        return MinimalStepExecutor(dossier)
    
    return factory
