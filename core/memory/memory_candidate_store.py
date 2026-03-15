"""
Memory Candidate Store

候选记忆存储，支持审核、提升、拒绝。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_capture import (
    CandidateRecord,
    CaptureMetadata,
    CaptureReason,
    SourceRef,
)


@dataclass
class PromotionResult:
    """
    提升结果
    
    记录候选提升为正式记忆的结果。
    """
    success: bool
    candidate_id: str
    memory_record: Optional[MemoryRecord] = None
    error: Optional[str] = None
    promoted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateStore:
    """
    候选存储
    
    管理候选记录的 CRUD 和提升操作。
    """
    
    def __init__(self):
        """初始化候选存储"""
        self._candidates: Dict[str, CandidateRecord] = {}
        self._memory_records: Dict[str, MemoryRecord] = {}
    
    def add(self, candidate: CandidateRecord) -> bool:
        """
        添加候选
        
        Args:
            candidate: 候选记录
        
        Returns:
            是否成功
        """
        if candidate.id in self._candidates:
            return False
        
        self._candidates[candidate.id] = candidate
        return True
    
    def get(self, candidate_id: str) -> Optional[CandidateRecord]:
        """
        获取候选
        
        Args:
            candidate_id: 候选 ID
        
        Returns:
            候选记录
        """
        return self._candidates.get(candidate_id)
    
    def update(self, candidate_id: str, **kwargs) -> bool:
        """
        更新候选
        
        Args:
            candidate_id: 候选 ID
            **kwargs: 更新字段
        
        Returns:
            是否成功
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return False
        
        for key, value in kwargs.items():
            if hasattr(candidate, key):
                setattr(candidate, key, value)
        
        return True
    
    def delete(self, candidate_id: str) -> bool:
        """
        删除候选
        
        Args:
            candidate_id: 候选 ID
        
        Returns:
            是否成功
        """
        if candidate_id not in self._candidates:
            return False
        
        del self._candidates[candidate_id]
        return True
    
    def list(
        self,
        status: Optional[str] = None,
        scope: Optional[MemoryScope] = None,
        limit: int = 100,
    ) -> List[CandidateRecord]:
        """
        列出候选
        
        Args:
            status: 状态过滤
            scope: 作用域过滤
            limit: 返回数量
        
        Returns:
            候选列表
        """
        candidates = list(self._candidates.values())
        
        if status:
            candidates = [c for c in candidates if c.status == status]
        
        if scope:
            candidates = [c for c in candidates if c.metadata.scope == scope]
        
        # 按捕获时间倒序
        candidates.sort(key=lambda x: x.captured_at, reverse=True)
        
        return candidates[:limit]
    
    def approve(
        self,
        candidate_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> bool:
        """
        批准候选
        
        Args:
            candidate_id: 候选 ID
            reviewed_by: 审核者
            review_notes: 审核备注
        
        Returns:
            是否成功
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return False
        
        if candidate.status != "pending":
            return False
        
        candidate.status = "approved"
        candidate.reviewed_at = datetime.now(timezone.utc)
        candidate.reviewed_by = reviewed_by
        candidate.review_notes = review_notes
        
        return True
    
    def reject(
        self,
        candidate_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> bool:
        """
        拒绝候选
        
        Args:
            candidate_id: 候选 ID
            reviewed_by: 审核者
            review_notes: 审核备注
        
        Returns:
            是否成功
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return False
        
        if candidate.status != "pending":
            return False
        
        candidate.status = "rejected"
        candidate.reviewed_at = datetime.now(timezone.utc)
        candidate.reviewed_by = reviewed_by
        candidate.review_notes = review_notes
        
        return True
    
    def promote(
        self,
        candidate_id: str,
        target_tkr_layer: TruthKnowledgeRetrieval,
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> PromotionResult:
        """
        提升候选为正式记忆
        
        Args:
            candidate_id: 候选 ID
            target_tkr_layer: 目标 T/K/R 层级
            reviewed_by: 审核者
            review_notes: 审核备注
        
        Returns:
            PromotionResult
        """
        candidate = self._candidates.get(candidate_id)
        
        if not candidate:
            return PromotionResult(
                success=False,
                candidate_id=candidate_id,
                error="Candidate not found",
            )
        
        if candidate.status not in ["pending", "approved"]:
            return PromotionResult(
                success=False,
                candidate_id=candidate_id,
                error=f"Invalid status: {candidate.status}",
            )
        
        # 创建正式记忆记录
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{candidate.content_hash[:8]}"
        
        memory_record = MemoryRecord(
            id=memory_id,
            source_file=candidate.metadata.source_ref.path,
            source_kind=self._infer_source_kind(candidate),
            content_type=candidate.metadata.content_type,
            scope=candidate.metadata.scope,
            scope_qualifier=candidate.metadata.scope_qualifier,
            tkr_layer=target_tkr_layer,
            title=candidate.title,
            content=candidate.content,
            tags=candidate.metadata.tags,
            confidence=candidate.metadata.confidence,
            importance=candidate.metadata.importance,
            tier=MemoryTier.WARM,
            created_at=datetime.now(timezone.utc),
        )
        
        # 更新候选状态
        candidate.status = "promoted"
        candidate.reviewed_at = datetime.now(timezone.utc)
        candidate.reviewed_by = reviewed_by
        candidate.review_notes = review_notes
        candidate.promoted_at = datetime.now(timezone.utc)
        candidate.promoted_to_id = memory_id
        candidate.target_tkr_layer = target_tkr_layer
        
        # 存储正式记忆
        self._memory_records[memory_id] = memory_record
        
        return PromotionResult(
            success=True,
            candidate_id=candidate_id,
            memory_record=memory_record,
        )
    
    def _infer_source_kind(self, candidate: CandidateRecord) -> MemorySourceKind:
        """
        推断来源类型
        
        Args:
            candidate: 候选记录
        
        Returns:
            来源类型
        """
        path = candidate.metadata.source_ref.path.lower()
        
        if "decision" in path:
            return MemorySourceKind.DECISION_LOG
        elif "note" in path:
            return MemorySourceKind.TECHNICAL_NOTE
        elif "policy" in path:
            return MemorySourceKind.POLICY
        elif "rule" in path:
            return MemorySourceKind.RULE
        else:
            return MemorySourceKind.SESSION_LOG
    
    def get_promoted_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """
        获取提升后的记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            记忆记录
        """
        return self._memory_records.get(memory_id)
    
    def list_promoted_memories(
        self,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """
        列出提升后的记忆
        
        Args:
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        memories = list(self._memory_records.values())
        memories.sort(key=lambda x: x.created_at, reverse=True)
        return memories[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        candidates = list(self._candidates.values())
        
        status_counts = {}
        for c in candidates:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1
        
        return {
            "total_candidates": len(candidates),
            "by_status": status_counts,
            "promoted_memories": len(self._memory_records),
        }
    
    def export_to_json(self, path: str):
        """
        导出到 JSON 文件
        
        Args:
            path: 文件路径
        """
        data = {
            "candidates": [c.to_dict() for c in self._candidates.values()],
            "promoted_memories": [
                {
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "scope": m.scope.value,
                    "tkr_layer": m.tkr_layer.value,
                }
                for m in self._memory_records.values()
            ],
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_candidate_store() -> CandidateStore:
    """
    便捷函数：创建候选存储
    
    Returns:
        CandidateStore 实例
    """
    return CandidateStore()
