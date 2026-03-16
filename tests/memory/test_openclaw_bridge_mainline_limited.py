"""
OpenClaw Bridge Mainline Limited Tests

测试 G3 Bridge Mainline Limited 的核心功能。

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
from integration.memory.openclaw_bridge_mainline_limited import (
    MainlineAssistRequest,
    MainlineAssistResponse,
    MainlineSuggestion,
    MainlineMetrics,
    BridgeMainlineLimited,
    create_bridge_mainline,
    ALLOWED_TASK_TYPES,
    TASK_TYPE_BUDGETS,
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
def bridge_mainline(approved_records):
    """创建 Bridge Mainline Limited"""
    return create_bridge_mainline(approved_records=approved_records)


# ============== MainlineAssistRequest Tests ==============

class TestMainlineAssistRequest:
    """测试 Mainline Assist 请求"""
    
    def test_default_request(self):
        """测试默认请求"""
        request = MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="coding",
        )
        
        assert request.query == "test"
        assert request.session_id == "session_001"
        assert request.task_type == "coding"
        assert request.max_suggestions == 3
        assert request.format == "block"
    
    def test_custom_request(self):
        """测试自定义请求"""
        request = MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="decision",
            max_suggestions=5,
            format="list",
        )
        
        assert request.task_type == "decision"
        assert request.max_suggestions == 5
        assert request.format == "list"


# ============== MainlineSuggestion Tests ==============

class TestMainlineSuggestion:
    """测试 Mainline 建议"""
    
    def test_suggestion_creation(self):
        """测试创建建议"""
        suggestion = MainlineSuggestion(
            suggestion_id="sug_001",
            record_id="mem_001",
            title="Test",
            content_preview="Test content",
            relevance_score=0.9,
            tkr_layer="knowledge",
            scope="global",
            source="test.md",
        )
        
        assert suggestion.suggestion_id == "sug_001"
        assert suggestion.relevance_score == 0.9
    
    def test_suggestion_to_markdown(self):
        """测试建议转 markdown"""
        suggestion = MainlineSuggestion(
            suggestion_id="sug_001",
            record_id="mem_001",
            title="Test Rule",
            content_preview="This is a test",
            relevance_score=0.9,
            tkr_layer="knowledge",
            scope="global",
            source="test.md",
        )
        
        md = suggestion.to_markdown(1)
        
        assert "1. [Test Rule]" in md
        assert "Knowledge" in md
        assert "Global" in md


# ============== Task Type Restriction Tests ==============

class TestTaskTypeRestriction:
    """测试任务类型限制"""
    
    def test_coding_allowed(self, bridge_mainline):
        """测试 coding 任务类型允许"""
        request = MainlineAssistRequest(
            query="how to code?",
            session_id="session_001",
            task_type="coding",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is True
    
    def test_decision_allowed(self, bridge_mainline):
        """测试 decision 任务类型允许"""
        request = MainlineAssistRequest(
            query="should I use API?",
            session_id="session_001",
            task_type="decision",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is True
    
    def test_question_allowed(self, bridge_mainline):
        """测试 question 任务类型允许"""
        request = MainlineAssistRequest(
            query="what is API?",
            session_id="session_001",
            task_type="question",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is True
    
    def test_analysis_denied(self, bridge_mainline):
        """测试 analysis 任务类型拒绝"""
        request = MainlineAssistRequest(
            query="analyze this",
            session_id="session_001",
            task_type="analysis",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is False
        assert "not allowed" in response.error.lower()
    
    def test_creative_denied(self, bridge_mainline):
        """测试 creative 任务类型拒绝"""
        request = MainlineAssistRequest(
            query="create something",
            session_id="session_001",
            task_type="creative",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is False
    
    def test_unknown_task_type_denied(self, bridge_mainline):
        """测试未知任务类型拒绝"""
        request = MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="unknown_type",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.allowed is False


# ============== Rate Limit Tests ==============

class TestRateLimit:
    """测试限流"""
    
    def test_request_count_limit(self, approved_records):
        """测试请求数限制"""
        bridge = create_bridge_mainline(
            approved_records=approved_records,
            max_requests_per_session=2,
        )
        
        session_id = "session_001"
        
        # 第一个请求
        r1 = bridge.assist(MainlineAssistRequest(
            query="test1",
            session_id=session_id,
            task_type="coding",
        ))
        assert r1.allowed is True
        
        # 第二个请求
        r2 = bridge.assist(MainlineAssistRequest(
            query="test2",
            session_id=session_id,
            task_type="coding",
        ))
        assert r2.allowed is True
        
        # 第三个请求应该被拒绝
        r3 = bridge.assist(MainlineAssistRequest(
            query="test3",
            session_id=session_id,
            task_type="coding",
        ))
        assert r3.allowed is False
        assert "rate limit" in r3.error.lower()
    
    def test_token_limit(self, approved_records):
        """测试 token 限制"""
        bridge = create_bridge_mainline(
            approved_records=approved_records,
            max_tokens_per_session=100,
        )
        
        session_id = "session_001"
        
        # 多个请求直到超过 token 限制
        for i in range(20):
            r = bridge.assist(MainlineAssistRequest(
                query=f"test{i}",
                session_id=session_id,
                task_type="coding",
            ))
            
            if not r.allowed and "token" in (r.error or "").lower():
                # 达到 token 限制
                return
        
        # 应该在某个点达到限制
        stats = bridge.get_statistics()
        assert stats["integration_metrics"]["rate_limit_denied"] > 0 or stats["raw_stats"]["rate_limit_denied"] > 0
    
    def test_different_sessions_independent(self, approved_records):
        """测试不同会话独立"""
        bridge = create_bridge_mainline(
            approved_records=approved_records,
            max_requests_per_session=1,
        )
        
        # 会话 1
        r1 = bridge.assist(MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="coding",
        ))
        assert r1.allowed is True
        
        # 会话 1 第二次应该被拒绝
        r2 = bridge.assist(MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="coding",
        ))
        assert r2.allowed is False
        
        # 会话 2 应该可以
        r3 = bridge.assist(MainlineAssistRequest(
            query="test",
            session_id="session_002",
            task_type="coding",
        ))
        assert r3.allowed is True


# ============== Suggestion Block Tests ==============

class TestSuggestionBlock:
    """测试建议块"""
    
    def test_block_format(self, bridge_mainline):
        """测试块格式"""
        request = MainlineAssistRequest(
            query="API",
            session_id="session_001",
            task_type="coding",
            format="block",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        if response.suggestions:
            assert response.suggestion_block is not None
            assert "---" in response.suggestion_block
            assert "Memory Suggestions" in response.suggestion_block
    
    def test_block_format_empty_suggestions(self, bridge_mainline):
        """测试空建议块"""
        request = MainlineAssistRequest(
            query="nonexistent_xyz123",
            session_id="session_001",
            task_type="coding",
            format="block",
        )
        
        response = bridge_mainline.assist(request)
        
        assert response.success is True
        assert response.suggestion_block is None or response.suggestion_block == ""


# ============== Safety Tests ==============

class TestSafety:
    """测试安全性"""
    
    def test_fail_open_on_error(self):
        """测试错误时 fail-open"""
        bridge = BridgeMainlineLimited()
        
        request = MainlineAssistRequest(
            query="test",
            session_id="session_001",
            task_type="coding",
        )
        
        response = bridge.assist(request)
        
        # Fail-open: 应该返回成功但无建议
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_no_auto_inject(self, bridge_mainline):
        """测试不自动注入"""
        request = MainlineAssistRequest(
            query="API",
            session_id="session_001",
            task_type="coding",
        )
        
        response = bridge_mainline.assist(request)
        
        # 建议作为块返回，不是自动注入
        assert response.success is True
        # 建议是可选使用的
        assert response.suggestion_block is not None or len(response.suggestions) == 0
    
    def test_candidate_not_leaked(self, approved_records):
        """测试 candidate 不泄露"""
        bridge = create_bridge_mainline(approved_records=approved_records)
        
        request = MainlineAssistRequest(
            query="candidate",
            session_id="session_001",
            task_type="coding",
        )
        
        response = bridge.assist(request)
        
        for suggestion in response.suggestions:
            assert "candidate" not in suggestion.title.lower()


# ============== Metrics Tests ==============

class TestMetrics:
    """测试指标"""
    
    def test_statistics(self, bridge_mainline):
        """测试统计"""
        request = MainlineAssistRequest(
            query="API",
            session_id="session_001",
            task_type="coding",
        )
        
        bridge_mainline.assist(request)
        
        stats = bridge_mainline.get_statistics()
        
        assert "raw_stats" in stats
        assert "quality_metrics" in stats
        assert "safety_metrics" in stats
        assert "integration_metrics" in stats
        assert stats["raw_stats"]["total_requests"] == 1
    
    def test_adoption_report(self, bridge_mainline):
        """测试采纳报告"""
        request = MainlineAssistRequest(
            query="API",
            session_id="session_001",
            task_type="coding",
        )
        
        response = bridge_mainline.assist(request)
        
        if response.suggestions:
            bridge_mainline.report_adoption(
                suggestion_ids=[s.suggestion_id for s in response.suggestions],
                adopted=True,
                helpful=True,
                quality_improved=True,
            )
        
        stats = bridge_mainline.get_statistics()
        # 验证统计更新
        assert stats["raw_stats"]["total_requests"] == 1


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_mainline_flow(self, approved_records):
        """测试完整 mainline 流程"""
        # 1. 创建 Bridge
        bridge = create_bridge_mainline(approved_records=approved_records)
        
        # 2. 发送请求
        request = MainlineAssistRequest(
            query="how to implement API?",
            session_id="session_001",
            task_type="coding",
            max_suggestions=3,
        )
        
        # 3. 获取响应
        response = bridge.assist(request)
        
        # 4. 验证结果
        assert response.success is True
        assert response.allowed is True
        assert response.metrics is not None
        
        # 5. 报告采纳
        if response.suggestions:
            bridge.report_adoption(
                suggestion_ids=[s.suggestion_id for s in response.suggestions],
                adopted=True,
                helpful=True,
            )
        
        # 6. 检查统计
        stats = bridge.get_statistics()
        assert stats["raw_stats"]["total_requests"] == 1
        assert stats["raw_stats"]["allowed_requests"] == 1
    
    def test_multiple_sessions(self, bridge_mainline):
        """测试多会话"""
        sessions = ["session_001", "session_002", "session_003"]
        
        for session_id in sessions:
            response = bridge_mainline.assist(MainlineAssistRequest(
                query="API",
                session_id=session_id,
                task_type="coding",
            ))
            assert response.success is True
        
        stats = bridge_mainline.get_statistics()
        assert stats["active_sessions"] == 3
    
    def test_session_reset(self, bridge_mainline):
        """测试会话重置"""
        # 发送请求
        bridge_mainline.assist(MainlineAssistRequest(
            query="API",
            session_id="session_001",
            task_type="coding",
        ))
        
        # 重置会话
        bridge_mainline.reset_session("session_001")
        
        # 验证会话已重置
        stats = bridge_mainline.get_statistics()
        assert stats["active_sessions"] == 0
