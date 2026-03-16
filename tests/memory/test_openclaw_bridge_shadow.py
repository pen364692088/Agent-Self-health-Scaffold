"""
OpenClaw Bridge Shadow Tests

测试 G1 Bridge Shadow 的核心功能。

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
from integration.memory.openclaw_bridge import (
    BridgeRequest,
    BridgeResponse,
    RecallSuggestion,
    BridgeTrace,
    OpenClawBridge,
    create_bridge,
)


# ============== Fixtures ==============

@pytest.fixture
def approved_records():
    """创建 approved 记录"""
    now = datetime.now(timezone.utc)
    
    return [
        MemoryRecord(
            id="mem_approved_001",
            source_file="memory/approved/rule.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="API Versioning Rule",
            content="All API endpoints must be versioned with /vN prefix",
            tags=["api", "versioning"],
            confidence=0.9,
            created_at=now - timedelta(days=1),
        ),
        MemoryRecord(
            id="mem_approved_002",
            source_file="memory/approved/truth.md",
            source_kind=MemorySourceKind.RULE,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Configuration Path",
            content="All configuration files are located in ~/.openclaw/ directory",
            tags=["config"],
            confidence=0.95,
            created_at=now - timedelta(days=2),
        ),
        MemoryRecord(
            id="mem_approved_003",
            source_file="memory/approved/coding.md",
            source_kind=MemorySourceKind.TECHNICAL_NOTE,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.PROJECTS,
            scope_qualifier="openemotion",
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Coding Standard",
            content="Use TypeScript for all frontend code",
            tags=["coding", "typescript"],
            confidence=0.85,
            created_at=now - timedelta(days=3),
        ),
    ]


@pytest.fixture
def bridge(approved_records):
    """创建 Bridge"""
    return create_bridge(approved_records=approved_records)


# ============== BridgeRequest Tests ==============

class TestBridgeRequest:
    """测试 Bridge 请求"""
    
    def test_default_request(self):
        """测试默认请求"""
        request = BridgeRequest(query="test")
        
        assert request.query == "test"
        assert request.max_suggestions == 5
        assert request.timeout_ms == 1000
    
    def test_custom_request(self):
        """测试自定义请求"""
        request = BridgeRequest(
            query="test",
            task_type="coding",
            max_suggestions=10,
            timeout_ms=2000,
        )
        
        assert request.task_type == "coding"
        assert request.max_suggestions == 10
        assert request.timeout_ms == 2000


# ============== RecallSuggestion Tests ==============

class TestRecallSuggestion:
    """测试召回建议"""
    
    def test_suggestion_creation(self):
        """测试创建建议"""
        suggestion = RecallSuggestion(
            record_id="mem_001",
            title="Test",
            content_preview="Test content",
            relevance_score=0.9,
            source="test.md",
            scope="global",
            tkr_layer="knowledge",
            tags=["test"],
        )
        
        assert suggestion.record_id == "mem_001"
        assert suggestion.relevance_score == 0.9
    
    def test_suggestion_to_dict(self):
        """测试建议转字典"""
        suggestion = RecallSuggestion(
            record_id="mem_001",
            title="Test",
            content_preview="Test",
            relevance_score=0.9,
            source="test.md",
            scope="global",
            tkr_layer="knowledge",
        )
        
        data = suggestion.to_dict()
        
        assert data["record_id"] == "mem_001"
        assert data["relevance_score"] == 0.9


# ============== OpenClawBridge Tests ==============

class TestOpenClawBridge:
    """测试 OpenClaw Bridge"""
    
    def test_recall_success(self, bridge):
        """测试成功召回"""
        request = BridgeRequest(query="API versioning")
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert len(response.suggestions) >= 1
        assert response.trace is not None
        assert response.error is None
    
    def test_recall_no_results(self, bridge):
        """测试无结果召回"""
        request = BridgeRequest(query="nonexistent topic xyz123")
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_recall_with_task_type(self, bridge):
        """测试指定任务类型"""
        request = BridgeRequest(
            query="how to code?",
            task_type="coding",
        )
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert response.trace.task_type_detected == "coding"
    
    def test_recall_creative_no_recall(self, bridge):
        """测试创意类不召回"""
        request = BridgeRequest(
            query="create something new",
            task_type="creative",
        )
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert response.trace.recall_triggered is False
    
    def test_recall_budget_limit(self, approved_records):
        """测试预算限制"""
        # 小预算
        bridge = create_bridge(
            approved_records=approved_records,
            max_tokens=50,
            max_records=2,
        )
        
        request = BridgeRequest(query="API")
        
        response = bridge.recall(request)
        
        assert response.success is True
        assert len(response.suggestions) <= 2
        assert response.trace.budget_used_tokens <= 50
    
    def test_recall_fail_open(self):
        """测试 fail-open"""
        # 空 approved 记录
        bridge = create_bridge(approved_records=[])
        
        request = BridgeRequest(query="test")
        
        response = bridge.recall(request)
        
        # 应该成功返回空建议，不抛异常
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_recall_trace(self, bridge):
        """测试追踪信息"""
        request = BridgeRequest(query="API versioning")
        
        response = bridge.recall(request)
        
        assert response.trace is not None
        assert response.trace.request_id is not None
        assert response.trace.started_at is not None
        assert response.trace.completed_at is not None
        assert response.trace.duration_ms > 0
        assert len(response.trace.stages) > 0
    
    def test_recall_statistics(self, bridge):
        """测试统计信息"""
        # 发送几个请求
        bridge.recall(BridgeRequest(query="API"))
        bridge.recall(BridgeRequest(query="config"))
        bridge.recall(BridgeRequest(query="coding"))
        
        stats = bridge.get_statistics()
        
        assert stats["total_requests"] == 3
        assert stats["successful_requests"] >= 0


# ============== Safety Tests ==============

class TestSafety:
    """测试安全性"""
    
    def test_candidate_not_leaked(self, approved_records):
        """测试 candidate 不泄露"""
        # 创建 candidate 记录
        candidate_record = MemoryRecord(
            id="mem_candidate_001",
            source_file="memory/candidate/test.md",
            source_kind=MemorySourceKind.SESSION_LOG,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Candidate Record",
            content="This is a candidate",
            tags=["candidate"],
            confidence=0.9,
        )
        
        # Bridge 只加载 approved
        bridge = create_bridge(approved_records=approved_records)
        
        request = BridgeRequest(query="candidate")
        
        response = bridge.recall(request)
        
        # candidate 不应该出现在结果中
        for suggestion in response.suggestions:
            assert "candidate" not in suggestion.title.lower()
    
    def test_fail_open_on_error(self):
        """测试错误时 fail-open"""
        bridge = OpenClawBridge()
        
        # 没有加载任何记录
        request = BridgeRequest(query="test")
        
        # 不应该抛异常
        response = bridge.recall(request)
        
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_max_suggestions_limit(self, approved_records):
        """测试最大建议数限制"""
        bridge = create_bridge(approved_records=approved_records)
        
        request = BridgeRequest(
            query="",
            max_suggestions=2,
        )
        
        response = bridge.recall(request)
        
        assert len(response.suggestions) <= 2


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_bridge_flow(self, approved_records):
        """测试完整 Bridge 流程"""
        # 1. 创建 Bridge
        bridge = create_bridge(approved_records=approved_records)
        
        # 2. 发送请求
        request = BridgeRequest(
            query="how to implement API?",
            task_type="coding",
            max_suggestions=5,
        )
        
        # 3. 获取响应
        response = bridge.recall(request)
        
        # 4. 验证结果
        assert response.success is True
        assert response.trace is not None
        assert response.trace.task_type_detected == "coding"
        
        # 5. 验证建议
        for suggestion in response.suggestions:
            assert suggestion.record_id is not None
            assert suggestion.title is not None
            assert suggestion.relevance_score >= 0
    
    def test_multiple_requests(self, bridge):
        """测试多个请求"""
        queries = ["API", "config", "coding", "test"]
        
        for query in queries:
            response = bridge.recall(BridgeRequest(query=query))
            assert response.success is True
        
        stats = bridge.get_statistics()
        assert stats["total_requests"] == 4
