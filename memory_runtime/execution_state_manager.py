"""
Execution State Manager - Runtime Execution State Management

管理运行时执行状态，支持任务恢复和检查点。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone


@dataclass
class ExecutionStateConfig:
    """
    执行状态配置
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    max_checkpoints: int = 10


class ExecutionStateManager:
    """
    执行状态管理器
    
    负责：
    - 加载执行状态
    - 保存执行状态
    - 检查点管理
    """
    
    def __init__(self, config: Optional[ExecutionStateConfig] = None, **kwargs):
        # 支持直接传参
        if config is None:
            config = ExecutionStateConfig(
                agent_id=kwargs.get("agent_id", "default"),
                memory_root=kwargs.get("memory_root"),
            )
        self.config = config
    
    def _get_memory_root(self) -> Path:
        """获取记忆根目录"""
        if self.config.memory_root:
            return self.config.memory_root
        
        # 默认路径
        return Path.home() / ".openclaw" / "agents" / self.config.agent_id / "memory"
    
    def _get_state_file(self) -> Path:
        """获取状态文件路径"""
        return self._get_memory_root() / "execution_state.yaml"
    
    def _ensure_memory_dir(self) -> Path:
        """确保记忆目录存在"""
        root = self._get_memory_root()
        root.mkdir(parents=True, exist_ok=True)
        return root
    
    def load(self) -> Optional[Dict[str, Any]]:
        """
        加载执行状态
        
        Returns:
            执行状态字典，不存在时返回 None
        """
        state_file = self._get_state_file()
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return None
    
    def save(
        self,
        task_id: Optional[str] = None,
        step: Optional[str] = None,
        status: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        保存执行状态
        
        Args:
            task_id: 任务 ID
            step: 当前步骤
            status: 状态 (pending/running/completed/failed)
            context: 上下文
            metadata: 元数据
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_memory_dir()
            state_file = self._get_state_file()
            
            # 读取现有状态
            existing = self.load() or {}
            
            # 构建新状态
            state = {
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # 更新字段
            if task_id:
                state["task_id"] = task_id
            elif existing.get("task_id"):
                state["task_id"] = existing["task_id"]
            
            if step:
                state["step"] = step
            elif existing.get("step"):
                state["step"] = existing["step"]
            
            if status:
                state["status"] = status
            elif existing.get("status"):
                state["status"] = existing["status"]
            
            if context:
                state["context"] = context
            elif existing.get("context"):
                state["context"] = existing["context"]
            
            if metadata:
                state["metadata"] = metadata
            
            # 写入
            with open(state_file, "w") as f:
                yaml.dump(state, f)
            
            return True
            
        except Exception:
            return False
    
    def save_checkpoint(
        self,
        checkpoint_name: str,
        state: Dict[str, Any],
    ) -> bool:
        """
        保存检查点
        
        Args:
            checkpoint_name: 检查点名称
            state: 状态
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_memory_dir()
            checkpoints_dir = self._get_memory_root() / "checkpoints"
            checkpoints_dir.mkdir(exist_ok=True)
            
            checkpoint_file = checkpoints_dir / f"{checkpoint_name}.yaml"
            
            checkpoint = {
                "name": checkpoint_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state": state,
            }
            
            with open(checkpoint_file, "w") as f:
                yaml.dump(checkpoint, f)
            
            # 清理旧检查点
            self._cleanup_old_checkpoints(checkpoints_dir)
            
            return True
            
        except Exception:
            return False
    
    def load_checkpoint(self, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        加载检查点
        
        Args:
            checkpoint_name: 检查点名称
        
        Returns:
            检查点状态，不存在时返回 None
        """
        checkpoints_dir = self._get_memory_root() / "checkpoints"
        checkpoint_file = checkpoints_dir / f"{checkpoint_name}.yaml"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file) as f:
                data = yaml.safe_load(f)
                return data.get("state") if data else None
        except Exception:
            return None
    
    def list_checkpoints(self) -> List[str]:
        """
        列出所有检查点
        
        Returns:
            检查点名称列表
        """
        checkpoints_dir = self._get_memory_root() / "checkpoints"
        
        if not checkpoints_dir.exists():
            return []
        
        return [f.stem for f in checkpoints_dir.glob("*.yaml")]
    
    def _cleanup_old_checkpoints(self, checkpoints_dir: Path):
        """清理旧检查点"""
        checkpoints = sorted(
            checkpoints_dir.glob("*.yaml"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        
        # 保留最新的 N 个
        for old_checkpoint in checkpoints[self.config.max_checkpoints:]:
            old_checkpoint.unlink()
    
    def clear(self) -> bool:
        """
        清除执行状态
        
        Returns:
            是否清除成功
        """
        state_file = self._get_state_file()
        
        if state_file.exists():
            state_file.unlink()
        
        return True
