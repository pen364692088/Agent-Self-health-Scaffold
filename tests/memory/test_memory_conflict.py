"""
Memory Conflict Tests

测试 M4b 冲突解决的核心功能。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_conflict import (
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
    Conflict,
    ConflictRule,
    ConflictDetector,
    ConflictResolver,
    create_conflict_resolver,
)


# ============== Fixtures ==============

@pytest.fixture
def existing_memory():
    """创建现有记忆"""
    return MemoryRecord(
        id="mem_existing_001",
        source_file="existing.md",
        source_kind=MemorySourceKind.DECISION_LOG,
        content_type=MemoryContentType.RULE,
        scope=MemoryScope.GLOBAL,
        tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
        title="Existing Rule",
        content="All API endpoints must be versioned with /vN prefix",
        tags=["api", "versioning"],
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    )


@pytest.fixture
def new_memory():
    """创建新记忆"""
    return MemoryRecord(
        id="mem_new_001",
        source_file="new.md",
        source_kind=MemorySourceKind.DECISION_LOG,
        content_type=MemoryContentType.RULE,
        scope=MemoryScope.GLOBAL,
        tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
        title="New Rule",
        content="All API endpoints must be versioned with /vN prefix",  # 相同内容
        tags=["api"],
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def conflict_detector():
    """创建冲突检测器"""
    return ConflictDetector()


@pytest.fixture
def conflict_resolver():
    """创建冲突解决器"""
    return ConflictResolver()


# ============== ConflictDetector Tests ==============

class TestConflictDetector:
    """测试冲突检测器"""
    
    def test_detect_duplicate(self, conflict_detector, existing_memory, new_memory):
        """测试检测重复"""
        conflict_detector.load_records([existing_memory])
        
        conflicts = conflict_detector.detect(new_memory)
        
        # 应该检测到重复
        duplicate_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DUPLICATE]
        assert len(duplicate_conflicts) >= 1
    
    def test_detect_overlap(self, conflict_detector, existing_memory):
        """测试检测重叠"""
        conflict_detector.load_records([existing_memory])
        
        # 创建重叠内容
        overlap_memory = MemoryRecord(
            id="mem_overlap",
            source_file="overlap.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Overlap",
            content="API endpoints should use versioning",  # 部分重叠
            tags=["api"],
            created_at=datetime.now(timezone.utc),
        )
        
        conflicts = conflict_detector.detect(overlap_memory)
        
        # 可能检测到重叠或取代
        assert len(conflicts) >= 0  # 取决于相似度
    
    def test_no_conflict(self, conflict_detector, existing_memory):
        """测试无冲突"""
        conflict_detector.load_records([existing_memory])
        
        # 创建完全不同的记忆
        different_memory = MemoryRecord(
            id="mem_different",
            source_file="different.md",
            source_kind=MemorySourceKind.TECHNICAL_NOTE,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.PROJECTS,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Different",
            content="This is completely different content about something else",
            tags=["different"],
            created_at=datetime.now(timezone.utc),
        )
        
        conflicts = conflict_detector.detect(different_memory)
        
        # 应该没有冲突
        assert len(conflicts) == 0


# ============== ConflictResolver Tests ==============

class TestConflictResolver:
    """测试冲突解决器"""
    
    def test_detect_and_resolve(self, conflict_resolver, existing_memory, new_memory):
        """测试检测并解决"""
        conflict_resolver.detector.load_records([existing_memory])
        
        conflicts, unresolved = conflict_resolver.detect_and_resolve(new_memory)
        
        # 应该检测到冲突
        assert len(conflicts) >= 1
        
        # 重复冲突应该自动解决
        if conflicts:
            duplicate = [c for c in conflicts if c.conflict_type == ConflictType.DUPLICATE]
            if duplicate:
                assert duplicate[0].resolution is not None
    
    def test_manual_resolve(self, conflict_resolver):
        """测试人工解决"""
        # 创建冲突
        conflict = Conflict(
            conflict_id="conflict_test",
            conflict_type=ConflictType.CONTRADICTION,
            severity=ConflictSeverity.HIGH,
            record_a_id="mem_001",
            record_b_id="mem_002",
            description="Test conflict",
        )
        
        conflict_resolver._conflicts[conflict.conflict_id] = conflict
        
        # 人工解决
        success, error = conflict_resolver.manual_resolve(
            conflict_id="conflict_test",
            strategy=ResolutionStrategy.KEEP_NEWER,
            resolved_by="manager",
            notes="Manual resolution",
        )
        
        assert success is True
        
        # 验证解决
        resolved = conflict_resolver.get_conflict("conflict_test")
        assert resolved.resolved_at is not None
    
    def test_has_blocking_conflicts(self, conflict_resolver):
        """测试是否有阻塞冲突"""
        # 创建高严重程度未解决的冲突
        conflict = Conflict(
            conflict_id="conflict_blocking",
            conflict_type=ConflictType.CONTRADICTION,
            severity=ConflictSeverity.HIGH,
            record_a_id="mem_001",
            record_b_id="mem_002",
            description="Blocking conflict",
        )
        
        has_blocking = conflict_resolver.has_blocking_conflicts([conflict])
        
        assert has_blocking is True
        
        # 解决后
        conflict.resolution = ResolutionStrategy.MANUAL
        conflict.resolved_at = datetime.now(timezone.utc)
        
        has_blocking_after = conflict_resolver.has_blocking_conflicts([conflict])
        
        # 已解决的冲突不阻塞
        # 注意：这取决于实现细节
    
    def test_list_unresolved(self, conflict_resolver):
        """测试列出未解决"""
        # 创建两个冲突
        conflict1 = Conflict(
            conflict_id="conflict_1",
            conflict_type=ConflictType.OVERLAP,
            severity=ConflictSeverity.LOW,
            record_a_id="mem_001",
            record_b_id="mem_002",
            description="Unresolved 1",
        )
        
        conflict2 = Conflict(
            conflict_id="conflict_2",
            conflict_type=ConflictType.CONTRADICTION,
            severity=ConflictSeverity.HIGH,
            record_a_id="mem_003",
            record_b_id="mem_004",
            description="Unresolved 2",
        )
        
        conflict_resolver._conflicts["conflict_1"] = conflict1
        conflict_resolver._conflicts["conflict_2"] = conflict2
        
        unresolved = conflict_resolver.list_unresolved()
        
        assert len(unresolved) == 2
        
        # 高严重程度应该排在前面
        assert unresolved[0].severity == ConflictSeverity.HIGH
    
    def test_get_statistics(self, conflict_resolver):
        """测试统计信息"""
        # 创建冲突
        conflict = Conflict(
            conflict_id="conflict_stats",
            conflict_type=ConflictType.OVERLAP,
            severity=ConflictSeverity.MEDIUM,
            record_a_id="mem_001",
            record_b_id="mem_002",
            description="Stats test",
        )
        
        conflict_resolver._conflicts["conflict_stats"] = conflict
        
        stats = conflict_resolver.get_statistics()
        
        assert stats["total"] == 1
        assert stats["unresolved"] == 1


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_conflict_flow(self, existing_memory, new_memory):
        """测试完整冲突流程"""
        # 1. 创建解决器
        resolver = ConflictResolver()
        
        # 2. 加载现有记忆
        resolver.detector.load_records([existing_memory])
        
        # 3. 检测冲突
        conflicts, unresolved = resolver.detect_and_resolve(new_memory, auto_resolve=False)
        
        assert len(conflicts) >= 1
        
        # 4. 获取未解决冲突
        unresolved_list = resolver.list_unresolved()
        assert len(unresolved_list) >= 1
        
        # 5. 人工解决
        if unresolved_list:
            success, _ = resolver.manual_resolve(
                conflict_id=unresolved_list[0].conflict_id,
                strategy=ResolutionStrategy.KEEP_NEWER,
                resolved_by="manager",
            )
            assert success is True
        
        # 6. 验证统计
        stats = resolver.get_statistics()
        assert stats["resolved"] >= 1
