"""
Memory Candidate Promotion Tests

测试 M4a 候选存储和提升功能。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryScope,
    MemoryContentType,
    TruthKnowledgeRetrieval,
    MemoryTier,
)
from core.memory.memory_capture import (
    CaptureReason,
    SourceRef,
    CaptureMetadata,
    CandidateRecord,
)
from core.memory.memory_candidate_store import (
    CandidateStore,
    PromotionResult,
    create_candidate_store,
)


# ============== Fixtures ==============

@pytest.fixture
def candidate_store():
    """创建候选存储"""
    return CandidateStore()


@pytest.fixture
def sample_candidate():
    """创建测试候选"""
    metadata = CaptureMetadata(
        capture_reason=CaptureReason(
            reason="Test promotion",
            category="manual",
        ),
        source_ref=SourceRef(
            path="memory/test.md",
            line_start=1,
            line_end=10,
        ),
        scope=MemoryScope.GLOBAL,
        importance=0.8,
        confidence=0.9,
        authority_level="high",
        tags=["test", "promotion"],
    )
    
    return CandidateRecord(
        id="cand_test_001",
        title="Test Candidate",
        content="This is a test candidate for promotion.",
        metadata=metadata,
        content_hash="abc123def456",
    )


# ============== CandidateStore CRUD Tests ==============

class TestCandidateStoreCRUD:
    """测试候选存储 CRUD"""
    
    def test_add_candidate(self, candidate_store, sample_candidate):
        """测试添加候选"""
        result = candidate_store.add(sample_candidate)
        
        assert result is True
        
        retrieved = candidate_store.get(sample_candidate.id)
        assert retrieved is not None
        assert retrieved.id == sample_candidate.id
    
    def test_add_duplicate_candidate(self, candidate_store, sample_candidate):
        """测试添加重复候选"""
        candidate_store.add(sample_candidate)
        result = candidate_store.add(sample_candidate)
        
        assert result is False
    
    def test_get_nonexistent_candidate(self, candidate_store):
        """测试获取不存在的候选"""
        result = candidate_store.get("nonexistent")
        
        assert result is None
    
    def test_update_candidate(self, candidate_store, sample_candidate):
        """测试更新候选"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.update(
            sample_candidate.id,
            review_notes="Updated",
        )
        
        assert result is True
        
        updated = candidate_store.get(sample_candidate.id)
        assert updated.review_notes == "Updated"
    
    def test_delete_candidate(self, candidate_store, sample_candidate):
        """测试删除候选"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.delete(sample_candidate.id)
        
        assert result is True
        
        deleted = candidate_store.get(sample_candidate.id)
        assert deleted is None
    
    def test_list_candidates(self, candidate_store):
        """测试列出候选"""
        for i in range(3):
            metadata = CaptureMetadata(
                capture_reason=CaptureReason(reason=f"Test {i}", category="manual"),
                source_ref=SourceRef(path=f"test{i}.md"),
                scope=MemoryScope.GLOBAL,
                importance=0.8,
                confidence=0.9,
                authority_level="medium",
            )
            candidate = CandidateRecord(
                id=f"cand_{i}",
                title=f"Candidate {i}",
                content=f"Content {i}",
                metadata=metadata,
                content_hash=f"hash_{i}",
            )
            candidate_store.add(candidate)
        
        candidates = candidate_store.list()
        
        assert len(candidates) == 3


# ============== Approve/Reject Tests ==============

class TestApproveReject:
    """测试批准和拒绝"""
    
    def test_approve_candidate(self, candidate_store, sample_candidate):
        """测试批准候选"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.approve(
            sample_candidate.id,
            reviewed_by="manager",
            review_notes="Looks good",
        )
        
        assert result is True
        
        approved = candidate_store.get(sample_candidate.id)
        assert approved.status == "approved"
        assert approved.reviewed_by == "manager"
        assert approved.review_notes == "Looks good"
    
    def test_approve_nonexistent_candidate(self, candidate_store):
        """测试批准不存在的候选"""
        result = candidate_store.approve(
            "nonexistent",
            reviewed_by="manager",
        )
        
        assert result is False
    
    def test_approve_already_approved_candidate(self, candidate_store, sample_candidate):
        """测试批准已批准的候选"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="manager")
        
        # 再次批准
        result = candidate_store.approve(
            sample_candidate.id,
            reviewed_by="another",
        )
        
        assert result is False
    
    def test_reject_candidate(self, candidate_store, sample_candidate):
        """测试拒绝候选"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.reject(
            sample_candidate.id,
            reviewed_by="manager",
            review_notes="Not relevant",
        )
        
        assert result is True
        
        rejected = candidate_store.get(sample_candidate.id)
        assert rejected.status == "rejected"
        assert rejected.reviewed_by == "manager"
    
    def test_reject_nonexistent_candidate(self, candidate_store):
        """测试拒绝不存在的候选"""
        result = candidate_store.reject(
            "nonexistent",
            reviewed_by="manager",
        )
        
        assert result is False


