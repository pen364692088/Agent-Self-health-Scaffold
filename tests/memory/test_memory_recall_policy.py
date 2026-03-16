"""
Memory Recall Policy Tests

测试 M5b 召回策略的核心功能。

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
from core.memory.memory_recall_policy import (
    TaskType,
    RecallTrigger,
    RecallPolicy,
    RecallPolicyManager,
    create_recall_policy,
)


# ============== Fixtures ==============

@pytest.fixture
def recall_policy():
    """创建召回策略"""
    return RecallPolicy()


@pytest.fixture
def policy_manager():
    """创建策略管理器"""
    return RecallPolicyManager()


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
            tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
            title="Test Record",
            content="This is a test record",
            tags=["test"],
        ),
        MemoryRecord(
            id="mem_002",
            source_file="test.md",
            source_kind=MemorySourceKind.DECISION_LOG,
            content_type=MemoryContentType.RULE,
            scope=MemoryScope.PROJECTS,
            tkr_layer=TruthKnowledgeRetrieval.TRUTH,
            title="Truth Record",
            content="This is a truth record",
            tags=["truth"],
        ),
    ]


# ============== RecallTrigger Tests ==============

class TestRecallTrigger:
    """测试召回触发器"""
    
    def test_trigger_enabled(self):
        """测试启用触发"""
        trigger = RecallTrigger(task_type=TaskType.QUESTION, trigger_recall=True)
        
        assert trigger.should_trigger("test") is True
    
    def test_trigger_disabled(self):
        """测试禁用触发"""
        trigger = RecallTrigger(task_type=TaskType.CREATIVE, trigger_recall=False)
        
        assert trigger.should_trigger("test") is False
    
    def test_trigger_with_keywords(self):
        """测试关键词触发"""
        trigger = RecallTrigger(
            task_type=TaskType.QUESTION,
            trigger_recall=True,
            keywords=["api", "code"],
        )
        
        assert trigger.should_trigger("how to use api") is True
        assert trigger.should_trigger("general question") is False


# ============== RecallPolicy Tests ==============

class TestRecallPolicy:
    """测试召回策略"""
    
    def test_default_policy(self, recall_policy):
        """测试默认策略"""
        assert recall_policy.approved_only is True
        assert recall_policy.canary_mode is True
    
    def test_should_recall_question(self, recall_policy):
        """测试问答类召回"""
        assert recall_policy.should_recall(TaskType.QUESTION, "test") is True
    
    def test_should_recall_creative(self, recall_policy):
        """测试创意类召回"""
        assert recall_policy.should_recall(TaskType.CREATIVE, "test") is False
    
    def test_filter_records(self, recall_policy, sample_records):
        """测试过滤记录"""
        approved_ids = {"mem_001"}
        
        filtered = recall_policy.filter_records(sample_records, approved_ids)
        
        assert len(filtered) == 1
        assert filtered[0].id == "mem_001"
    
    def test_filter_by_scope(self, sample_records):
        """测试作用域过滤"""
        policy = RecallPolicy(
            allowed_scopes={MemoryScope.GLOBAL},
        )
        
        filtered = policy.filter_records(sample_records)
        
        assert len(filtered) == 1
        assert filtered[0].scope == MemoryScope.GLOBAL


# ============== RecallPolicyManager Tests ==============

class TestRecallPolicyManager:
    """测试策略管理器"""
    
    def test_detect_task_type_question(self, policy_manager):
        """测试检测问答类型"""
        task_type = policy_manager.detect_task_type("what is this?")
        
        assert task_type == TaskType.QUESTION
    
    def test_detect_task_type_coding(self, policy_manager):
        """测试检测编码类型"""
        task_type = policy_manager.detect_task_type("implement a function")
        
        assert task_type == TaskType.CODING
    
    def test_detect_task_type_decision(self, policy_manager):
        """测试检测决策类型"""
        task_type = policy_manager.detect_task_type("should I use this approach?")
        
        assert task_type == TaskType.DECISION
    
    def test_detect_task_type_creative(self, policy_manager):
        """测试检测创意类型"""
        task_type = policy_manager.detect_task_type("create a new design")
        
        assert task_type == TaskType.CREATIVE
    
    def test_should_recall_by_task(self, policy_manager):
        """测试按任务类型召回"""
        assert policy_manager.should_recall("how to code?", TaskType.CODING) is True
        assert policy_manager.should_recall("create something", TaskType.CREATIVE) is False
    
    def test_apply_policy(self, policy_manager, sample_records):
        """测试应用策略"""
        policy_manager.set_approved_ids({"mem_001"})
        
        filtered = policy_manager.apply_policy(sample_records, "how to test?")
        
        assert len(filtered) == 1
    
    def test_get_policy_summary(self, policy_manager):
        """测试策略摘要"""
        summary = policy_manager.get_policy_summary()
        
        assert summary["approved_only"] is True
        assert summary["canary_mode"] is True
        assert "task_triggers" in summary


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_policy_flow(self, sample_records):
        """测试完整策略流程"""
        # 1. 创建管理器
        manager = RecallPolicyManager()
        
        # 2. 设置 approved
        manager.set_approved_ids({"mem_001", "mem_002"})
        
        # 3. 检测任务类型
        task_type = manager.detect_task_type("how to implement a function?")
        
        # 4. 检查是否应该召回
        should_recall = manager.should_recall("how to implement?", task_type)
        
        assert should_recall is True
        
        # 5. 应用策略
        filtered = manager.apply_policy(sample_records, "how to implement?", task_type)
        
        assert len(filtered) >= 1
