"""
Memory Recall Tests

测试 M5a 召回引擎的核心功能。

Author: Memory Kernel
Created: 2026-03-15
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
    MemoryTier,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_recall import (
    RecallEngine,
    RecallConfig,
    RecallResult,
    create_recall_engine,
)


# ============== Fixtures ==============

@pytest.fixture
def approved_records():
    """创建 approved 记录"""
    now = datetime.now(timezone.utc)
    
    return [
        MemoryRecord(
            id="mem_approved_001",
            source_file="memory/approved1.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Approved Rule 1",
            content="All API endpoints must require authentication",
            tags=["security", "api"],
            created_at=now - timedelta(days=1),
        ),
        MemoryRecord(
            id="mem_approved_002",
            source_file="memory/approved2.md",
            source_kind=MemorySourceKind.TECHNICAL_NOTE,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Truth Fact 1",
            content="Configuration files are stored in ~/.openclaw/ directory",
            tags=["config"],
            created_at=now - timedelta(days=2),
        ),
        MemoryRecord(
            id="mem_approved_003",
            source_file="memory/approved3.md",
            source_kind=MemorySourceKind.SESSION_LOG,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.PROJECTS,
            scope_qualifier="openemotion",
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Session Log Entry",
            content="Discussed emotion recognition architecture",
            tags=["openemotion"],
            created_at=now - timedelta(days=3),
        ),
    ]


@pytest.fixture
def candidate_records():
    """创建 candidate 记录"""
    now = datetime.now(timezone.utc)
    
    return [
        MemoryRecord(
            id="mem_candidate_001",
            source_file="memory/candidate1.md",
            source_kind=MemorySourceKind.SESSION_LOG,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Candidate Entry 1",
            content="This is a candidate memory awaiting review",
            tags=["candidate"],
            created_at=now,
        ),
    ]


@pytest.fixture
def recall_engine(approved_records):
    """创建召回引擎"""
    return RecallEngine(approved_records=approved_records)


# ============== RecallConfig Tests ==============

class TestRecallConfig:
    """测试召回配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RecallConfig()
        
        assert config.mode == "production"
        assert config.top_k == 10
        assert config.include_candidates is False
        assert config.fail_open is True
        assert config.enable_trace is True


# ============== RecallEngine Tests ==============

class TestRecallEngine:
    """测试召回引擎"""
    
    def test_recall_basic(self, recall_engine):
        """测试基本召回"""
        result = recall_engine.recall(query="authentication")
        
        assert len(result.records) > 0
        assert result.trace is not None
    
    def test_recall_from_approved_only(self, recall_engine, candidate_records):
        """测试只从 approved 召回"""
        recall_engine.load_candidate_records(candidate_records)
        
        result = recall_engine.recall(query="candidate")
        
        # 生产模式下不应该返回 candidate
        assert len(result.records) == 0
    
    def test_recall_candidate_shadow_mode(self, approved_records, candidate_records):
        """测试 shadow 模式下的 candidate"""
        config = RecallConfig(
            mode="shadow",
            include_candidates=True,
        )
        engine = RecallEngine(
            approved_records=approved_records,
            candidate_records=candidate_records,
            config=config,
        )
        
        result = engine.recall(query="candidate")
        
        # 应该有 candidate 记录的追踪
        assert result.trace is not None
        # Shadow 模式下 candidate 可见
        assert result.trace.has_candidates()
    
    def test_recall_candidate_debug_mode(self, approved_records, candidate_records):
        """测试 debug 模式下的 candidate"""
        config = RecallConfig(
            mode="debug",
            include_candidates=True,
        )
        engine = RecallEngine(
            approved_records=approved_records,
            candidate_records=candidate_records,
            config=config,
        )
        
        result = engine.recall(query="candidate")
        
        assert result.trace is not None
        assert result.trace.mode == "debug"
    
    def test_recall_top_k_limit(self, recall_engine):
        """测试 top-k 限制"""
        result = recall_engine.recall(query="", top_k=2)
        
        assert len(result.records) <= 2
    
    def test_recall_trace_output(self, recall_engine):
        """测试 trace 输出"""
        result = recall_engine.recall(query="authentication")
        
        assert result.trace is not None
        assert result.trace.query == "authentication"
        assert result.trace.mode == "production"
        assert len(result.trace.stages) > 0
    
    def test_recall_fail_open(self):
        """测试 fail-open"""
        # 创建会抛异常的引擎
        engine = RecallEngine()
        engine._search_engine = None  # 强制错误
        
        result = engine.recall(query="test")
        
        # Fail-open 应该返回空结果，不抛异常
        assert len(result.records) == 0
        assert len(result.errors) > 0
    
    def test_recall_no_fail_open(self):
        """测试不 fail-open"""
        config = RecallConfig(fail_open=False)
        engine = RecallEngine(config=config)
        engine._search_engine = None  # 强制错误
        
        with pytest.raises(Exception):
            engine.recall(query="test")
    
    def test_recall_with_scope_filter(self, recall_engine):
        """测试作用域过滤"""
        result = recall_engine.recall(
            query="",
            scope=MemoryScope.PROJECTS,
        )
        
        # 作用域过滤应该生效，但可能包含全局记录
        for record in result.records:
            assert record.scope in [MemoryScope.PROJECTS, MemoryScope.GLOBAL]
    
    def test_recall_statistics(self, recall_engine):
        """测试统计信息"""
        stats = recall_engine.get_statistics()
        
        assert stats["approved_count"] == 3
        assert stats["candidate_count"] == 0
        assert stats["mode"] == "production"


