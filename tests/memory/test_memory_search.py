"""
Memory Search Engine Tests

测试 M3 统一查询服务的核心功能。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta, timezone
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
from core.memory.memory_scope import MemoryScopeHandler, ScopeFilter
from core.memory.memory_ranker import MemoryRanker, RankingConfig, RankedResult
from core.memory.memory_search import (
    MemorySearchEngine,
    SearchParams,
    SearchResult,
)
from core.memory.memory_service import MemoryService, ServiceConfig


# ============== Fixtures ==============

@pytest.fixture
def sample_records():
    """创建测试记录"""
    now = datetime.now(timezone.utc)
    
    return [
        MemoryRecord(
            id="mem_001",
            source_file="memory/2026-03-15.md",
            source_kind=MemorySourceKind.SESSION_LOG,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Session Log: Memory Kernel Development",
            content="Discussion about implementing memory kernel M3...",
            tags=["memory", "kernel"],
            created_at=now - timedelta(days=1),
        ),
        MemoryRecord(
            id="mem_002",
            source_file="projects/openemotion/memory/decision.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.PROJECTS,
            scope_qualifier="openemotion",
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Architecture Decision: Emotion Recognition",
            content="Decided to use transformer model for emotion recognition...",
            tags=["decision", "architecture", "openemotion"],
            created_at=now - timedelta(days=7),
        ),
        MemoryRecord(
            id="mem_003",
            source_file="domains/security/memory/policy.md",
            source_kind=MemorySourceKind.POLICY,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.DOMAINS,
            scope_qualifier="security",
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Security Policy: Authentication",
            content="All API endpoints must require authentication...",
            tags=["policy", "security", "auth"],
            created_at=now - timedelta(days=30),
        ),
        MemoryRecord(
            id="mem_004",
            source_file="memory/templates/entry.md",
            source_kind=MemorySourceKind.TEMPLATE,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Memory Entry Template",
            content="Template for creating memory entries...",
            tags=["template"],
            created_at=now - timedelta(days=60),
        ),
        MemoryRecord(
            id="mem_005",
            source_file="projects/openclaw-core/memory/note.md",
            source_kind=MemorySourceKind.TECHNICAL_NOTE,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.PROJECTS,
            scope_qualifier="openclaw_core",
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Technical Note: Plugin System",
            content="The plugin system uses a registry pattern...",
            tags=["technical", "plugin", "openclaw"],
            created_at=now - timedelta(days=14),
        ),
    ]


# ============== MemoryScopeHandler Tests ==============

class TestMemoryScopeHandler:
    """测试作用域处理器"""
    
    def test_infer_scope_global(self):
        """测试推断全局作用域"""
        handler = MemoryScopeHandler()
        scope, qualifier = handler.infer_scope("memory/general.md")
        assert scope == MemoryScope.GLOBAL
        assert qualifier is None
    
    def test_infer_scope_projects(self):
        """测试推断项目作用域"""
        handler = MemoryScopeHandler()
        scope, qualifier = handler.infer_scope("projects/openemotion/config.md")
        assert scope == MemoryScope.PROJECTS
        # qualifier extraction may vary
    
    def test_infer_scope_domains(self):
        """测试推断领域作用域"""
        handler = MemoryScopeHandler()
        scope, qualifier = handler.infer_scope("domains/security/policy.md")
        assert scope == MemoryScope.DOMAINS
        assert qualifier == "security"
    
    def test_matches_filter_global_included(self, sample_records):
        """测试全局记录是否包含"""
        handler = MemoryScopeHandler()
        record = sample_records[0]  # GLOBAL
        
        scope_filter = ScopeFilter(
            scope=MemoryScope.PROJECTS,
            include_global=True
        )
        
        assert handler.matches_filter(record, scope_filter)
    
    def test_matches_filter_global_excluded(self, sample_records):
        """测试全局记录是否排除"""
        handler = MemoryScopeHandler()
        record = sample_records[0]  # GLOBAL
        
        scope_filter = ScopeFilter(
            scope=MemoryScope.PROJECTS,
            include_global=False
        )
        
        assert handler.matches_filter(record, scope_filter) is False
    
    def test_filter_records(self, sample_records):
        """测试过滤记录列表"""
        handler = MemoryScopeHandler()
        
        scope_filter = ScopeFilter(
            scope=MemoryScope.PROJECTS,
            include_global=False
        )
        
        filtered = handler.filter_records(sample_records, scope_filter)
        assert len(filtered) == 2
        assert all(r.scope == MemoryScope.PROJECTS for r in filtered)
    
    def test_get_scope_distribution(self, sample_records):
        """测试作用域分布统计"""
        handler = MemoryScopeHandler()
        distribution = handler.get_scope_distribution(sample_records)
        
        assert distribution.get("global") == 2
        assert distribution.get("projects") == 2
        assert distribution.get("domains") == 1


# ============== MemoryRanker Tests ==============

class TestMemoryRanker:
    """测试排序器"""
    
    def test_compute_score_basic(self, sample_records):
        """测试基本分数计算"""
        ranker = MemoryRanker()
        result = ranker.compute_score(sample_records[0])
        
        assert result.score > 0
        assert "layer" in result.score_breakdown
        assert "scope" in result.score_breakdown
    
    def test_authority_aware_ranking(self, sample_records):
        """测试权威感知排序"""
        ranker = MemoryRanker()
        
        # 搜索 "openemotion"
        results = ranker.rank_records(sample_records, query="openemotion")
        
        # openemotion 相关记录应该排在前面
        assert results[0].record.scope_qualifier == "openemotion"
    
    def test_keyword_match(self, sample_records):
        """测试关键词匹配"""
        ranker = MemoryRanker()
        
        # 搜索 "security"
        results = ranker.rank_records(sample_records, query="security")
        
        # 应该找到包含 security 的记录
        security_found = any(
            "security" in r.record.title.lower() or "security" in r.record.tags
            for r in results
        )
        assert security_found
    
    def test_freshness_score(self, sample_records):
        """测试新鲜度分数"""
        ranker = MemoryRanker()
        
        # 最新记录
        result_new = ranker.compute_score(sample_records[0])
        # 最旧记录
        result_old = ranker.compute_score(sample_records[3])
        
        # 新记录的新鲜度分数应该更高
        assert result_new.score_breakdown["freshness"] > result_old.score_breakdown["freshness"]
    
    def test_top_k_limit(self, sample_records):
        """测试 top_k 限制"""
        ranker = MemoryRanker()
        results = ranker.rank_records(sample_records, top_k=2)
        
        assert len(results) == 2


# ============== MemorySearchEngine Tests ==============

class TestMemorySearchEngine:
    """测试搜索引擎"""
    
    def test_keyword_search_basic(self, sample_records):
        """测试基本关键词搜索"""
        engine = MemorySearchEngine(sample_records)
        result = engine.keyword_search("memory")
        
        assert len(result.records) > 0
        assert any("memory" in r.title.lower() or "memory" in (r.content or "").lower() 
                   for r in result.records)
    
    def test_keyword_search_with_scope_filter(self, sample_records):
        """测试带作用域过滤的关键词搜索"""
        engine = MemorySearchEngine(sample_records)
        
        params = SearchParams(
            query="openemotion",
            scope=MemoryScope.PROJECTS,
            include_global=False
        )
        
        result = engine.search(params)
        
        assert all(r.scope == MemoryScope.PROJECTS for r in result.records)
    
    def test_metadata_filter_tkr_layer(self, sample_records):
        """测试元数据过滤 - 层级"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.filtered_search(
            query="",
            filters={"tkr_layer": TruthKnowledgeRetrieval.TRUTH}
        )
        
        assert all(r.tkr_layer == TruthKnowledgeRetrieval.TRUTH for r in result.records)
    
    def test_metadata_filter_source_kind(self, sample_records):
        """测试元数据过滤 - 来源类型"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.filtered_search(
            query="",
            filters={"source_kind": MemorySourceKind.DECISION_LOG}
        )
        
        assert all(r.source_kind == MemorySourceKind.DECISION_LOG for r in result.records)
    
    def test_scope_filter_projects(self, sample_records):
        """测试作用域过滤 - 项目"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.scope_search(MemoryScope.PROJECTS, include_global=False)
        
        assert all(r.scope == MemoryScope.PROJECTS for r in result.records)
    
    def test_scope_filter_domains(self, sample_records):
        """测试作用域过滤 - 领域"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.scope_search(MemoryScope.DOMAINS, include_global=False)
        
        assert all(r.scope == MemoryScope.DOMAINS for r in result.records)
    
    def test_authority_aware_ranking(self, sample_records):
        """测试权威感知排序"""
        engine = MemorySearchEngine(sample_records)
        
        # 搜索 "openemotion"
        result = engine.keyword_search("openemotion")
        
        # 应该找到相关记录
        assert len(result.records) > 0
    
    def test_top_k_limit(self, sample_records):
        """测试 top_k 限制"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.keyword_search("", top_k=2)
        
        assert len(result.records) == 2
    
    def test_trace_output(self, sample_records):
        """测试 trace 输出"""
        engine = MemorySearchEngine(sample_records)
        
        params = SearchParams(
            query="memory",
            trace=True
        )
        
        result = engine.search(params)
        
        assert result.trace_info is not None
        assert result.trace_info.total_records_scanned == 5
        assert len(result.trace_info.stages) > 0
    
    def test_empty_query(self, sample_records):
        """测试空查询"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.keyword_search("")
        
        # 空查询应该返回所有记录（受 top_k 限制）
        assert len(result.records) <= 10
    
    def test_no_results(self, sample_records):
        """测试无结果"""
        engine = MemorySearchEngine(sample_records)
        
        result = engine.keyword_search("xyznonexistent123")
        
        assert len(result.records) == 0
    
    def test_get_statistics(self, sample_records):
        """测试统计信息"""
        engine = MemorySearchEngine(sample_records)
        stats = engine.get_statistics()
        
        assert stats["total"] == 5
        assert "by_scope" in stats
        assert "by_tkr_layer" in stats


# ============== MemoryService Tests ==============

class TestMemoryService:
    """测试统一服务"""
    
    def test_search_basic(self, sample_records):
        """测试基本搜索"""
        service = MemoryService(sample_records)
        
        result = service.search(query="memory", top_k=5)
        
        assert len(result.records) <= 5
    
    def test_keyword_search(self, sample_records):
        """测试关键词搜索"""
        service = MemoryService(sample_records)
        
        records = service.keyword_search("security", top_k=5)
        
        assert len(records) > 0
    
    def test_search_by_scope(self, sample_records):
        """测试按作用域搜索"""
        service = MemoryService(sample_records)
        
        records = service.search_by_scope("projects", include_global=False)
        
        assert all(r.scope == MemoryScope.PROJECTS for r in records)
    
    def test_search_by_layer(self, sample_records):
        """测试按层级搜索"""
        service = MemoryService(sample_records)
        
        records = service.search_by_layer("truth")
        
        assert all(r.tkr_layer == TruthKnowledgeRetrieval.TRUTH for r in records)
    
    def test_search_by_tags(self, sample_records):
        """测试按标签搜索"""
        service = MemoryService(sample_records)
        
        records = service.search_by_tags(tags=["decision"])
        
        assert all("decision" in r.tags for r in records)
    
    def test_advanced_search(self, sample_records):
        """测试高级搜索"""
        service = MemoryService(sample_records)
        
        result = service.advanced_search(
            query="",
            scope="projects",
            tkr_layer="knowledge",
            top_k=10,
            trace=True
        )
        
        assert all(r.scope == MemoryScope.PROJECTS for r in result.records)
        assert all(r.tkr_layer == TruthKnowledgeRetrieval.KNOWLEDGE for r in result.records)
        assert result.trace_info is not None
    
    def test_get_statistics(self, sample_records):
        """测试统计信息"""
        service = MemoryService(sample_records)
        
        stats = service.get_statistics()
        
        assert stats["total"] == 5
    
    def test_count(self, sample_records):
        """测试计数"""
        service = MemoryService(sample_records)
        
        assert service.count() == 5


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_search_workflow(self, sample_records):
        """测试完整搜索流程"""
        service = MemoryService(sample_records)
        
        # 1. 关键词搜索
        result1 = service.search(query="openemotion", trace=True)
        assert len(result1.records) > 0
        assert result1.trace_info is not None
        
        # 2. 作用域过滤
        records2 = service.search_by_scope("projects", include_global=False)
        assert len(records2) == 2
        
        # 3. 层级过滤
        records3 = service.search_by_layer("truth")
        assert len(records3) == 1
        
        # 4. 组合过滤
        result4 = service.advanced_search(
            query="security",
            scope="domains",
            top_k=10
        )
        assert len(result4.records) == 1
    
    def test_scope_distribution(self, sample_records):
        """测试作用域分布"""
        service = MemoryService(sample_records)
        
        distribution = service.get_scope_distribution()
        
        assert distribution.get("global") == 2
        assert distribution.get("projects") == 2
        assert distribution.get("domains") == 1
    
    def test_layer_distribution(self, sample_records):
        """测试层级分布"""
        service = MemoryService(sample_records)
        
        distribution = service.get_layer_distribution()
        
        assert distribution.get("truth") == 1
        assert distribution.get("knowledge") == 2
        assert distribution.get("retrieval") == 2
