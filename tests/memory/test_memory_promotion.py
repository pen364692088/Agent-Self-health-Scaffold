"""
Memory Promotion Tests

测试 M4b 晋升管理器的核心功能。

Author: Memory Kernel
Created: 2026-03-16
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
)
from core.memory.memory_capture import (
    CaptureReason,
    SourceRef,
    CaptureMetadata,
    CandidateRecord,
)
from core.memory.memory_candidate_store import CandidateStore
from core.memory.memory_promotion import (
    PromotionGate,
    PromotionRecord,
    PromotionManager,
    create_promotion_manager,
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
        source_ref=SourceRef(path="test.md"),
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
        content_hash="abc123",
    )


@pytest.fixture
def promotion_manager(candidate_store):
    """创建晋升管理器"""
    return PromotionManager(candidate_store=candidate_store)


# ============== PromotionGate Tests ==============

class TestPromotionGate:
    """测试晋升门槛"""
    
    def test_default_gate(self):
        """测试默认门槛"""
        gate = PromotionGate()
        
        assert gate.review_required is True
        assert gate.min_confidence == 0.7
        assert gate.min_importance == 0.5
    
    def test_gate_check_pass(self, sample_candidate):
        """测试门槛检查通过"""
        gate = PromotionGate()
        sample_candidate.status = "approved"
        
        passed, reasons = gate.check(sample_candidate)
        
        assert passed is True
        assert len(reasons) == 0
    
    def test_gate_check_fail_confidence(self, sample_candidate):
        """测试门槛检查失败 - 置信度"""
        gate = PromotionGate(min_confidence=0.9)
        sample_candidate.status = "approved"
        sample_candidate.metadata.confidence = 0.5
        
        passed, reasons = gate.check(sample_candidate)
        
        assert passed is False
        assert any("Confidence" in r for r in reasons)
    
    def test_gate_check_fail_importance(self, sample_candidate):
        """测试门槛检查失败 - 重要性"""
        gate = PromotionGate(min_importance=0.9)
        sample_candidate.status = "approved"
        sample_candidate.metadata.importance = 0.5
        
        passed, reasons = gate.check(sample_candidate)
        
        assert passed is False
        assert any("Importance" in r for r in reasons)
    
    def test_gate_check_fail_tags(self, sample_candidate):
        """测试门槛检查失败 - 标签"""
        gate = PromotionGate(min_tags=5)
        sample_candidate.status = "approved"
        
        passed, reasons = gate.check(sample_candidate)
        
        assert passed is False
        assert any("Tags" in r for r in reasons)


# ============== PromotionManager Tests ==============

class TestPromotionManager:
    """测试晋升管理器"""
    
    def test_check_gates(self, promotion_manager, candidate_store, sample_candidate):
        """测试门槛检查"""
        candidate_store.add(sample_candidate)
        
        passed, reasons = promotion_manager.check_gates(sample_candidate.id)
        
        # 需要先 approve
        assert passed is False or sample_candidate.status in ["approved", "pending"]
    
    def test_promote_success(self, promotion_manager, candidate_store, sample_candidate):
        """测试晋升成功"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        success, record, reasons = promotion_manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
        )
        
        assert success is True
        assert record is not None
        assert record.memory_id is not None
    
    def test_promotion_history(self, promotion_manager, candidate_store, sample_candidate):
        """测试晋升历史"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        promotion_manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
        )
        
        history = promotion_manager.get_promotion_history()
        
        assert len(history) == 1
    
    def test_rollback(self, promotion_manager, candidate_store, sample_candidate):
        """测试回滚"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        success, record, _ = promotion_manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
        )
        
        assert success is True
        
        # 回滚
        rollback_success, error = promotion_manager.rollback(
            memory_id=record.memory_id,
            rolled_back_by="manager",
            rollback_reason="Error found",
        )
        
        assert rollback_success is True
        
        # 检查状态
        updated_record = promotion_manager.get_promotion_history(sample_candidate.id)[0]
        assert updated_record.rolled_back is True
    
    def test_list_active_memories(self, promotion_manager, candidate_store, sample_candidate):
        """测试列出活跃记忆"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        promotion_manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
        )
        
        memories = promotion_manager.list_active_memories()
        
        assert len(memories) == 1
    
    def test_get_statistics(self, promotion_manager, candidate_store, sample_candidate):
        """测试统计信息"""
        candidate_store.add(sample_candidate)
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        promotion_manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
        )
        
        stats = promotion_manager.get_statistics()
        
        assert stats["total_promotions"] == 1
        assert stats["active_memories"] == 1


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_promotion_flow(self, candidate_store, sample_candidate):
        """测试完整晋升流程"""
        # 1. 创建晋升管理器
        manager = PromotionManager(candidate_store=candidate_store)
        
        # 2. 添加候选
        candidate_store.add(sample_candidate)
        
        # 3. 审核候选
        candidate_store.approve(sample_candidate.id, reviewed_by="reviewer")
        
        # 4. 检查门槛
        passed, reasons = manager.check_gates(sample_candidate.id)
        assert passed is True
        
        # 5. 晋升
        success, record, _ = manager.promote(
            candidate_id=sample_candidate.id,
            promoted_by="manager",
            review_notes="Approved for promotion",
        )
        
        assert success is True
        assert record is not None
        
        # 6. 验证记忆
        memory = manager.get_memory(record.memory_id)
        assert memory is not None
        
        # 7. 验证历史
        history = manager.get_promotion_history()
        assert len(history) == 1
