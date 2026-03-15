"""
Memory Capture Tests

测试 M4a 捕获引擎的核心功能。

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
    MemorySourceKind,
)
from core.memory.memory_capture import (
    CaptureEngine,
    CaptureWhitelist,
    CaptureReason,
    SourceRef,
    CaptureMetadata,
    CandidateRecord,
    create_capture_engine,
)


# ============== Fixtures ==============

@pytest.fixture
def capture_metadata():
    """创建测试元数据"""
    return CaptureMetadata(
        capture_reason=CaptureReason(
            reason="Test capture",
            category="manual",
            triggered_by="test",
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
    )


@pytest.fixture
def capture_engine():
    """创建捕获引擎"""
    return CaptureEngine()


# ============== CaptureWhitelist Tests ==============

class TestCaptureWhitelist:
    """测试白名单"""
    
    def test_default_whitelist(self):
        """测试默认白名单"""
        whitelist = CaptureWhitelist()
        
        assert whitelist.min_confidence == 0.5
        assert whitelist.min_importance == 0.3
    
    def test_is_source_allowed(self):
        """测试来源白名单"""
        whitelist = CaptureWhitelist()
        
        assert whitelist.is_source_allowed(MemorySourceKind.SESSION_LOG)
        assert whitelist.is_source_allowed(MemorySourceKind.DECISION_LOG)
    
    def test_is_content_type_allowed(self):
        """测试内容类型白名单"""
        whitelist = CaptureWhitelist()
        
        assert whitelist.is_content_type_allowed(MemoryContentType.RULE)
        assert whitelist.is_content_type_allowed(MemoryContentType.FACT)
    
    def test_meets_thresholds(self):
        """测试阈值"""
        whitelist = CaptureWhitelist()
        
        assert whitelist.meets_thresholds(0.6, 0.4)
        assert not whitelist.meets_thresholds(0.4, 0.4)
        assert not whitelist.meets_thresholds(0.6, 0.2)


# ============== CaptureEngine Tests ==============

class TestCaptureEngine:
    """测试捕获引擎"""
    
    def test_capture_basic(self, capture_engine, capture_metadata):
        """测试基本捕获"""
        candidate = capture_engine.capture(
            title="Test Title",
            content="This is a test content for capture.",
            metadata=capture_metadata,
        )
        
        assert candidate is not None
        assert candidate.title == "Test Title"
        assert candidate.status == "pending"
    
    def test_capture_with_whitelist(self, capture_metadata):
        """测试白名单捕获"""
        whitelist = CaptureWhitelist(
            min_confidence=0.7,
            min_importance=0.5,
        )
        engine = CaptureEngine(whitelist=whitelist)
        
        # 低于阈值
        metadata_low = CaptureMetadata(
            capture_reason=CaptureReason(reason="test", category="manual"),
            source_ref=SourceRef(path="test.md"),
            scope=MemoryScope.GLOBAL,
            importance=0.4,
            confidence=0.6,
            authority_level="low",
        )
        
        candidate = engine.capture(
            title="Low quality",
            content="Some content here",
            metadata=metadata_low,
        )
        
        assert candidate is None
    
    def test_capture_noise_filter_empty(self, capture_engine, capture_metadata):
        """测试噪音过滤 - 空内容"""
        candidate = capture_engine.capture(
            title="Empty",
            content="",
            metadata=capture_metadata,
        )
        
        assert candidate is None
    
    def test_capture_noise_filter_too_short(self, capture_engine, capture_metadata):
        """测试噪音过滤 - 过短"""
        candidate = capture_engine.capture(
            title="Short",
            content="Hi",
            metadata=capture_metadata,
        )
        
        assert candidate is None
    
    def test_capture_noise_filter_whitespace(self, capture_engine, capture_metadata):
        """测试噪音过滤 - 纯空白"""
        candidate = capture_engine.capture(
            title="Whitespace",
            content="   \n\t  ",
            metadata=capture_metadata,
        )
        
        assert candidate is None
    
    def test_capture_deduplication(self, capture_engine, capture_metadata):
        """测试去重"""
        # 第一次捕获
        candidate1 = capture_engine.capture(
            title="Original",
            content="This is unique content.",
            metadata=capture_metadata,
        )
        
        assert candidate1 is not None
        
        # 第二次捕获相同内容
        candidate2 = capture_engine.capture(
            title="Duplicate",
            content="This is unique content.",  # 相同内容
            metadata=capture_metadata,
        )
        
        assert candidate2 is None
    
    def test_capture_missing_required_field(self, capture_engine):
        """测试缺少必填字段"""
        # 缺少 capture_reason
        metadata = CaptureMetadata(
            capture_reason=CaptureReason(reason="", category="manual"),  # 空原因
            source_ref=SourceRef(path="test.md"),
            scope=MemoryScope.GLOBAL,
            importance=0.8,
            confidence=0.9,
            authority_level="high",
        )
        
        candidate = capture_engine.capture(
            title="Missing field",
            content="Some content here",
            metadata=metadata,
        )
        
        assert candidate is None
    
    def test_capture_importance_out_of_range(self, capture_engine):
        """测试重要性超出范围"""
        metadata = CaptureMetadata(
            capture_reason=CaptureReason(reason="test", category="manual"),
            source_ref=SourceRef(path="test.md"),
            scope=MemoryScope.GLOBAL,
            importance=1.5,  # 超出范围
            confidence=0.9,
            authority_level="high",
        )
        
        candidate = capture_engine.capture(
            title="Invalid importance",
            content="Some content here",
            metadata=metadata,
        )
        
        assert candidate is None
    
    def test_capture_confidence_out_of_range(self, capture_engine):
        """测试置信度超出范围"""
        metadata = CaptureMetadata(
            capture_reason=CaptureReason(reason="test", category="manual"),
            source_ref=SourceRef(path="test.md"),
            scope=MemoryScope.GLOBAL,
            importance=0.8,
            confidence=-0.1,  # 超出范围
            authority_level="high",
        )
        
        candidate = capture_engine.capture(
            title="Invalid confidence",
            content="Some content here",
            metadata=metadata,
        )
        
        assert candidate is None
    
    def test_get_candidate(self, capture_engine, capture_metadata):
        """测试获取候选"""
        candidate = capture_engine.capture(
            title="Test",
            content="Test content here.",
            metadata=capture_metadata,
        )
        
        assert candidate is not None
        
        retrieved = capture_engine.get_candidate(candidate.id)
        
        assert retrieved is not None
        assert retrieved.id == candidate.id
    
    def test_list_candidates(self, capture_engine, capture_metadata):
        """测试列出候选"""
        # 捕获多个
        for i in range(3):
            capture_engine.capture(
                title=f"Test {i}",
                content=f"Content {i} here.",
                metadata=capture_metadata,
            )
        
        candidates = capture_engine.list_candidates()
        
        assert len(candidates) == 3
    
    def test_list_candidates_by_status(self, capture_engine, capture_metadata):
        """测试按状态列出候选"""
        candidate = capture_engine.capture(
            title="Test",
            content="Test content here.",
            metadata=capture_metadata,
        )
        
        # 修改状态
        candidate.status = "approved"
        
        pending = capture_engine.list_candidates(status="pending")
        approved = capture_engine.list_candidates(status="approved")
        
        assert len(pending) == 0
        assert len(approved) == 1
    
    def test_get_statistics(self, capture_engine, capture_metadata):
        """测试统计信息"""
        capture_engine.capture(
            title="Test 1",
            content="Content 1.",
            metadata=capture_metadata,
        )
        capture_engine.capture(
            title="Test 2",
            content="Content 2.",
            metadata=capture_metadata,
        )
        
        stats = capture_engine.get_statistics()
        
        assert stats["total"] == 2
        assert "by_status" in stats


# ============== Content Hash Tests ==============

class TestContentHash:
    """测试内容哈希"""
    
    def test_compute_content_hash(self, capture_engine):
        """测试计算内容哈希"""
        hash1 = capture_engine.compute_content_hash("Test content")
        hash2 = capture_engine.compute_content_hash("Test content")
        hash3 = capture_engine.compute_content_hash("Different content")
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_content_hash_normalization(self, capture_engine):
        """测试内容哈希规范化"""
        hash1 = capture_engine.compute_content_hash("Test Content")
        hash2 = capture_engine.compute_content_hash("  test content  ")
        
        assert hash1 == hash2


# ============== CandidateRecord Tests ==============

class TestCandidateRecord:
    """测试候选记录"""
    
    def test_to_dict(self, capture_metadata):
        """测试转换为字典"""
        candidate = CandidateRecord(
            id="cand_test",
            title="Test",
            content="Content",
            metadata=capture_metadata,
            content_hash="abc123",
        )
        
        data = candidate.to_dict()
        
        assert data["id"] == "cand_test"
        assert data["title"] == "Test"
        assert data["status"] == "pending"


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_capture_flow(self, capture_engine, capture_metadata):
        """测试完整捕获流程"""
        # 1. 捕获
        candidate = capture_engine.capture(
            title="Integration Test",
            content="This is an integration test for the capture engine.",
            metadata=capture_metadata,
        )
        
        assert candidate is not None
        assert candidate.status == "pending"
        
        # 2. 获取
        retrieved = capture_engine.get_candidate(candidate.id)
        assert retrieved is not None
        
        # 3. 统计
        stats = capture_engine.get_statistics()
        assert stats["total"] == 1
    
    def test_multiple_captures(self, capture_engine, capture_metadata):
        """测试多次捕获"""
        for i in range(5):
            capture_engine.capture(
                title=f"Capture {i}",
                content=f"Unique content {i}.",
                metadata=capture_metadata,
            )
        
        stats = capture_engine.get_statistics()
        assert stats["total"] == 5
