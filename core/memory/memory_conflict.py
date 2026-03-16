"""
Memory Conflict Resolution

检测和解决记忆冲突。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
import difflib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)


class ConflictType(str, Enum):
    """
    冲突类型
    
    定义不同类型的记忆冲突。
    """
    CONTRADICTION = "contradiction"  # 内容矛盾
    OVERLAP = "overlap"  # 内容重叠
    SUPERSESSION = "supersession"  # 新记录取代旧记录
    DUPLICATE = "duplicate"  # 重复内容
    SCOPE_CONFLICT = "scope_conflict"  # 作用域冲突


class ConflictSeverity(str, Enum):
    """
    冲突严重程度
    
    定义冲突的严重程度。
    """
    LOW = "low"  # 低严重程度，可自动解决
    MEDIUM = "medium"  # 中等严重程度，建议人工审核
    HIGH = "high"  # 高严重程度，必须人工裁定
    CRITICAL = "critical"  # 关键冲突，阻止晋升


class ResolutionStrategy(str, Enum):
    """
    解决策略
    
    定义如何解决冲突。
    """
    AUTO_MERGE = "auto_merge"  # 自动合并
    KEEP_NEWER = "keep_newer"  # 保留较新的
    KEEP_HIGHER_CONFIDENCE = "keep_higher_confidence"  # 保留置信度更高的
    KEEP_BOTH = "keep_both"  # 保留两者
    MANUAL = "manual"  # 人工裁定
    BLOCK = "block"  # 阻止晋升


@dataclass
class Conflict:
    """
    冲突记录
    
    记录检测到的冲突信息。
    """
    conflict_id: str  # 冲突 ID
    conflict_type: ConflictType  # 冲突类型
    severity: ConflictSeverity  # 严重程度
    
    record_a_id: str  # 记录 A 的 ID
    record_b_id: str  # 记录 B 的 ID
    
    description: str  # 冲突描述
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    resolution: Optional[ResolutionStrategy] = None  # 解决策略
    resolved_at: Optional[datetime] = None  # 解决时间
    resolved_by: Optional[str] = None  # 解决者
    resolution_notes: Optional[str] = None  # 解决备注
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "record_a_id": self.record_a_id,
            "record_b_id": self.record_b_id,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "resolution": self.resolution.value if self.resolution else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
        }


@dataclass
class ConflictRule:
    """
    冲突规则
    
    定义如何检测和处理特定类型的冲突。
    """
    conflict_type: ConflictType
    severity: ConflictSeverity
    auto_resolution: Optional[ResolutionStrategy] = None
    similarity_threshold: float = 0.9  # 相似度阈值（用于 overlap/duplicate 检测）
    
    def can_auto_resolve(self) -> bool:
        """是否可以自动解决"""
        return self.auto_resolution is not None and self.auto_resolution != ResolutionStrategy.MANUAL


class ConflictDetector:
    """
    冲突检测器
    
    检测记忆之间的冲突。
    """
    
    def __init__(
        self,
        rules: Optional[Dict[ConflictType, ConflictRule]] = None,
    ):
        """
        初始化冲突检测器
        
        Args:
            rules: 冲突规则
        """
        self.rules = rules or self._default_rules()
        self._existing_records: Dict[str, MemoryRecord] = {}
    
    def _default_rules(self) -> Dict[ConflictType, ConflictRule]:
        """
        默认冲突规则
        
        Returns:
            规则字典
        """
        return {
            ConflictType.CONTRADICTION: ConflictRule(
                conflict_type=ConflictType.CONTRADICTION,
                severity=ConflictSeverity.HIGH,
                auto_resolution=ResolutionStrategy.MANUAL,
            ),
            ConflictType.OVERLAP: ConflictRule(
                conflict_type=ConflictType.OVERLAP,
                severity=ConflictSeverity.MEDIUM,
                auto_resolution=ResolutionStrategy.KEEP_NEWER,
                similarity_threshold=0.7,
            ),
            ConflictType.SUPERSESSION: ConflictRule(
                conflict_type=ConflictType.SUPERSESSION,
                severity=ConflictSeverity.LOW,
                auto_resolution=ResolutionStrategy.KEEP_NEWER,
            ),
            ConflictType.DUPLICATE: ConflictRule(
                conflict_type=ConflictType.DUPLICATE,
                severity=ConflictSeverity.LOW,
                auto_resolution=ResolutionStrategy.KEEP_NEWER,
                similarity_threshold=0.9,
            ),
            ConflictType.SCOPE_CONFLICT: ConflictRule(
                conflict_type=ConflictType.SCOPE_CONFLICT,
                severity=ConflictSeverity.MEDIUM,
                auto_resolution=ResolutionStrategy.MANUAL,
            ),
        }
    
    def load_records(self, records: List[MemoryRecord]):
        """
        加载现有记录
        
        Args:
            records: 记录列表
        """
        self._existing_records = {r.id: r for r in records}
    
    def detect(
        self,
        new_record: MemoryRecord,
    ) -> List[Conflict]:
        """
        检测新记录与现有记录的冲突
        
        Args:
            new_record: 新记录
        
        Returns:
            冲突列表
        """
        conflicts = []
        
        for existing_id, existing in self._existing_records.items():
            # 检测重复
            if self._is_duplicate(new_record, existing):
                conflicts.append(self._create_conflict(
                    ConflictType.DUPLICATE,
                    new_record.id,
                    existing_id,
                    f"Duplicate content detected",
                ))
                continue
            
            # 检测重叠
            if self._is_overlap(new_record, existing):
                conflicts.append(self._create_conflict(
                    ConflictType.OVERLAP,
                    new_record.id,
                    existing_id,
                    f"Content overlap detected",
                ))
            
            # 检测作用域冲突
            if self._is_scope_conflict(new_record, existing):
                conflicts.append(self._create_conflict(
                    ConflictType.SCOPE_CONFLICT,
                    new_record.id,
                    existing_id,
                    f"Scope conflict: {new_record.scope.value} vs {existing.scope.value}",
                ))
            
            # 检测取代关系
            if self._is_supersession(new_record, existing):
                conflicts.append(self._create_conflict(
                    ConflictType.SUPERSESSION,
                    new_record.id,
                    existing_id,
                    f"New record may supersede existing",
                ))
        
        return conflicts
    
    def _is_duplicate(self, a: MemoryRecord, b: MemoryRecord) -> bool:
        """
        检测是否为重复
        
        Args:
            a: 记录 A
            b: 记录 B
        
        Returns:
            是否重复
        """
        rule = self.rules.get(ConflictType.DUPLICATE)
        threshold = rule.similarity_threshold if rule else 0.9
        
        # 比较内容相似度
        similarity = difflib.SequenceMatcher(None, a.content, b.content).ratio()
        
        return similarity >= threshold
    
    def _is_overlap(self, a: MemoryRecord, b: MemoryRecord) -> bool:
        """
        检测是否有重叠
        
        Args:
            a: 记录 A
            b: 记录 B
        
        Returns:
            是否重叠
        """
        rule = self.rules.get(ConflictType.OVERLAP)
        threshold = rule.similarity_threshold if rule else 0.7
        
        # 比较内容相似度
        similarity = difflib.SequenceMatcher(None, a.content, b.content).ratio()
        
        # 重叠阈值低于重复
        return 0.5 <= similarity < (rule.similarity_threshold if rule else 0.9)
    
    def _is_scope_conflict(self, a: MemoryRecord, b: MemoryRecord) -> bool:
        """
        检测作用域冲突
        
        Args:
            a: 记录 A
            b: 记录 B
        
        Returns:
            是否有作用域冲突
        """
        # 相同作用域和限定符的记录不应该有冲突
        if a.scope == b.scope and a.scope_qualifier == b.scope_qualifier:
            return False
        
        # 不同作用域的记录可能有冲突（需要人工裁定）
        if a.scope != b.scope and a.scope != MemoryScope.GLOBAL and b.scope != MemoryScope.GLOBAL:
            return True
        
        return False
    
    def _is_supersession(self, a: MemoryRecord, b: MemoryRecord) -> bool:
        """
        检测是否为取代关系
        
        Args:
            a: 记录 A（新）
            b: 记录 B（旧）
        
        Returns:
            是否取代
        """
        # 如果新记录的创建时间晚于旧记录，且内容相似，则可能取代
        if a.created_at > b.created_at:
            similarity = difflib.SequenceMatcher(None, a.content, b.content).ratio()
            return similarity >= 0.5
        
        return False
    
    def _create_conflict(
        self,
        conflict_type: ConflictType,
        record_a_id: str,
        record_b_id: str,
        description: str,
    ) -> Conflict:
        """
        创建冲突记录
        
        Args:
            conflict_type: 冲突类型
            record_a_id: 记录 A ID
            record_b_id: 记录 B ID
            description: 描述
        
        Returns:
            Conflict
        """
        rule = self.rules.get(conflict_type)
        severity = rule.severity if rule else ConflictSeverity.MEDIUM
        
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d%H%M%S')}_{record_a_id[:8]}"
        
        return Conflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            severity=severity,
            record_a_id=record_a_id,
            record_b_id=record_b_id,
            description=description,
        )


class ConflictResolver:
    """
    冲突解决器
    
    解决检测到的冲突。
    """
    
    def __init__(
        self,
        detector: Optional[ConflictDetector] = None,
    ):
        """
        初始化冲突解决器
        
        Args:
            detector: 冲突检测器
        """
        self.detector = detector or ConflictDetector()
        self._conflicts: Dict[str, Conflict] = {}
    
    def detect_and_resolve(
        self,
        new_record: MemoryRecord,
        auto_resolve: bool = True,
    ) -> tuple[List[Conflict], List[Conflict]]:
        """
        检测并解决冲突
        
        Args:
            new_record: 新记录
            auto_resolve: 是否自动解决
        
        Returns:
            (all_conflicts, unresolved_conflicts)
        """
        conflicts = self.detector.detect(new_record)
        
        unresolved = []
        
        for conflict in conflicts:
            self._conflicts[conflict.conflict_id] = conflict
            
            rule = self.detector.rules.get(conflict.conflict_type)
            
            if auto_resolve and rule and rule.can_auto_resolve():
                self._auto_resolve(conflict, rule.auto_resolution)
            else:
                unresolved.append(conflict)
        
        return conflicts, unresolved
    
    def _auto_resolve(
        self,
        conflict: Conflict,
        strategy: ResolutionStrategy,
    ):
        """
        自动解决冲突
        
        Args:
            conflict: 冲突
            strategy: 解决策略
        """
        conflict.resolution = strategy
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by = "auto"
        conflict.resolution_notes = f"Auto-resolved using {strategy.value} strategy"
    
    def manual_resolve(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy,
        resolved_by: str,
        notes: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        人工解决冲突
        
        Args:
            conflict_id: 冲突 ID
            strategy: 解决策略
            resolved_by: 解决者
            notes: 备注
        
        Returns:
            (success, error)
        """
        conflict = self._conflicts.get(conflict_id)
        
        if not conflict:
            return False, f"Conflict not found: {conflict_id}"
        
        if conflict.resolved_at:
            return False, f"Conflict already resolved: {conflict_id}"
        
        conflict.resolution = strategy
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by = resolved_by
        conflict.resolution_notes = notes
        
        return True, None
    
    def has_blocking_conflicts(self, conflicts: List[Conflict]) -> bool:
        """
        检查是否有阻塞晋升的冲突
        
        Args:
            conflicts: 冲突列表
        
        Returns:
            是否有阻塞冲突
        """
        for conflict in conflicts:
            if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                if not conflict.resolution:
                    return True
        
        return False
    
    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        """
        获取冲突
        
        Args:
            conflict_id: 冲突 ID
        
        Returns:
            Conflict
        """
        return self._conflicts.get(conflict_id)
    
    def list_unresolved(self, limit: int = 100) -> List[Conflict]:
        """
        列出未解决的冲突
        
        Args:
            limit: 返回数量
        
        Returns:
            冲突列表
        """
        unresolved = [
            c for c in self._conflicts.values()
            if not c.resolved_at
        ]
        
        # 按严重程度排序
        severity_order = {
            ConflictSeverity.CRITICAL: 0,
            ConflictSeverity.HIGH: 1,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 3,
        }
        
        unresolved.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return unresolved[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        total = len(self._conflicts)
        resolved = sum(1 for c in self._conflicts.values() if c.resolved_at)
        unresolved = total - resolved
        
        by_type = {}
        by_severity = {}
        
        for conflict in self._conflicts.values():
            type_name = conflict.conflict_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            severity_name = conflict.severity.value
            by_severity[severity_name] = by_severity.get(severity_name, 0) + 1
        
        return {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "by_type": by_type,
            "by_severity": by_severity,
        }


def create_conflict_resolver(
    rules: Optional[Dict[ConflictType, ConflictRule]] = None,
) -> ConflictResolver:
    """
    便捷函数：创建冲突解决器
    
    Args:
        rules: 冲突规则
    
    Returns:
        ConflictResolver 实例
    """
    detector = ConflictDetector(rules=rules)
    return ConflictResolver(detector=detector)
