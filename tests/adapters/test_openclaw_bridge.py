"""
Tests for OpenClaw Bridge - Shadow Mode

验证 Bridge 的核心功能：
1. 正常召回
2. Fail-open 行为
3. 预算截断
4. 任务类型检测
5. Candidate 隔离

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
    MemoryRecord,
    MemoryScope,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
    MemoryTier,
    MemoryStatus,
    MemorySource,
)
from adapters.openclaw_bridge import (
    BridgeRequest,
    BridgeResponse,
    RecallSuggestion,
    BridgeTrace,
    OpenClawBridge,
    create_bridge,
)


def create_test_record(
    id: str = "mem_20260316_001",
    title: str = "Test Record",
    content: str = "This is a test memory record content.",
    scope: MemoryScope = MemoryScope.GLOBAL,
    tkr_layer: TruthKnowledgeRetrieval = TruthKnowledgeRetrieval.KNOWLEDGE,
) -> MemoryRecord:
    """创建测试用的 MemoryRecord"""
    return MemoryRecord(
        id=id,
        scope=scope,
        source_kind=MemorySourceKind.SESSION_LOG,
        content_type=MemoryContentType.FACT,
        tkr_layer=tkr_layer,
        title=title,
        content=content,
        source_file="test/session.md",
        tier=MemoryTier.WARM,
        status=MemoryStatus.ACTIVE,
    )


class TestBridgeRequest:
    """测试 BridgeRequest"""
    
    def test_create_request(self):
        """测试创建请求"""
        request = BridgeRequest(
            query="test query",
            context="some context",
            task_type="coding",
        )
        
        assert request.query == "test query"
        assert request.context == "some context"
        assert request.task_type == "coding"
        assert request.max_suggestions == 5
        assert request.timeout_ms == 1000
    
    def test_default_values(self):
        """测试默认值"""
        request = BridgeRequest(query="test")
        
        assert request.context is None
        assert request.task_type is None
        assert request.max_suggestions == 5
        assert request.timeout_ms == 1000


class TestRecallSuggestion:
    """测试 RecallSuggestion"""
    
    def test_create_suggestion(self):
        """测试创建建议"""
        suggestion = RecallSuggestion(
            record_id="mem_001",
            title="Test Title",
            content_preview="Preview...",
            relevance_score=0.9,
            source="test.md",
            scope="global",
            tkr_layer="knowledge",
        )
        
        assert suggestion.record_id == "mem_001"
        assert suggestion.relevance_score == 0.9
        assert suggestion.use_count == 0


class TestBridgeTrace:
    """测试 BridgeTrace"""
    
    def test_create_trace(self):
        """测试创建追踪"""
        now = datetime.now(timezone.utc)
        trace = BridgeTrace(
            request_id="bridge_001",
            start_time=now,
        )
        
        assert trace.request_id == "bridge_001"
        assert trace.start_time == now
        assert trace.end_time is None
        assert trace.success is True
        assert trace.error is None


class TestOpenClawBridge:
    """测试 OpenClawBridge"""
    
    def test_create_bridge(self):
        """测试创建 Bridge"""
        bridge = create_bridge()
        
        assert bridge is not None
        assert bridge._max_content_preview == 200
    
    def test_recall_empty_records(self):
        """测试空记录召回"""
        bridge = create_bridge()
        request = BridgeRequest(query="test query")
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert response.suggestions == []
        assert response.trace is not None
    
    def test_recall_with_records(self):
        """测试有记录召回"""
        records = [
            create_test_record(
                id="mem_001",
                title="Test Title 1",
                content="Test content 1",
            ),
            create_test_record(
                id="mem_002",
                title="Test Title 2",
                content="Test content 2",
            ),
        ]
        
        bridge = create_bridge(approved_records=records)
        request = BridgeRequest(query="test", max_suggestions=5)
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert response.trace is not None
        assert response.trace.success is True
    
    def test_fail_open_on_error(self):
        """测试 fail-open 行为"""
        bridge = create_bridge()
        
        # 无效请求（负超时）
        request = BridgeRequest(query="test", timeout_ms=-1)
        
        response = bridge.recall(request)
        
        # 应该返回失败但不抛异常
        assert response.success is False
        assert response.error is not None
        assert response.suggestions == []
    
    def test_content_truncation(self):
        """测试内容截断"""
        long_content = "x" * 500  # 超过默认 200
        bridge = create_bridge(max_content_preview=100)
        
        truncated = bridge._truncate_content(long_content)
        
        assert len(truncated) <= 100
        assert truncated.endswith("...")
    
    def test_task_type_detection(self):
        """测试任务类型检测"""
        bridge = create_bridge()
        
        # Coding 任务
        assert bridge._detect_task_type("implement new feature") == "coding"
        assert bridge._detect_task_type("fix this bug") == "coding"
        
        # Review 任务
        assert bridge._detect_task_type("review the code") == "review"
        
        # Docs 任务
        assert bridge._detect_task_type("update docs") == "docs"
        
        # General
        assert bridge._detect_task_type("random query") == "general"
    
    def test_get_stats(self):
        """测试统计信息"""
        bridge = create_bridge()
        
        # 执行几次请求
        request = BridgeRequest(query="test")
        bridge.recall(request)
        bridge.recall(request)
        
        stats = bridge.get_stats()
        
        assert stats["request_count"] == 2
        assert stats["avg_duration_ms"] >= 0


class TestCandidateIsolation:
    """测试 Candidate 隔离"""
    
    def test_candidate_not_returned(self):
        """测试 candidate 不会返回"""
        # 只创建 approved 记录
        records = [
            create_test_record(
                id="mem_approved",
                title="Approved Record",
                content="Approved content",
            ),
        ]
        
        bridge = create_bridge(approved_records=records)
        
        # RecallEngine 默认 mode="shadow"，不包含 candidates
        assert bridge._recall_engine._config.mode == "shadow"
        assert bridge._recall_engine._config.include_candidates is False


class TestFailOpenBehavior:
    """测试 Fail-Open 行为"""
    
    def test_exception_returns_empty_suggestions(self):
        """测试异常返回空建议"""
        bridge = create_bridge()
        
        # 触发错误
        request = BridgeRequest(query="test", timeout_ms=-1)
        response = bridge.recall(request)
        
        assert response.success is False
        assert response.suggestions == []
        assert response.error is not None
    
    def test_trace_records_error(self):
        """测试追踪记录错误"""
        bridge = create_bridge()
        
        request = BridgeRequest(query="test", timeout_ms=-1)
        response = bridge.recall(request)
        
        assert response.trace is not None
        assert response.trace.success is False
        assert response.trace.error is not None


class TestBudgetTruncation:
    """测试预算截断"""
    
    def test_truncate_by_budget(self):
        """测试按预算截断"""
        bridge = create_bridge()
        
        records = [
            create_test_record(id="mem_001", content="a" * 100),
            create_test_record(id="mem_002", content="b" * 100),
            create_test_record(id="mem_003", content="c" * 100),
        ]
        
        # 预算只够前两条
        truncated = bridge._truncate_by_budget(records, budget=250)
        
        assert len(truncated) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