# ============== Truth Quote Tests ==============

class TestTruthQuote:
    """测试 Truth 引用"""
    
    def test_recall_with_truth_quote(self, recall_engine):
        """测试带 Truth 引用的召回"""
        result = recall_engine.recall_with_truth_quote(query="config")
        
        # 应该找到 Truth 层记录
        assert len(result.truth_quotes) > 0
        
        for quote in result.truth_quotes:
            assert quote.record_id is not None
            assert quote.exact_quote is not None
            assert quote.verified is True
    
    def test_truth_quote_exact_match(self, recall_engine):
        """测试 Truth 引用精确匹配"""
        result = recall_engine.recall_with_truth_quote(query="~/.openclaw")
        
        # 检查 Truth 引用
        if result.truth_quotes:
            quote = result.truth_quotes[0]
            # 引用应该是精确的
            assert "~/.openclaw/" in quote.exact_quote
    
    def test_truth_no_summary(self, recall_engine):
        """测试 Truth 不允许摘要"""
        result = recall_engine.recall_with_truth_quote(query="truth")
        
        # Truth 引用应该是完整内容，不是摘要
        for quote in result.truth_quotes:
            # 不应该有省略号或其他摘要标记
            assert "..." not in quote.exact_quote


# ============== RecallTrace Tests ==============

class TestRecallTrace:
    """测试召回追踪"""
    
    def test_trace_to_dict(self, recall_engine):
        """测试追踪转字典"""
        result = recall_engine.recall(query="test")
        
        trace_dict = result.trace.to_dict()
        
        assert trace_dict["query"] == "test"
        assert "stages" in trace_dict
        assert "approved_records" in trace_dict
    
    def test_trace_is_success(self, recall_engine):
        """测试追踪成功状态"""
        result = recall_engine.recall(query="test")
        
        assert result.trace.is_success() is True
    
    def test_trace_has_candidates(self, recall_engine):
        """测试追踪是否有候选"""
        result = recall_engine.recall(query="test")
        
        # 生产模式下没有候选
        assert result.trace.has_candidates() is False


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_recall_flow(self, recall_engine):
        """测试完整召回流程"""
        # 1. 基本召回
        result = recall_engine.recall(query="API")
        
        assert len(result.records) > 0
        assert result.trace is not None
        
        # 2. 检查追踪
        assert result.trace.total_scanned > 0
        assert len(result.trace.stages) > 0
        
        # 3. 检查结果
        for record in result.records:
            assert "API" in record.title or "API" in record.content
    
    def test_recall_multiple_queries(self, recall_engine):
        """测试多次查询"""
        queries = ["authentication", "config", "openemotion"]
        
        for query in queries:
            result = recall_engine.recall(query=query)
            assert result.trace is not None
    
    def test_recall_mode_switch(self, approved_records, candidate_records):
        """测试模式切换"""
        engine = RecallEngine(
            approved_records=approved_records,
            candidate_records=candidate_records,
        )
        
        # 生产模式
        engine.set_mode("production")
        result1 = engine.recall(query="candidate")
        assert not result1.trace.has_candidates() or result1.trace.mode == "production"
        
        # 切换到 shadow 模式
        engine.set_mode("shadow")
        engine._config.include_candidates = True
        result2 = engine.recall(query="candidate")
        assert result2.trace.mode == "shadow"
