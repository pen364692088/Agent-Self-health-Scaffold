"""
Memory Budget Tests

测试 M5b 预算控制的核心功能。

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
)
from core.memory.memory_budget import (
    PromptBudget,
    BudgetUsage,
    BudgetManager,
    create_budget_manager,
)


# ============== Fixtures ==============

@pytest.fixture
def prompt_budget():
    """创建 prompt 预算"""
    return PromptBudget()


@pytest.fixture
def budget_manager():
    """创建预算管理器"""
    return BudgetManager()


@pytest.fixture
def sample_records():
    """创建测试记录"""
    return [
        MemoryRecord(
            id="mem_001",
            source_file="test.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Truth Record",
            content="A" * 100,  # 100 chars
            tags=["test"],
        ),
        MemoryRecord(
            id="mem_002",
            source_file="test.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Knowledge Record",
            content="B" * 200,  # 200 chars
            tags=["test"],
        ),
        MemoryRecord(
            id="mem_003",
            source_file="test.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Retrieval Record",
            content="C" * 300,  # 300 chars
            tags=["test"],
        ),
    ]


# ============== PromptBudget Tests ==============

class TestPromptBudget:
    """测试 Prompt 预算"""
    
    def test_default_budget(self, prompt_budget):
        """测试默认预算"""
        assert prompt_budget.max_tokens == 1000
        assert prompt_budget.max_records == 10
        assert prompt_budget.max_content_length == 500
    
    def test_estimate_tokens(self, prompt_budget):
        """测试 token 估算"""
        text = "This is a test text"
        
        tokens = prompt_budget.estimate_tokens(text)
        
        # 约 len(text) / 4
        assert tokens > 0
        assert tokens <= len(text)
    
    def test_is_within_budget(self, prompt_budget):
        """测试预算检查"""
        assert prompt_budget.is_within_budget(500, 5) is True
        assert prompt_budget.is_within_budget(2000, 5) is False
        assert prompt_budget.is_within_budget(500, 20) is False


# ============== BudgetUsage Tests ==============

class TestBudgetUsage:
    """测试预算使用"""
    
    def test_usage_ratio(self, prompt_budget):
        """测试使用比例"""
        usage = BudgetUsage(budget=prompt_budget, used_tokens=500)
        
        ratio = usage.usage_ratio()
        
        assert ratio == 0.5
    
    def test_to_dict(self, prompt_budget):
        """测试转字典"""
        usage = BudgetUsage(
            budget=prompt_budget,
            used_tokens=500,
            used_records=5,
            truncated=2,
            rejected=1,
        )
        
        data = usage.to_dict()
        
        assert data["used_tokens"] == 500
        assert data["usage_ratio"] == 0.5
        assert data["truncated"] == 2
        assert data["rejected"] == 1


# ============== BudgetManager Tests ==============

class TestBudgetManager:
    """测试预算管理器"""
    
    def test_enforce_budget_within_limit(self, budget_manager, sample_records):
        """测试预算限制内"""
        filtered, usage = budget_manager.enforce_budget(sample_records)
        
        assert usage.used_records == 3
        assert usage.rejected == 0
    
    def test_enforce_budget_record_limit(self, sample_records):
        """测试记录数限制"""
        budget = PromptBudget(max_records=2)
        manager = BudgetManager(budget=budget)
        
        filtered, usage = manager.enforce_budget(sample_records)
        
        assert usage.used_records == 2
        assert usage.rejected == 1
    
    def test_enforce_budget_token_limit(self, sample_records):
        """测试 token 限制"""
        budget = PromptBudget(max_tokens=10)  # 很小的预算
        manager = BudgetManager(budget=budget)
        
        filtered, usage = manager.enforce_budget(sample_records)
        
        # 大部分会被拒绝
        assert usage.used_records < len(sample_records)
    
    def test_enforce_budget_content_truncation(self, sample_records):
        """测试内容截断"""
        # 创建超长内容
        long_record = MemoryRecord(
            id="mem_long",
            source_file="test.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Long Record",
            content="X" * 1000,  # 超长
            tags=["test"],
        )
        
        budget = PromptBudget(max_content_length=100)
        manager = BudgetManager(budget=budget)
        
        filtered, usage = manager.enforce_budget([long_record])
        
        assert usage.truncated == 1
    
    def test_allocate_by_layer(self, budget_manager, sample_records):
        """测试按层级分配"""
        allocated = budget_manager.allocate_by_layer(sample_records)
        
        assert len(allocated["truth"]) >= 0
        assert len(allocated["knowledge"]) >= 0
        assert len(allocated["retrieval"]) >= 0
    
    def test_get_budget_summary(self, budget_manager):
        """测试预算摘要"""
        summary = budget_manager.get_budget_summary()
        
        assert summary["max_tokens"] == 1000
        assert summary["max_records"] == 10
        assert "layer_ratios" in summary


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_budget_flow(self, sample_records):
        """测试完整预算流程"""
        # 1. 创建管理器
        manager = create_budget_manager(max_tokens=500, max_records=5)
        
        # 2. 执行预算
        filtered, usage = manager.enforce_budget(sample_records)
        
        # 3. 验证结果
        assert usage.used_records <= 5
        assert usage.used_tokens <= 500
        
        # 4. 按层级分配
        allocated = manager.allocate_by_layer(sample_records)
        
        assert "truth" in allocated
        assert "knowledge" in allocated
        assert "retrieval" in allocated
