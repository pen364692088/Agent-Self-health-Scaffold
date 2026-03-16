"""
Memory Lifecycle Manager

管理记忆的完整生命周期，包括 TTL、降级、归档、恢复。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from pathlib import Path
from enum import Enum
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryTier,
    MemoryStatus,
)


class LifecycleState(str, Enum):
    """
    生命周期状态
    
    定义记忆的生命周期状态。
    """
    ACTIVE = "active"  # 活跃使用
    DEPRECATED = "deprecated"  # 已弃用
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


@dataclass
class TTLConfig:
    """
    TTL 配置
    
    定义不同状态的默认存活时间。
    """
    active_days: int = 90  # 活跃状态默认 TTL
    deprecated_days: int = 30  # 弃用状态默认 TTL
    archived_days: int = 365  # 归档状态默认 TTL
    
    def get_ttl(self, state: LifecycleState) -> timedelta:
        """
        获取指定状态的 TTL
        
        Args:
            state: 生命周期状态
        
        Returns:
            timedelta
        """
        days = {
            LifecycleState.ACTIVE: self.active_days,
            LifecycleState.DEPRECATED: self.deprecated_days,
            LifecycleState.ARCHIVED: self.archived_days,
            LifecycleState.DELETED: 0,
        }.get(state, self.active_days)
        
        return timedelta(days=days)


@dataclass
class LifecycleTransition:
    """
    生命周期转换记录
    
    记录状态转换的历史。
    """
    from_state: LifecycleState
    to_state: LifecycleState
    transitioned_at: datetime
    transitioned_by: str
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "transitioned_at": self.transitioned_at.isoformat(),
            "transitioned_by": self.transitioned_by,
            "reason": self.reason,
        }


@dataclass
class LifecycleRecord:
    """
    生命周期记录
    
    跟踪单个记忆的生命周期。
    """
    memory_id: str
    state: LifecycleState = LifecycleState.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    transitions: List[LifecycleTransition] = field(default_factory=list)
    use_count: int = 0
    
    def update_usage(self):
        """更新使用信息"""
        self.last_used = datetime.now(timezone.utc)
        self.use_count += 1
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memory_id": self.memory_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "use_count": self.use_count,
            "transitions": [t.to_dict() for t in self.transitions],
        }


class LifecycleManager:
    """
    生命周期管理器
    
    管理记忆的完整生命周期。
    """
    
    def __init__(
        self,
        ttl_config: Optional[TTLConfig] = None,
    ):
        """
        初始化生命周期管理器
        
        Args:
            ttl_config: TTL 配置
        """
        self.ttl_config = ttl_config or TTLConfig()
        self._lifecycle_records: Dict[str, LifecycleRecord] = {}
        self._memory_records: Dict[str, MemoryRecord] = {}
    
    def register(self, memory: MemoryRecord) -> LifecycleRecord:
        """
        注册新记忆
        
        Args:
            memory: 记忆记录
        
        Returns:
            LifecycleRecord
        """
        record = LifecycleRecord(
            memory_id=memory.id,
            state=LifecycleState.ACTIVE,
            created_at=memory.created_at,
            expires_at=datetime.now(timezone.utc) + self.ttl_config.get_ttl(LifecycleState.ACTIVE),
        )
        
        self._lifecycle_records[memory.id] = record
        self._memory_records[memory.id] = memory
        
        return record
    
    def transition(
        self,
        memory_id: str,
        to_state: LifecycleState,
        transitioned_by: str,
        reason: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        转换状态
        
        Args:
            memory_id: 记忆 ID
            to_state: 目标状态
            transitioned_by: 转换者
            reason: 原因
        
        Returns:
            (success, error)
        """
        record = self._lifecycle_records.get(memory_id)
        if not record:
            return False, f"Memory not found: {memory_id}"
        
        from_state = record.state
        
        # 验证转换是否合法
        if not self._is_valid_transition(from_state, to_state):
            return False, f"Invalid transition: {from_state.value} -> {to_state.value}"
        
        # 创建转换记录
        transition_record = LifecycleTransition(
            from_state=from_state,
            to_state=to_state,
            transitioned_at=datetime.now(timezone.utc),
            transitioned_by=transitioned_by,
            reason=reason,
        )
        
        # 更新状态
        record.state = to_state
        record.transitions.append(transition_record)
        
        # 更新 TTL
        if to_state != LifecycleState.DELETED:
            record.expires_at = datetime.now(timezone.utc) + self.ttl_config.get_ttl(to_state)
        
        # 更新 MemoryRecord 状态
        if memory_id in self._memory_records:
            self._memory_records[memory_id].status = self._to_memory_status(to_state)
        
        return True, None
    
    def _is_valid_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
    ) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            from_state: 源状态
            to_state: 目标状态
        
        Returns:
            是否合法
        """
        # 允许的转换
        valid_transitions = {
            LifecycleState.ACTIVE: {LifecycleState.DEPRECATED, LifecycleState.ARCHIVED},
            LifecycleState.DEPRECATED: {LifecycleState.ACTIVE, LifecycleState.ARCHIVED},
            LifecycleState.ARCHIVED: {LifecycleState.ACTIVE, LifecycleState.DELETED},
            LifecycleState.DELETED: set(),  # 终态
        }
        
        return to_state in valid_transitions.get(from_state, set())
    
    def _to_memory_status(self, state: LifecycleState) -> MemoryStatus:
        """
        转换为 MemoryStatus
        
        Args:
            state: 生命周期状态
        
        Returns:
            MemoryStatus
        """
        mapping = {
            LifecycleState.ACTIVE: MemoryStatus.ACTIVE,
            LifecycleState.DEPRECATED: MemoryStatus.DEPRECATED,
            LifecycleState.ARCHIVED: MemoryStatus.ACTIVE,  # 归档但保留
            LifecycleState.DELETED: MemoryStatus.DELETED,
        }
        
        return mapping.get(state, MemoryStatus.ACTIVE)
    
    def demote(
        self,
        memory_id: str,
        demoted_by: str,
        reason: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        降级记忆
        
        Args:
            memory_id: 记忆 ID
            demoted_by: 降级者
            reason: 原因
        
        Returns:
            (success, error)
        """
        record = self._lifecycle_records.get(memory_id)
        if not record:
            return False, f"Memory not found: {memory_id}"
        
        # 根据当前状态决定降级目标
        if record.state == LifecycleState.ACTIVE:
            return self.transition(memory_id, LifecycleState.DEPRECATED, demoted_by, reason)
        elif record.state == LifecycleState.DEPRECATED:
            return self.transition(memory_id, LifecycleState.ARCHIVED, demoted_by, reason)
        else:
            return False, f"Cannot demote from state: {record.state.value}"
    
    def archive(
        self,
        memory_id: str,
        archived_by: str,
        reason: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        归档记忆
        
        Args:
            memory_id: 记忆 ID
            archived_by: 归档者
            reason: 原因
        
        Returns:
            (success, error)
        """
        return self.transition(memory_id, LifecycleState.ARCHIVED, archived_by, reason)
    
    def restore(
        self,
        memory_id: str,
        restored_by: str,
        reason: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        恢复记忆
        
        Args:
            memory_id: 记忆 ID
            restored_by: 恢复者
            reason: 原因
        
        Returns:
            (success, error)
        """
        record = self._lifecycle_records.get(memory_id)
        if not record:
            return False, f"Memory not found: {memory_id}"
        
        if record.state in [LifecycleState.DEPRECATED, LifecycleState.ARCHIVED]:
            return self.transition(memory_id, LifecycleState.ACTIVE, restored_by, reason)
        else:
            return False, f"Cannot restore from state: {record.state.value}"
    
    def record_usage(self, memory_id: str):
        """
        记录使用
        
        Args:
            memory_id: 记忆 ID
        """
        record = self._lifecycle_records.get(memory_id)
        if record:
            record.update_usage()
            
            # 更新 MemoryRecord
            if memory_id in self._memory_records:
                self._memory_records[memory_id].use_count = record.use_count
                self._memory_records[memory_id].last_used = record.last_used
    
    def check_expiration(self) -> List[str]:
        """
        检查过期的记忆
        
        Returns:
            过期的记忆 ID 列表
        """
        expired = []
        
        for memory_id, record in self._lifecycle_records.items():
            if record.is_expired() and record.state != LifecycleState.DELETED:
                expired.append(memory_id)
        
        return expired
    
    def get_record(self, memory_id: str) -> Optional[LifecycleRecord]:
        """
        获取生命周期记录
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            LifecycleRecord
        """
        return self._lifecycle_records.get(memory_id)
    
    def list_by_state(
        self,
        state: LifecycleState,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """
        按状态列出记忆
        
        Args:
            state: 生命周期状态
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        memories = [
            self._memory_records[mid]
            for mid, record in self._lifecycle_records.items()
            if record.state == state and mid in self._memory_records
        ]
        
        memories.sort(key=lambda x: x.created_at, reverse=True)
        
        return memories[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        state_counts = {}
        
        for record in self._lifecycle_records.values():
            state_name = record.state.value
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
        
        expired_count = len(self.check_expiration())
        
        return {
            "total": len(self._lifecycle_records),
            "by_state": state_counts,
            "expired": expired_count,
        }


def create_lifecycle_manager(
    ttl_config: Optional[Dict[str, Any]] = None,
) -> LifecycleManager:
    """
    便捷函数：创建生命周期管理器
    
    Args:
        ttl_config: TTL 配置
    
    Returns:
        LifecycleManager 实例
    """
    config = TTLConfig()
    
    if ttl_config:
        if "active_days" in ttl_config:
            config.active_days = ttl_config["active_days"]
        if "deprecated_days" in ttl_config:
            config.deprecated_days = ttl_config["deprecated_days"]
        if "archived_days" in ttl_config:
            config.archived_days = ttl_config["archived_days"]
    
    return LifecycleManager(ttl_config=config)
