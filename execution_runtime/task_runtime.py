"""
Task Runtime - Task Lifecycle Management

任务生命周期管理，封装 runtime/step_executor.py 的核心能力。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Awaitable
from pathlib import Path
import sys
import asyncio
from datetime import datetime, timezone

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入核心实现
from runtime.step_executor import StepExecutor


@dataclass
class TaskConfig:
    """
    任务配置
    """
    task_id: str
    agent_id: str = "default"
    max_steps: int = 100
    timeout_seconds: int = 3600
    enable_checkpoint: bool = True
    checkpoint_interval: int = 10
    enable_receipt: bool = True
    fail_fast: bool = False


@dataclass
class TaskResult:
    """
    任务结果
    """
    success: bool
    task_id: str
    steps_completed: int = 0
    steps_failed: int = 0
    output: Optional[str] = None
    error: Optional[str] = None
    receipt_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def duration_seconds(self) -> Optional[float]:
        """计算执行时长"""
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        return None


@dataclass
class StepResult:
    """
    步骤结果
    """
    step_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class TaskRuntime:
    """
    任务运行时
    
    负责：
    - 任务生命周期管理
    - 步骤执行
    - 检查点管理
    - 凭证生成
    """
    
    def __init__(self, config: TaskConfig):
        self.config = config
        self._steps: List[StepResult] = []
        self._started_at: Optional[str] = None
        self._completed_at: Optional[str] = None
        self._checkpoints: List[Dict[str, Any]] = []
    
    def start(self) -> str:
        """启动任务"""
        self._started_at = datetime.now(timezone.utc).isoformat()
        return self.config.task_id
    
    def complete(self, success: bool, output: Optional[str] = None, error: Optional[str] = None) -> TaskResult:
        """完成任务"""
        self._completed_at = datetime.now(timezone.utc).isoformat()
        
        result = TaskResult(
            success=success,
            task_id=self.config.task_id,
            steps_completed=len([s for s in self._steps if s.success]),
            steps_failed=len([s for s in self._steps if not s.success]),
            output=output,
            error=error,
            started_at=self._started_at,
            completed_at=self._completed_at,
        )
        
        # 生成凭证
        if self.config.enable_receipt:
            from execution_runtime.receipt import ReceiptManager
            receipt_manager = ReceiptManager()
            receipt = receipt_manager.create_receipt(result)
            result.receipt_id = receipt.receipt_id
        
        return result
    
    def add_step(self, step: StepResult):
        """添加步骤结果"""
        self._steps.append(step)
        
        # 检查点
        if self.config.enable_checkpoint and len(self._steps) % self.config.checkpoint_interval == 0:
            self._save_checkpoint()
    
    def _save_checkpoint(self):
        """保存检查点"""
        from memory_runtime.execution_state_manager import ExecutionStateManager
        
        manager = ExecutionStateManager(agent_id=self.config.agent_id)
        manager.save_checkpoint(
            checkpoint_name=f"task-{self.config.task_id}-step-{len(self._steps)}",
            state={
                "task_id": self.config.task_id,
                "steps_completed": len(self._steps),
                "steps": [s.__dict__ for s in self._steps],
            }
        )
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度"""
        return {
            "task_id": self.config.task_id,
            "total_steps": len(self._steps),
            "completed_steps": len([s for s in self._steps if s.success]),
            "failed_steps": len([s for s in self._steps if not s.success]),
            "started_at": self._started_at,
        }
    
    @classmethod
    def from_execution_state(cls, agent_id: str, task_id: str) -> Optional["TaskRuntime"]:
        """从执行状态恢复"""
        from memory_runtime.execution_state_manager import ExecutionStateManager
        
        manager = ExecutionStateManager(agent_id=agent_id)
        state = manager.load()
        
        if not state or state.get("task_id") != task_id:
            return None
        
        config = TaskConfig(
            task_id=task_id,
            agent_id=agent_id,
        )
        
        runtime = cls(config)
        runtime._started_at = state.get("started_at")
        
        return runtime


# 便捷函数
def run_task(
    task_id: str,
    steps: List[Callable[[], Awaitable[StepResult]]],
    agent_id: str = "default",
    **kwargs
) -> TaskResult:
    """
    便捷的任务执行函数
    
    Args:
        task_id: 任务 ID
        steps: 步骤函数列表
        agent_id: Agent ID
        **kwargs: 其他 TaskConfig 参数
    
    Returns:
        TaskResult
    """
    import asyncio
    
    config = TaskConfig(task_id=task_id, agent_id=agent_id, **kwargs)
    runtime = TaskRuntime(config)
    runtime.start()
    
    async def execute_steps():
        for step_fn in steps:
            try:
                result = await step_fn()
                runtime.add_step(result)
                
                if not result.success and config.fail_fast:
                    break
            except Exception as e:
                runtime.add_step(StepResult(
                    step_id=f"step-{len(runtime._steps) + 1}",
                    success=False,
                    error=str(e),
                ))
                
                if config.fail_fast:
                    break
    
    asyncio.run(execute_steps())
    
    failed = any(not s.success for s in runtime._steps)
    return runtime.complete(
        success=not failed,
        error=None if not failed else "Some steps failed"
    )