# ============== Promotion Tests ==============

class TestPromotion:
    """测试提升"""
    
    def test_promote_pending_candidate(self, candidate_store, sample_candidate):
        """测试提升待审核候选"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
            review_notes="Approved for knowledge layer",
        )
        
        assert result.success is True
        assert result.memory_record is not None
        assert result.memory_record.tkr_layer == TruthKnowledgeRetrieval.KNOWLEDGE
        
        # 检查候选状态
        promoted = candidate_store.get(sample_candidate.id)
        assert promoted.status == "promoted"
        assert promoted.promoted_to_id is not None
    
    def test_promote_approved_candidate(self, candidate_store, sample_candidate):
        """测试提升已批准候选"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            reviewed_by="manager",
        )
        
        assert result.success is True
    
    def test_promote_rejected_candidate(self, candidate_store, sample_candidate):
        """测试提升已拒绝候选"""
        candidate_store.add(sample_candidate)
        candidate_store.reject(sample_candidate.id, reviewed_by="manager")
        
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
        )
        
        assert result.success is False
        assert "Invalid status" in result.error
    
    def test_promote_nonexistent_candidate(self, candidate_store):
        """测试提升不存在的候选"""
        result = candidate_store.promote(
            candidate_id="nonexistent",
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
        )
        
        assert result.success is False
        assert "not found" in result.error
    
    def test_promoted_memory_attributes(self, candidate_store, sample_candidate):
        """测试提升后的记忆属性"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            reviewed_by="manager",
        )
        
        memory = result.memory_record
        
        assert memory.title == sample_candidate.title
        assert memory.content == sample_candidate.content
        assert memory.scope == sample_candidate.metadata.scope
        assert memory.confidence == sample_candidate.metadata.confidence
        assert memory.importance == sample_candidate.metadata.importance
        assert memory.tier == MemoryTier.WARM
    
    def test_get_promoted_memory(self, candidate_store, sample_candidate):
        """测试获取提升后的记忆"""
        candidate_store.add(sample_candidate)
        
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
        )
        
        memory_id = result.memory_record.id
        retrieved = candidate_store.get_promoted_memory(memory_id)
        
        assert retrieved is not None
        assert retrieved.id == memory_id
    
    def test_list_promoted_memories(self, candidate_store):
        """测试列出提升后的记忆"""
        for i in range(3):
            metadata = CaptureMetadata(
                capture_reason=CaptureReason(reason=f"Test {i}", category="manual"),
                source_ref=SourceRef(path=f"test{i}.md"),
                scope=MemoryScope.GLOBAL,
                importance=0.8,
                confidence=0.9,
                authority_level="medium",
            )
            candidate = CandidateRecord(
                id=f"cand_{i}",
                title=f"Candidate {i}",
                content=f"Content {i}",
                metadata=metadata,
                content_hash=f"hash_{i}",
            )
            candidate_store.add(candidate)
            candidate_store.promote(
                candidate_id=f"cand_{i}",
                target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
                reviewed_by="manager",
            )
        
        memories = candidate_store.list_promoted_memories()
        
        assert len(memories) == 3


# ============== Statistics Tests ==============

class TestStatistics:
    """测试统计信息"""
    
    def test_get_statistics(self, candidate_store, sample_candidate):
        """测试统计信息"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="manager")
        
        stats = candidate_store.get_statistics()
        
        assert stats["total_candidates"] == 1
        assert stats["by_status"]["approved"] == 1
        assert stats["promoted_memories"] == 0
    
    def test_statistics_after_promotion(self, candidate_store, sample_candidate):
        """测试提升后的统计信息"""
        candidate_store.add(sample_candidate)
        candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
        )
        
        stats = candidate_store.get_statistics()
        
        assert stats["by_status"]["promoted"] == 1
        assert stats["promoted_memories"] == 1


