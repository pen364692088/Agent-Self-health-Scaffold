"""
Memory Promotion Manager

管理 candidate -> approved 的晋升流程，包含硬门槛、审核、回滚。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_candidate_store import CandidateStore, CandidateRecord


@dataclass
class PromotionGate:
    """
    晋升门槛
    
    定义 candidate 晋升为 approved 的条件。
    """
    review_required: bool = True  # 是否需要审核
    min_confidence: float = 0.7  # 最低置信度
    min_importance: float = 0.5  # 最低重要性
    no_severe_conflicts: bool = True  # 无严重冲突
    source_verified: bool = False  # 来源已验证
    min_tags: int = 1  # 最少标签数
    
    def check(self, candidate: CandidateRecord) -> tuple[bool, List[str]]:
        """
        检查候选是否满足门槛
        
        Args:
            candidate: 候选记录
        
        Returns:
            (passed, reasons): 是否通过，原因列表
        """
        reasons = []
        
        # 检查审核
        if self.review_required and candidate.status not in ["approved", "pending"]:
            reasons.append(f"Status must be approved or pending, got: {candidate.status}")
        
        # 检查置信度
        if candidate.metadata.confidence < self.min_confidence:
            reasons.append(f"Confidence {candidate.metadata.confidence} < {self.min_confidence}")
        
        # 检查重要性
        if candidate.metadata.importance < self.min_importance:
            reasons.append(f"Importance {candidate.metadata.importance} < {self.min_importance}")
        
        # 检查标签数
        if len(candidate.metadata.tags) < self.min_tags:
            reasons.append(f"Tags {len(candidate.metadata.tags)} < {self.min_tags}")
        
        passed = len(reasons) == 0
        return passed, reasons


@dataclass
class PromotionRecord:
    """
    晋升记录
    
    记录晋升的历史信息，支持回滚。
    """
    promotion_id: str  # 晋升 ID
    candidate_id: str  # 候选 ID
    memory_id: str  # 生成的记忆 ID
    
    promoted_at: datetime  # 晋升时间
    promoted_by: str  # 晋升者
    review_notes: Optional[str] = None  # 审核备注
    
    rolled_back: bool = False  # 是否已回滚
    rolled_back_at: Optional[datetime] = None  # 回滚时间
    rolled_back_by: Optional[str] = None  # 回滚者
    rollback_reason: Optional[str] = None  # 回滚原因
    
    gates_passed: List[str] = field(default_factory=list)  # 通过的门槛
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "promotion_id": self.promotion_id,
            "candidate_id": self.candidate_id,
            "memory_id": self.memory_id,
            "promoted_at": self.promoted_at.isoformat(),
            "promoted_by": self.promoted_by,
            "review_notes": self.review_notes,
            "rolled_back": self.rolled_back,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "rolled_back_by": self.rolled_back_by,
            "rollback_reason": self.rollback_reason,
            "gates_passed": self.gates_passed,
        }


class PromotionManager:
    """
    晋升管理器
    
    管理 candidate -> approved 的晋升流程。
    """
    
    def __init__(
        self,
        candidate_store: Optional[CandidateStore] = None,
        gate: Optional[PromotionGate] = None,
    ):
        """
        初始化晋升管理器
        
        Args:
            candidate_store: 候选存储
            gate: 晋升门槛
        """
        self.candidate_store = candidate_store or CandidateStore()
        self.gate = gate or PromotionGate()
        self._promotion_history: Dict[str, PromotionRecord] = {}
        self._memory_records: Dict[str, MemoryRecord] = {}
    
    def check_gates(self, candidate_id: str) -> tuple[bool, List[str]]:
        """
        检查候选是否满足晋升门槛
        
        Args:
            candidate_id: 候选 ID
        
        Returns:
            (passed, reasons)
        """
        candidate = self.candidate_store.get(candidate_id)
        if not candidate:
            return False, [f"Candidate not found: {candidate_id}"]
        
        return self.gate.check(candidate)
    
    def promote(
        self,
        candidate_id: str,
        promoted_by: str,
        review_notes: Optional[str] = None,
        target_tkr_layer: Optional[TruthKnowledgeRetrieval] = None,
    ) -> tuple[bool, Optional[PromotionRecord], List[str]]:
        """
        晋升候选为正式记忆
        
        Args:
            candidate_id: 候选 ID
            promoted_by: 晋升者
            review_notes: 审核备注
            target_tkr_layer: 目标 T/K/R 层级
        
        Returns:
            (success, record, reasons)
        """
        # 检查门槛
        passed, reasons = self.check_gates(candidate_id)
        if not passed:
            return False, None, reasons
        
        # 执行晋升
        result = self.candidate_store.promote(
            candidate_id=candidate_id,
            target_tkr_layer=target_tkr_layer or TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by=promoted_by,
            review_notes=review_notes,
        )
        
        if not result.success:
            return False, None, [result.error or "Promotion failed"]
        
        # 创建晋升记录
        promotion_id = f"promo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{candidate_id[:8]}"
        
        record = PromotionRecord(
            promotion_id=promotion_id,
            candidate_id=candidate_id,
            memory_id=result.memory_record.id,
            promoted_at=datetime.now(timezone.utc),
            promoted_by=promoted_by,
            review_notes=review_notes,
            gates_passed=["confidence", "importance", "tags"],
        )
        
        self._promotion_history[promotion_id] = record
        self._memory_records[result.memory_record.id] = result.memory_record
        
        return True, record, []
    
    def rollback(
        self,
        memory_id: str,
        rolled_back_by: str,
        rollback_reason: str,
    ) -> tuple[bool, Optional[str]]:
        """
        回滚晋升
        
        Args:
            memory_id: 记忆 ID
            rolled_back_by: 回滚者
            rollback_reason: 回滚原因
        
        Returns:
            (success, error)
        """
        # 查找晋升记录
        record = None
        for r in self._promotion_history.values():
            if r.memory_id == memory_id and not r.rolled_back:
                record = r
                break
        
        if not record:
            return False, f"No active promotion found for memory: {memory_id}"
        
        # 标记回滚
        record.rolled_back = True
        record.rolled_back_at = datetime.now(timezone.utc)
        record.rolled_back_by = rolled_back_by
        record.rollback_reason = rollback_reason
        
        # 从正式记忆中移除
        if memory_id in self._memory_records:
            del self._memory_records[memory_id]
        
        # 更新候选状态
        candidate = self.candidate_store.get(record.candidate_id)
        if candidate:
            candidate.status = "rollback"
        
        return True, None
    
    def get_promotion_history(
        self,
        candidate_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PromotionRecord]:
        """
        获取晋升历史
        
        Args:
            candidate_id: 候选 ID 过滤
            limit: 返回数量
        
        Returns:
            晋升记录列表
        """
        records = list(self._promotion_history.values())
        
        if candidate_id:
            records = [r for r in records if r.candidate_id == candidate_id]
        
        # 按时间倒序
        records.sort(key=lambda x: x.promoted_at, reverse=True)
        
        return records[:limit]
    
    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """
        获取晋升后的记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            记忆记录
        """
        return self._memory_records.get(memory_id)
    
    def list_active_memories(
        self,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """
        列出活跃的正式记忆
        
        Args:
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        # 过滤已回滚的
        active_ids = {
            r.memory_id for r in self._promotion_history.values()
            if not r.rolled_back
        }
        
        memories = [
            self._memory_records[mid]
            for mid in active_ids
            if mid in self._memory_records
        ]
        
        memories.sort(key=lambda x: x.created_at, reverse=True)
        
        return memories[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        total = len(self._promotion_history)
        rolled_back = sum(1 for r in self._promotion_history.values() if r.rolled_back)
        active = total - rolled_back
        
        return {
            "total_promotions": total,
            "active_memories": active,
            "rolled_back": rolled_back,
            "rollback_rate": rolled_back / total if total > 0 else 0,
        }


def create_promotion_manager(
    candidate_store: Optional[CandidateStore] = None,
    gate_config: Optional[Dict[str, Any]] = None,
) -> PromotionManager:
    """
    便捷函数：创建晋升管理器
    
    Args:
        candidate_store: 候选存储
        gate_config: 门槛配置
    
    Returns:
        PromotionManager 实例
    """
    gate = PromotionGate()
    
    if gate_config:
        if "review_required" in gate_config:
            gate.review_required = gate_config["review_required"]
        if "min_confidence" in gate_config:
            gate.min_confidence = gate_config["min_confidence"]
        if "min_importance" in gate_config:
            gate.min_importance = gate_config["min_importance"]
        if "min_tags" in gate_config:
            gate.min_tags = gate_config["min_tags"]
    
    return PromotionManager(candidate_store=candidate_store, gate=gate)
