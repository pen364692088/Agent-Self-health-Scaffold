"""
Memory Recall Policy

定义召回策略，按任务类型触发 recall，默认只召回 approved。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)


class TaskType(str, Enum):
    """
    任务类型
    
    定义不同类型的任务，用于触发召回策略。
    """
    QUESTION = "question"  # 问答类
    CODING = "coding"  # 编码类
    DECISION = "decision"  # 决策类
    CREATIVE = "creative"  # 创意类
    ANALYSIS = "analysis"  # 分析类
    GENERAL = "general"  # 通用类


@dataclass
class RecallTrigger:
    """
    召回触发器
    
    定义何时触发召回。
    """
    task_type: TaskType
    trigger_recall: bool = True
    priority: int = 0  # 优先级（越高越优先）
    keywords: List[str] = field(default_factory=list)  # 触发关键词
    
    def should_trigger(self, query: str) -> bool:
        """
        检查是否应该触发
        
        Args:
            query: 查询内容
        
        Returns:
            是否触发
        """
        if not self.trigger_recall:
            return False
        
        # 检查关键词
        if self.keywords:
            query_lower = query.lower()
            return any(kw.lower() in query_lower for kw in self.keywords)
        
        return True


@dataclass
class RecallPolicy:
    """
    召回策略
    
    定义完整的召回策略。
    """
    # 基本设置
    default_task_type: TaskType = TaskType.GENERAL
    approved_only: bool = True  # 默认只召回 approved
    canary_mode: bool = True  # 只允许 canary 模式
    
    # 任务类型触发器
    triggers: Dict[TaskType, RecallTrigger] = field(default_factory=lambda: {
        TaskType.QUESTION: RecallTrigger(task_type=TaskType.QUESTION, trigger_recall=True, priority=1),
        TaskType.CODING: RecallTrigger(task_type=TaskType.CODING, trigger_recall=True, priority=2),
        TaskType.DECISION: RecallTrigger(task_type=TaskType.DECISION, trigger_recall=True, priority=3),
        TaskType.CREATIVE: RecallTrigger(task_type=TaskType.CREATIVE, trigger_recall=False, priority=0),
        TaskType.ANALYSIS: RecallTrigger(task_type=TaskType.ANALYSIS, trigger_recall=True, priority=1),
        TaskType.GENERAL: RecallTrigger(task_type=TaskType.GENERAL, trigger_recall=True, priority=0),
    })
    
    # 作用域限制
    allowed_scopes: Set[MemoryScope] = field(default_factory=lambda: {
        MemoryScope.GLOBAL,
        MemoryScope.PROJECTS,
        MemoryScope.DOMAINS,
    })
    
    # 层级限制
    allowed_layers: Set[TruthKnowledgeRetrieval] = field(default_factory=lambda: {
        TruthKnowledgeRetrieval.TRUTH,
        TruthKnowledgeRetrieval.KNOWLEDGE,
        TruthKnowledgeRetrieval.RETRIEVAL,
    })
    
    def should_recall(
        self,
        task_type: TaskType,
        query: str,
    ) -> bool:
        """
        检查是否应该召回
        
        Args:
            task_type: 任务类型
            query: 查询内容
        
        Returns:
            是否召回
        """
        trigger = self.triggers.get(task_type)
        if not trigger:
            return False
        
        return trigger.should_trigger(query)
    
    def is_approved_only(self) -> bool:
        """是否只召回 approved"""
        return self.approved_only
    
    def is_canary_mode(self) -> bool:
        """是否 canary 模式"""
        return self.canary_mode
    
    def filter_records(
        self,
        records: List[MemoryRecord],
        approved_ids: Optional[Set[str]] = None,
    ) -> List[MemoryRecord]:
        """
        过滤记录
        
        Args:
            records: 记录列表
            approved_ids: approved 记录 ID 集合
        
        Returns:
            过滤后的记录
        """
        filtered = []
        
        for record in records:
            # 检查作用域
            if record.scope not in self.allowed_scopes:
                continue
            
            # 检查层级
            if record.tkr_layer not in self.allowed_layers:
                continue
            
            # 检查 approved only
            if self.approved_only and approved_ids:
                if record.id not in approved_ids:
                    continue
            
            filtered.append(record)
        
        return filtered


class RecallPolicyManager:
    """
    召回策略管理器
    
    管理召回策略的应用和执行。
    """
    
    def __init__(
        self,
        policy: Optional[RecallPolicy] = None,
    ):
        """
        初始化策略管理器
        
        Args:
            policy: 召回策略
        """
        self.policy = policy or RecallPolicy()
        self._approved_ids: Set[str] = set()
    
    def set_approved_ids(self, approved_ids: Set[str]):
        """
        设置 approved 记录 ID
        
        Args:
            approved_ids: ID 集合
        """
        self._approved_ids = approved_ids
    
    def detect_task_type(self, query: str) -> TaskType:
        """
        检测任务类型
        
        Args:
            query: 查询内容
        
        Returns:
            任务类型
        """
        query_lower = query.lower()
        
        # 关键词检测
        if any(kw in query_lower for kw in ["code", "implement", "function", "class", "method"]):
            return TaskType.CODING
        
        if any(kw in query_lower for kw in ["decide", "should", "choose", "option"]):
            return TaskType.DECISION
        
        if any(kw in query_lower for kw in ["create", "write", "design", "generate"]):
            return TaskType.CREATIVE
        
        if any(kw in query_lower for kw in ["analyze", "review", "compare", "evaluate"]):
            return TaskType.ANALYSIS
        
        if any(kw in query_lower for kw in ["what", "how", "why", "when", "where"]):
            return TaskType.QUESTION
        
        return TaskType.GENERAL
    
    def should_recall(
        self,
        query: str,
        task_type: Optional[TaskType] = None,
    ) -> bool:
        """
        检查是否应该召回
        
        Args:
            query: 查询内容
            task_type: 任务类型（可选，自动检测）
        
        Returns:
            是否召回
        """
        if task_type is None:
            task_type = self.detect_task_type(query)
        
        return self.policy.should_recall(task_type, query)
    
    def apply_policy(
        self,
        records: List[MemoryRecord],
        query: str,
        task_type: Optional[TaskType] = None,
    ) -> List[MemoryRecord]:
        """
        应用策略
        
        Args:
            records: 记录列表
            query: 查询内容
            task_type: 任务类型（可选）
        
        Returns:
            过滤后的记录
        """
        if task_type is None:
            task_type = self.detect_task_type(query)
        
        # 检查是否应该召回
        if not self.policy.should_recall(task_type, query):
            return []
        
        # 过滤记录
        return self.policy.filter_records(records, self._approved_ids)
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """
        获取策略摘要
        
        Returns:
            摘要字典
        """
        return {
            "approved_only": self.policy.approved_only,
            "canary_mode": self.policy.canary_mode,
            "task_triggers": {
                tt.value: {
                    "trigger": t.trigger_recall,
                    "priority": t.priority,
                }
                for tt, t in self.policy.triggers.items()
            },
            "allowed_scopes": [s.value for s in self.policy.allowed_scopes],
            "allowed_layers": [l.value for l in self.policy.allowed_layers],
        }


def create_recall_policy(
    approved_only: bool = True,
    canary_mode: bool = True,
) -> RecallPolicy:
    """
    便捷函数：创建召回策略
    
    Args:
        approved_only: 是否只召回 approved
        canary_mode: 是否 canary 模式
    
    Returns:
        RecallPolicy 实例
    """
    return RecallPolicy(
        approved_only=approved_only,
        canary_mode=canary_mode,
    )
