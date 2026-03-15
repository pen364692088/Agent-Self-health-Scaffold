"""
Tests for Memory Source Mapper

测试 source_mapper 和 truth_classifier 的核心功能。
"""

import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemorySourceKind,
    MemoryTier,
    MemoryStatus,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)
from core.memory.source_mapper import SourceMapper
from core.memory.truth_classifier import TruthKnowledgeRetrievalClassifier


class TestSourceMapper:
    """测试 SourceMapper 类"""
    
    @pytest.fixture
    def memory_dir(self, tmp_path):
        """创建临时 memory 目录"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        # 创建测试文件
        (memory_dir / "2026-03-15.md").write_text("""# Test Session Log

This is a test session log.
- Fixed bug in X
- Added feature Y
""")
        
        (memory_dir / "EVENT_SCHEMA.md").write_text("""# Memory Event Schema v1.1

## Event Types
- use
- correction
""")
        
        (memory_dir / "events.log").write_text("""{"event": "retrieval", "ts": "2026-03-15T00:00:00Z"}
{"event": "recall", "ts": "2026-03-15T00:00:01Z"}
""")
        
        (memory_dir / "stats.json").write_text("""{"total": 100, "used": 80}""")
        
        return memory_dir
    
    def test_scan_directory(self, memory_dir):
        """测试目录扫描"""
        mapper = SourceMapper(str(memory_dir))
        files = mapper.scan_directory()
        
        assert len(files) == 4
        extensions = [f["extension"] for f in files]
        assert ".md" in extensions
        assert ".log" in extensions
        assert ".json" in extensions
    
    def test_map_md_file(self, memory_dir):
        """测试映射 Markdown 文件"""
        mapper = SourceMapper(str(memory_dir))
        files = mapper.scan_directory()
        
        # 找到 2026-03-15.md
        md_file = next(f for f in files if f["filename"] == "2026-03-15.md")
        record = mapper.map_file_to_record(md_file)
        
        assert record is not None
        assert record.source_kind == MemorySourceKind.SESSION_LOG
        assert record.tkr_layer == TruthKnowledgeRetrieval.KNOWLEDGE
        assert record.title == "Test Session Log"
    
    def test_map_schema_file(self, memory_dir):
        """测试映射 Schema 文件"""
        mapper = SourceMapper(str(memory_dir))
        files = mapper.scan_directory()
        
        schema_file = next(f for f in files if f["filename"] == "EVENT_SCHEMA.md")
        record = mapper.map_file_to_record(schema_file)
        
        assert record is not None
        assert record.source_kind == MemorySourceKind.SCHEMA
        assert record.tkr_layer == TruthKnowledgeRetrieval.TRUTH
    
    def test_map_log_file(self, memory_dir):
        """测试映射日志文件"""
        mapper = SourceMapper(str(memory_dir))
        files = mapper.scan_directory()
        
        log_file = next(f for f in files if f["filename"] == "events.log")
        record = mapper.map_file_to_record(log_file)
        
        assert record is not None
        assert record.source_kind == MemorySourceKind.RETRIEVAL_EVENT
        assert record.tkr_layer == TruthKnowledgeRetrieval.RETRIEVAL
    
    def test_map_json_file(self, memory_dir):
        """测试映射 JSON 文件"""
        mapper = SourceMapper(str(memory_dir))
        files = mapper.scan_directory()
        
        json_file = next(f for f in files if f["filename"] == "stats.json")
        record = mapper.map_file_to_record(json_file)
        
        assert record is not None
        assert record.source_kind == MemorySourceKind.METRICS
    
    def test_map_all_files(self, memory_dir):
        """测试映射所有文件"""
        mapper = SourceMapper(str(memory_dir))
        records = mapper.map_all_files()
        
        assert len(records) == 4
        
        # 检查分类
        source_kinds = [r.source_kind for r in records]
        assert MemorySourceKind.SESSION_LOG in source_kinds
        assert MemorySourceKind.SCHEMA in source_kinds
        assert MemorySourceKind.RETRIEVAL_EVENT in source_kinds
        assert MemorySourceKind.METRICS in source_kinds
    
    def test_generate_asset_map(self, memory_dir):
        """测试生成资产映射报告"""
        mapper = SourceMapper(str(memory_dir))
        report = mapper.generate_asset_map()
        
        assert report["total_files"] == 4
        assert "by_extension" in report
        assert "by_source_kind" in report
        assert "by_tkr_layer" in report


class TestTruthKnowledgeRetrievalClassifier:
    """测试 TruthKnowledgeRetrievalClassifier 类"""
    
    @pytest.fixture
    def classifier(self):
        """创建分类器实例"""
        return TruthKnowledgeRetrievalClassifier()
    
    @pytest.fixture
    def truth_record(self):
        """创建 Truth 层记录"""
        return MemoryRecord(
            id="mem_001",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.SCHEMA,
            content_type=MemoryContentType.FACT,
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Event Schema",
            content="schema definition with version and fields",
            source_file="EVENT_SCHEMA.md",
        )
    
    @pytest.fixture
    def knowledge_record(self):
        """创建 Knowledge 层记录"""
        return MemoryRecord(
            id="mem_002",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.RULE,
            content_type=MemoryContentType.RULE,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Must Follow Rule",
            content="You must follow this rule when processing data",
            source_file="RULE.md",
        )
    
    @pytest.fixture
    def retrieval_record(self):
        """创建 Retrieval 层记录"""
        return MemoryRecord(
            id="mem_003",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.RETRIEVAL_EVENT,
            content_type=MemoryContentType.FACT,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Retrieval Event",
            content='{"event": "retrieval", "query": "test"}',
            source_file="events.log",
        )
    
    def test_classify_truth(self, classifier, truth_record):
        """测试分类 Truth 层"""
        result = classifier.classify(truth_record)
        
        assert result.layer == TruthKnowledgeRetrieval.TRUTH
        assert result.confidence > 0
        assert len(result.reasons) > 0
    
    def test_classify_knowledge(self, classifier, knowledge_record):
        """测试分类 Knowledge 层"""
        result = classifier.classify(knowledge_record)
        
        assert result.layer == TruthKnowledgeRetrieval.KNOWLEDGE
        assert result.confidence > 0
    
    def test_classify_retrieval(self, classifier, retrieval_record):
        """测试分类 Retrieval 层"""
        result = classifier.classify(retrieval_record)
        
        assert result.layer == TruthKnowledgeRetrieval.RETRIEVAL
        assert result.confidence > 0
    
    def test_classify_batch(self, classifier, truth_record, knowledge_record, retrieval_record):
        """测试批量分类"""
        records = [truth_record, knowledge_record, retrieval_record]
        results = classifier.classify_batch(records)
        
        assert len(results) == 3
        assert results[0].layer == TruthKnowledgeRetrieval.TRUTH
        assert results[1].layer == TruthKnowledgeRetrieval.KNOWLEDGE
        assert results[2].layer == TruthKnowledgeRetrieval.RETRIEVAL
    
    def test_get_layer_distribution(self, classifier, truth_record, knowledge_record, retrieval_record):
        """测试获取层级分布"""
        records = [truth_record, knowledge_record, retrieval_record]
        distribution = classifier.get_layer_distribution(records)
        
        assert distribution["truth"] == 1
        assert distribution["knowledge"] == 1
        assert distribution["retrieval"] == 1
    
    def test_get_layer_statistics(self, classifier, truth_record, knowledge_record, retrieval_record):
        """测试获取层级统计"""
        records = [truth_record, knowledge_record, retrieval_record]
        stats = classifier.get_layer_statistics(records)
        
        assert stats["total"] == 3
        assert stats["distribution"]["truth"] == 1
        assert stats["distribution"]["knowledge"] == 1
        assert stats["distribution"]["retrieval"] == 1
        assert stats["avg_confidence"] > 0


class TestMemoryRecord:
    """测试 MemoryRecord 类"""
    
    def test_calculate_score(self):
        """测试评分计算"""
        record = MemoryRecord(
            id="mem_001",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.RULE,
            content_type=MemoryContentType.RULE,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Test",
            content="Test content",
            source_file="test.md",
            use_count=5,
            importance=0.8,
            conflict_penalty=0.5,
        )
        
        score = record.calculate_score()
        
        # score = 2*log(6) + 1.5*recency + 3*0.8 - 2*0.5
        # 验证分数在合理范围内
        assert 0 < score < 15
    
    def test_determine_tier_hot(self):
        """测试确定分层 - HOT"""
        record = MemoryRecord(
            id="mem_001",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.RULE,
            content_type=MemoryContentType.RULE,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Test",
            content="Test content",
            source_file="test.md",
            pinned=True,
        )
        
        tier = record.determine_tier()
        assert tier == MemoryTier.HOT
    
    def test_to_entry_template_format(self):
        """测试转换为 ENTRY_TEMPLATE 格式"""
        record = MemoryRecord(
            id="mem_20260315_001",
            scope=MemoryScope.GLOBAL,
            source_kind=MemorySourceKind.RULE,
            content_type=MemoryContentType.RULE,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Test Rule",
            content="This is a test rule.",
            source_file="test.md",
            use_count=3,
            confidence=0.85,
            importance=0.7,
        )
        
        output = record.to_entry_template_format()
        
        assert "---" in output
        assert "id: mem_20260315_001" in output
        assert "type: RULE" in output
        assert "scope: global" in output
        assert "This is a test rule" in output


class TestMemoryPolicy:
    """测试策略类"""
    
    def test_retention_policy_defaults(self):
        """测试保留策略默认值"""
        from contract.memory.policies import RetentionPolicy
        
        policy = RetentionPolicy()
        
        assert policy.hot_max_age.days == 90
        assert policy.warm_max_age.days == 180
        assert policy.cold_max_age.days == 365
        assert policy.hot_min_use_count == 5
        assert policy.warm_min_use_count == 2
    
    def test_conflict_resolution_policy_defaults(self):
        """测试冲突解决策略默认值"""
        from contract.memory.policies import ConflictResolutionPolicy, ConflictStrategy
        
        policy = ConflictResolutionPolicy()
        
        assert policy.default_strategy == ConflictStrategy.NEWEST_WINS
        assert len(policy.field_strategies) > 0
    
    def test_policy_bundle_config_hash(self):
        """测试策略包配置哈希"""
        from contract.memory.policies import MemoryPolicyBundle
        
        bundle = MemoryPolicyBundle()
        hash_value = bundle.calculate_config_hash()
        
        assert len(hash_value) == 8
        assert bundle.config_hash == hash_value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
