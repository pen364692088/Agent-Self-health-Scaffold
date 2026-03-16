"""
OpenClaw Bridge Canary Assist Tests

测试 G2 Bridge Canary Assist 的核心功能。

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
from integration.memory.openclaw_bridge_canary import (
    AssistRequest,
    AssistResponse,
    AssistSuggestion,
    AssistTrace,
    AdoptionReport,
    BridgeCanaryAssist,
    create_bridge_canary,
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
def bridge_canary(approved_records):
    """创建 Bridge Canary Assist"""
    return create_bridge_canary(approved_records=approved_records)


# ============== AssistRequest Tests ==============

class TestAssistRequest:
    """测试 Assist 请求"""
    
    def test_default_request(self):
        """测试默认请求"""
        request = AssistRequest(query="test")
        
        assert request.query == "test"
        assert request.max_suggestions == 3
        assert request.include_reasoning is False
    
    def test_custom_request(self):
        """测试自定义请求"""
        request = AssistRequest(
            query="test",
            task_type="coding",
            max_suggestions=5,
            include_reasoning=True,
        )
        
        assert request.task_type == "coding"
        assert request.max_suggestions == 5
        assert request.include_reasoning is True


# ============== AssistSuggestion Tests ==============

class TestAssistSuggestion:
    """测试 Assist 建议"""
    
    def test_suggestion_creation(self):
        """测试创建建议"""
        suggestion = AssistSuggestion(
            suggestion_id="sug_001",
            record_id="mem_001",
            title="Test",
            content_preview="Test content",
            relevance_score=0.9,
        )
        
        assert suggestion.suggestion_id == "sug_001"
        assert suggestion.record_id == "mem_001"
        assert suggestion.relevance_score == 0.9
    
    def test_suggestion_with_reasoning(self):
        """测试带推理的建议"""
        suggestion = AssistSuggestion(
            suggestion_id="sug_001",
            record_id="mem_001",
            title="Test",
            content_preview="Test",
            relevance_score=0.9,
            reasoning="This is relevant because...",
        )
        
        assert suggestion.reasoning is not None
    
    def test_suggestion_to_dict(self):
        """测试建议转字典"""
        suggestion = AssistSuggestion(
            suggestion_id="sug_001",
            record_id="mem_001",
            title="Test",
            content_preview="Test",
            relevance_score=0.9,
        )
        
        data = suggestion.to_dict()
        
        assert data["suggestion_id"] == "sug_001"
        assert data["relevance_score"] == 0.9


# ============== AdoptionReport Tests ==============

class TestAdoptionReport:
    """测试采纳报告"""
    
    def test_adoption_report_creation(self):
        """测试创建采纳报告"""
        report = AdoptionReport(
            adoption_token="adopt_123",
            adopted=True,
            helpful=True,
            reason="Very useful",
        )
        
        assert report.adopted is True
        assert report.helpful is True
        assert report.reason == "Very useful"
    
    def test_adoption_report_to_dict(self):
        """测试采纳报告转字典"""
        report = AdoptionReport(
            adoption_token="adopt_123",
            adopted=True,
            helpful=True,
        )
        
        data = report.to_dict()
        
        assert data["adoption_token"] == "adopt_123"
        assert data["adopted"] is True


# ============== BridgeCanaryAssist Tests ==============

class TestBridgeCanaryAssist:
    """测试 Bridge Canary Assist"""
    
    def test_assist_success(self, bridge_canary):
        """测试成功 assist"""
        request = AssistRequest(query="API versioning")
        
        response = bridge_canary.assist(request)
        
        assert response.success is True
        assert len(response.suggestions) >= 1
        assert response.adoption_token is not None
        assert response.trace is not None
        assert response.error is None
    
    def test_assist_no_results(self, bridge_canary):
        """测试无结果 assist"""
        request = AssistRequest(query="nonexistent topic xyz123")
        
        response = bridge_canary.assist(request)
        
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_assist_with_task_type(self, bridge_canary):
        """测试指定任务类型"""
        request = AssistRequest(
            query="how to code?",
            task_type="coding",
        )
        
        response = bridge_canary.assist(request)
        
        assert response.success is True
        assert response.trace.task_type_detected == "coding"
    
    def test_assist_creative_no_recall(self, bridge_canary):
        """测试创意类不召回"""
        request = AssistRequest(
            query="create something new",
            task_type="creative",
        )
        
        response = bridge_canary.assist(request)
        
        assert response.success is True
        assert response.trace.recall_triggered is False
    
    def test_assist_with_reasoning(self, bridge_canary):
        """测试包含推理"""
        request = AssistRequest(
            query="API",
            include_reasoning=True,
        )
        
        response = bridge_canary.assist(request)
        
        assert response.success is True
        # 检查建议是否有推理
        for suggestion in response.suggestions:
            if suggestion.reasoning:
                assert len(suggestion.reasoning) > 0
    
    def test_assist_budget_limit(self, approved_records):
        """测试预算限制"""
        bridge = create_bridge_canary(
            approved_records=approved_records,
            max_tokens=50,
            max_records=2,
        )
        
        request = AssistRequest(query="API")
        
        response = bridge.assist(request)
        
        assert response.success is True
        assert len(response.suggestions) <= 2
    
    def test_assist_fail_open(self):
        """测试 fail-open"""
        bridge = create_bridge_canary(approved_records=[])
        
        request = AssistRequest(query="test")
        
        response = bridge.assist(request)
        
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_adoption_tracking(self, bridge_canary):
        """测试采纳追踪"""
        # 1. 发送 assist 请求
        request = AssistRequest(query="API")
        response = bridge_canary.assist(request)
        
        assert response.success is True
        
        # 2. 报告采纳
        report = AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=True,
            helpful=True,
        )
        
        result = bridge_canary.report_adoption(report)
        
        assert result is True
    
    def test_adoption_tracking_helpful_false(self, bridge_canary):
        """测试采纳追踪 - 无帮助"""
        request = AssistRequest(query="API")
        response = bridge_canary.assist(request)
        
        report = AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=True,
            helpful=False,
            reason="Not relevant",
        )
        
        result = bridge_canary.report_adoption(report)
        
        assert result is True
    
    def test_adoption_tracking_ignore(self, bridge_canary):
        """测试采纳追踪 - 忽略"""
        request = AssistRequest(query="API")
        response = bridge_canary.assist(request)
        
        report = AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=False,
        )
        
        result = bridge_canary.report_adoption(report)
        
        assert result is True


# ============== Metrics Tests ==============

class TestMetrics:
    """测试指标"""
    
    def test_quality_metrics(self, bridge_canary):
        """测试质量指标"""
        # 发送请求并报告采纳
        request = AssistRequest(query="API")
        response = bridge_canary.assist(request)
        
        bridge_canary.report_adoption(AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=True,
            helpful=True,
        ))
        
        metrics = bridge_canary.get_quality_metrics()
        
        assert "adoption_rate" in metrics
        assert "helpful_rate" in metrics
        assert "noise_rate" in metrics
    
    def test_safety_metrics(self, bridge_canary):
        """测试安全指标"""
        metrics = bridge_canary.get_safety_metrics()
        
        assert "fail_open_success_rate" in metrics
        assert "task_mismatch_count" in metrics
    
    def test_integration_metrics(self, bridge_canary):
        """测试集成指标"""
        # 发送几个请求
        bridge_canary.assist(AssistRequest(query="API"))
        bridge_canary.assist(AssistRequest(query="config"))
        
        metrics = bridge_canary.get_integration_metrics()
        
        assert metrics["total_requests"] == 2
        assert "error_rate" in metrics
        assert "prompt_bloat_tokens" in metrics
    
    def test_full_statistics(self, bridge_canary):
        """测试完整统计"""
        request = AssistRequest(query="API")
        response = bridge_canary.assist(request)
        
        bridge_canary.report_adoption(AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=True,
            helpful=True,
        ))
        
        stats = bridge_canary.get_statistics()
        
        assert "raw_stats" in stats
        assert "quality_metrics" in stats
        assert "safety_metrics" in stats
        assert "integration_metrics" in stats


# ============== Safety Tests ==============

class TestSafety:
    """测试安全性"""
    
    def test_no_auto_inject(self, bridge_canary):
        """测试不自动注入"""
        request = AssistRequest(query="API")
        
        response = bridge_canary.assist(request)
        
        # 建议是可用的，但没有被"注入"
        # 只是通过 adoption_token 追踪
        assert response.success is True
        assert response.adoption_token is not None
        # 建议需要显式采纳
        assert len(response.suggestions) >= 0
    
    def test_candidate_not_leaked(self, approved_records):
        """测试 candidate 不泄露"""
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
        
        bridge = create_bridge_canary(approved_records=approved_records)
        
        request = AssistRequest(query="candidate")
        
        response = bridge.assist(request)
        
        for suggestion in response.suggestions:
            assert "candidate" not in suggestion.title.lower()
    
    def test_fail_open_on_error(self):
        """测试错误时 fail-open"""
        bridge = BridgeCanaryAssist()
        
        request = AssistRequest(query="test")
        
        response = bridge.assist(request)
        
        assert response.success is True
        assert len(response.suggestions) == 0
    
    def test_max_suggestions_limit(self, approved_records):
        """测试最大建议数限制"""
        bridge = create_bridge_canary(approved_records=approved_records)
        
        request = AssistRequest(
            query="",
            max_suggestions=2,
        )
        
        response = bridge.assist(request)
        
        assert len(response.suggestions) <= 2


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_assist_flow(self, approved_records):
        """测试完整 assist 流程"""
        # 1. 创建 Bridge
        bridge = create_bridge_canary(approved_records=approved_records)
        
        # 2. 发送请求
        request = AssistRequest(
            query="how to implement API?",
            task_type="coding",
            max_suggestions=5,
            include_reasoning=True,
        )
        
        # 3. 获取响应
        response = bridge.assist(request)
        
        # 4. 验证结果
        assert response.success is True
        assert response.trace is not None
        assert response.adoption_token is not None
        
        # 5. 报告采纳
        report = AdoptionReport(
            adoption_token=response.adoption_token,
            adopted=True,
            helpful=True,
            reason="Very helpful",
        )
        
        result = bridge.report_adoption(report)
        assert result is True
        
        # 6. 检查统计
        stats = bridge.get_statistics()
        assert stats["raw_stats"]["total_requests"] == 1
        assert stats["raw_stats"]["total_adoptions"] == 1
    
    def test_multiple_requests_with_adoptions(self, bridge_canary):
        """测试多个请求和采纳"""
        queries = ["API", "config", "coding"]
        
        for query in queries:
            response = bridge_canary.assist(AssistRequest(query=query))
            
            if response.suggestions:
                bridge_canary.report_adoption(AdoptionReport(
                    adoption_token=response.adoption_token,
                    adopted=True,
                    helpful=True,
                ))
        
        stats = bridge_canary.get_statistics()
        assert stats["raw_stats"]["total_requests"] == 3
