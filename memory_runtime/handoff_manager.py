"""
Handoff Manager - Session Handoff State Management

管理会话交接状态，支持跨会话工作恢复。

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
class HandoffConfig:
    """
    Handoff 配置
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    auto_create: bool = True


class HandoffManager:
    """
    Handoff 状态管理器
    
    负责：
    - 加载 handoff 状态
    - 保存 handoff 状态
    - 生成 handoff 摘要
    """
    
    def __init__(self, config: Optional[HandoffConfig] = None, **kwargs):
        # 支持直接传参
        if config is None:
            config = HandoffConfig(
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
    
    def _get_handoff_file(self) -> Path:
        """获取 handoff 文件路径"""
        return self._get_memory_root() / "handoff_state.yaml"
    
    def _ensure_memory_dir(self) -> Path:
        """确保记忆目录存在"""
        root = self._get_memory_root()
        root.mkdir(parents=True, exist_ok=True)
        return root
    
    def load(self) -> Optional[Dict[str, Any]]:
        """
        加载 handoff 状态
        
        Returns:
            Handoff 状态字典，不存在时返回 None
        """
        handoff_file = self._get_handoff_file()
        
        if not handoff_file.exists():
            return None
        
        try:
            with open(handoff_file) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return None
    
    def save(
        self,
        objective: Optional[str] = None,
        phase: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        保存 handoff 状态
        
        Args:
            objective: 当前目标
            phase: 当前阶段
            next_actions: 下一步动作
            blockers: 阻塞项
            summary: 摘要
            metadata: 元数据
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_memory_dir()
            handoff_file = self._get_handoff_file()
            
            # 读取现有状态
            existing = self.load() or {}
            
            # 更新字段
            state = {
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # 合并现有状态
            if objective:
                state["objective"] = objective
            elif existing.get("objective"):
                state["objective"] = existing["objective"]
            
            if phase:
                state["phase"] = phase
            elif existing.get("phase"):
                state["phase"] = existing["phase"]
            
            if next_actions:
                state["next_actions"] = next_actions
            elif existing.get("next_actions"):
                state["next_actions"] = existing["next_actions"]
            
            if blockers:
                state["blockers"] = blockers
            elif existing.get("blockers"):
                state["blockers"] = existing["blockers"]
            
            if summary:
                state["summary"] = summary
            
            if metadata:
                state["metadata"] = metadata
            
            # 写入
            with open(handoff_file, "w") as f:
                yaml.dump(state, f)
            
            return True
            
        except Exception:
            return False
    
    def clear(self) -> bool:
        """
        清除 handoff 状态
        
        Returns:
            是否清除成功
        """
        handoff_file = self._get_handoff_file()
        
        if handoff_file.exists():
            handoff_file.unlink()
        
        return True
    
    def get_summary(self) -> str:
        """
        获取 handoff 摘要
        
        Returns:
            摘要字符串
        """
        state = self.load()
        
        if not state:
            return "No handoff state available."
        
        lines = [f"# Handoff Summary ({self.config.agent_id})"]
        
        if state.get("objective"):
            lines.append(f"\n## Objective\n{state['objective']}")
        
        if state.get("phase"):
            lines.append(f"\n## Phase\n{state['phase']}")
        
        if state.get("next_actions"):
            lines.append("\n## Next Actions")
            for action in state["next_actions"]:
                lines.append(f"- {action}")
        
        if state.get("blockers"):
            lines.append("\n## Blockers")
            for blocker in state["blockers"]:
                lines.append(f"- {blocker}")
        
        if state.get("summary"):
            lines.append(f"\n## Summary\n{state['summary']}")
        
        return "\n".join(lines)
