"""
Memory Writer - Unified Writing Interface

封装 core/memory/memory_capture.py，提供统一的记忆写入接口。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import json
from datetime import datetime, timezone

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入核心实现
from core.memory.memory_capture import (
    CaptureEngine,
    CaptureReason,
    SourceRef,
)


@dataclass
class WriteConfig:
    """
    写入配置
    
    定义记忆写入行为。
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    tier: str = "candidate"  # candidate/approved
    enable_evidence: bool = True
    fail_open: bool = False


@dataclass
class WriteResult:
    """
    写入结果
    
    包含写入的状态。
    """
    success: bool
    record_id: Optional[str] = None
    evidence_id: Optional[str] = None
    error: Optional[str] = None


class MemoryWriter:
    """
    记忆写入器
    
    统一的记忆写入入口，整合：
    - 长期记忆写入 (core/memory/memory_capture.py)
    - Handoff 状态写入
    - Execution 状态写入
    """
    
    def __init__(self, config: Optional[WriteConfig] = None):
        self.config = config or WriteConfig()
        self._capture_engine: Optional[CaptureEngine] = None
    
    def _get_memory_root(self) -> Path:
        """获取记忆根目录"""
        if self.config.memory_root:
            return self.config.memory_root
        
        # 默认路径
        return Path.home() / ".openclaw" / "agents" / self.config.agent_id / "memory"
    
    def _ensure_memory_dir(self):
        """确保记忆目录存在"""
        root = self._get_memory_root()
        root.mkdir(parents=True, exist_ok=True)
        return root
    
    def write_long_term_memory(
        self,
        content: str,
        category: str = "fact",
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WriteResult:
        """
        写入长期记忆
        
        Args:
            content: 记忆内容
            category: 分类 (fact/decision/preference/other)
            source: 来源
            metadata: 元数据
        
        Returns:
            WriteResult
        """
        try:
            # 生成记录 ID
            timestamp = datetime.now(timezone.utc)
            record_id = f"{category}:{timestamp.strftime('%Y%m%d')}:{hash(content) % 10000:04d}"
            
            # 写入文件
            root = self._ensure_memory_dir()
            memory_file = root / "long_term_memory.yaml"
            
            # 追加记录
            record = {
                "id": record_id,
                "content": content,
                "category": category,
                "source": source,
                "timestamp": timestamp.isoformat(),
                "metadata": metadata or {},
            }
            
            # 读取现有内容
            existing = []
            if memory_file.exists():
                import yaml
                with open(memory_file) as f:
                    data = yaml.safe_load(f) or {}
                    existing = data.get("records", [])
            
            # 追加新记录
            existing.append(record)
            
            # 写回
            import yaml
            with open(memory_file, "w") as f:
                yaml.dump({"records": existing}, f)
            
            return WriteResult(
                success=True,
                record_id=record_id,
            )
            
        except Exception as e:
            return WriteResult(
                success=False,
                error=str(e),
            )
    
    def write_handoff_state(
        self,
        objective: Optional[str] = None,
        phase: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        summary: Optional[str] = None,
    ) -> WriteResult:
        """
        写入 handoff 状态
        
        Args:
            objective: 当前目标
            phase: 当前阶段
            next_actions: 下一步动作
            blockers: 阻塞项
            summary: 摘要
        
        Returns:
            WriteResult
        """
        try:
            from memory_runtime.handoff_manager import HandoffManager
            
            manager = HandoffManager(
                agent_id=self.config.agent_id,
                memory_root=self.config.memory_root,
            )
            
            success = manager.save(
                objective=objective,
                phase=phase,
                next_actions=next_actions,
                blockers=blockers,
                summary=summary,
            )
            
            return WriteResult(success=success)
            
        except Exception as e:
            return WriteResult(
                success=False,
                error=str(e),
            )
    
    def write_execution_state(
        self,
        task_id: Optional[str] = None,
        step: Optional[str] = None,
        status: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WriteResult:
        """
        写入执行状态
        
        Args:
            task_id: 任务 ID
            step: 当前步骤
            status: 状态
            context: 上下文
        
        Returns:
            WriteResult
        """
        try:
            from memory_runtime.execution_state_manager import ExecutionStateManager
            
            manager = ExecutionStateManager(
                agent_id=self.config.agent_id,
                memory_root=self.config.memory_root,
            )
            
            success = manager.save(
                task_id=task_id,
                step=step,
                status=status,
                context=context,
            )
            
            return WriteResult(success=success)
            
        except Exception as e:
            return WriteResult(
                success=False,
                error=str(e),
            )


# 便捷函数
def write_memory(
    content: str,
    agent_id: str = "default",
    category: str = "fact",
    **kwargs
) -> WriteResult:
    """
    便捷的记忆写入函数
    
    Args:
        content: 记忆内容
        agent_id: Agent ID
        category: 分类
        **kwargs: 其他 WriteConfig 参数
    
    Returns:
        WriteResult
    """
    config = WriteConfig(agent_id=agent_id, **kwargs)
    writer = MemoryWriter(config)
    return writer.write_long_term_memory(content, category=category)