# ============== Export Tests ==============

class TestExport:
    """测试导出"""
    
    def test_export_to_json(self, candidate_store, sample_candidate, tmp_path):
        """测试导出到 JSON"""
        candidate_store.add(sample_candidate)
        
        export_path = str(tmp_path / "export.json")
        candidate_store.export_to_json(export_path)
        
        import json
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert "candidates" in data
        assert len(data["candidates"]) == 1


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_promotion_flow(self, candidate_store, sample_candidate):
        """测试完整提升流程"""
        # 1. 添加候选
        candidate_store.add(sample_candidate)
        
        # 2. 检查状态
        assert sample_candidate.status == "pending"
        
        # 3. 批准
        candidate_store.approve(
            sample_candidate.id,
            reviewed_by="reviewer",
            review_notes="Good candidate",
        )
        
        # 4. 提升
        result = candidate_store.promote(
            candidate_id=sample_candidate.id,
            target_tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            reviewed_by="manager",
            review_notes="Promoted to truth layer",
        )
        
        # 5. 验证结果
        assert result.success is True
        assert result.memory_record.tkr_layer == TruthKnowledgeRetrieval.TRUTH
        
        # 6. 验证状态
        promoted = candidate_store.get(sample_candidate.id)
        assert promoted.status == "promoted"
        assert promoted.promoted_to_id == result.memory_record.id
    
    def test_multiple_candidates_different_states(self, candidate_store):
        """测试多个候选的不同状态"""
        # 创建 5 个候选
        for i in range(5):
            metadata = CaptureMetadata(
                capture_reason=CaptureReason(reason=f"Test {i}", category="manual"),
                source_ref=SourceRef(path=f"test{i}.md"),
                scope=MemoryScope.GLOBAL,
                importance=0.8,
                confidence=0.9,
                authority_level="medium",
            )
            candidate = CandidateRecord(
                id=f"cand_{i}",
                title=f"Candidate {i}",
                content=f"Content {i}",
                metadata=metadata,
                content_hash=f"hash_{i}",
            )
            candidate_store.add(candidate)
        
        # 批准 2 个
        candidate_store.approve("cand_0", reviewed_by="manager")
        candidate_store.approve("cand_1", reviewed_by="manager")
        
        # 拒绝 1 个
        candidate_store.reject("cand_2", reviewed_by="manager")
        
        # 提升 1 个
        candidate_store.promote(
            candidate_id="cand_0",
            target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            reviewed_by="manager",
        )
        
        # 检查统计
        stats = candidate_store.get_statistics()
        
        assert stats["by_status"]["pending"] == 2  # cand_3, cand_4
        assert stats["by_status"]["approved"] == 1  # cand_1
        assert stats["by_status"]["rejected"] == 1  # cand_2
        assert stats["by_status"]["promoted"] == 1  # cand_0
        assert stats["promoted_memories"] == 1
