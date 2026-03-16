"""
Memory Lifecycle Tests

测试 M4b 生命周期管理器的核心功能。

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
    MemoryStatus,
)
from core.memory.memory_lifecycle import (
    LifecycleState,
    TTLConfig,
    LifecycleManager,
    LifecycleRecord,
    create_lifecycle_manager,
)


# ============== Fixtures ==============

@pytest.fixture
def sample_memory():
    """创建测试记忆"""
    return MemoryRecord(
        id="mem_test_001",
        source_file="test.md",
        source_kind=MemorySourceKind.DECISION_LOG,
        content_type=MemoryContentType.RULE,
        scope=MemoryScope.GLOBAL,
        tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
        title="Test Memory",
        content="This is a test memory for lifecycle.",
        tags=["test"],
    )


@pytest.fixture
def lifecycle_manager():
    """创建生命周期管理器"""
    return LifecycleManager()


# ============== TTLConfig Tests ==============

class TestTTLConfig:
    """测试 TTL 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = TTLConfig()
        
        assert config.active_days == 90
        assert config.deprecated_days == 30
        assert config.archived_days == 365
    
    def test_get_ttl(self):
        """测试获取 TTL"""
        config = TTLConfig()
        
        ttl = config.get_ttl(LifecycleState.ACTIVE)
        
        assert ttl == timedelta(days=90)


# ============== LifecycleManager Tests ==============

class TestLifecycleManager:
    """测试生命周期管理器"""
    
    def test_register(self, lifecycle_manager, sample_memory):
        """测试注册"""
        record = lifecycle_manager.register(sample_memory)
        
        assert record.memory_id == sample_memory.id
        assert record.state == LifecycleState.ACTIVE
    
    def test_transition_demote(self, lifecycle_manager, sample_memory):
        """测试降级"""
        lifecycle_manager.register(sample_memory)
        
        success, error = lifecycle_manager.demote(
            memory_id=sample_memory.id,
            demoted_by="manager",
            reason="Low usage",
        )
        
        assert success is True
        
        record = lifecycle_manager.get_record(sample_memory.id)
        assert record.state == LifecycleState.DEPRECATED
    
    def test_transition_archive(self, lifecycle_manager, sample_memory):
        """测试归档"""
        lifecycle_manager.register(sample_memory)
        
        success, error = lifecycle_manager.archive(
            memory_id=sample_memory.id,
            archived_by="manager",
            reason="Old",
        )
        
        assert success is True
        
        record = lifecycle_manager.get_record(sample_memory.id)
        assert record.state == LifecycleState.ARCHIVED
    
    def test_transition_restore(self, lifecycle_manager, sample_memory):
        """测试恢复"""
        lifecycle_manager.register(sample_memory)
        
        # 先降级
        lifecycle_manager.demote(sample_memory.id, demoted_by="manager")
        
        # 再恢复
        success, error = lifecycle_manager.restore(
            memory_id=sample_memory.id,
            restored_by="manager",
            reason="Needed again",
        )
        
        assert success is True
        
        record = lifecycle_manager.get_record(sample_memory.id)
        assert record.state == LifecycleState.ACTIVE
    
    def test_invalid_transition(self, lifecycle_manager, sample_memory):
        """测试无效转换"""
        lifecycle_manager.register(sample_memory)
        
        # 尝试从 active 直接跳到 deleted（无效）
        success, error = lifecycle_manager.transition(
            memory_id=sample_memory.id,
            to_state=LifecycleState.DELETED,
            transitioned_by="manager",
        )
        
        assert success is False
        assert "Invalid transition" in error
    
    def test_record_usage(self, lifecycle_manager, sample_memory):
        """测试记录使用"""
        lifecycle_manager.register(sample_memory)
        
        lifecycle_manager.record_usage(sample_memory.id)
        
        record = lifecycle_manager.get_record(sample_memory.id)
        assert record.use_count == 1
        assert record.last_used is not None
    
    def test_check_expiration(self, lifecycle_manager, sample_memory):
        """测试检查过期"""
        record = lifecycle_manager.register(sample_memory)
        
        # 设置过期时间为过去
        record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        expired = lifecycle_manager.check_expiration()
        
        assert sample_memory.id in expired
    
    def test_list_by_state(self, lifecycle_manager, sample_memory):
        """测试按状态列出"""
        lifecycle_manager.register(sample_memory)
        
        active = lifecycle_manager.list_by_state(LifecycleState.ACTIVE)
        
        assert len(active) == 1
    
    def test_get_statistics(self, lifecycle_manager, sample_memory):
        """测试统计信息"""
        lifecycle_manager.register(sample_memory)
        
        stats = lifecycle_manager.get_statistics()
        
        assert stats["total"] == 1
        assert stats["by_state"]["active"] == 1


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_lifecycle(self, sample_memory):
        """测试完整生命周期"""
        manager = LifecycleManager()
        
        # 1. 注册
        record = manager.register(sample_memory)
        assert record.state == LifecycleState.ACTIVE
        
        # 2. 使用
        manager.record_usage(sample_memory.id)
        
        # 3. 降级
        success, _ = manager.demote(
            sample_memory.id,
            demoted_by="manager",
            reason="Low usage",
        )
        assert success is True
        
        # 4. 恢复
        success, _ = manager.restore(
            sample_memory.id,
            restored_by="manager",
            reason="Needed",
        )
        assert success is True
        
        # 5. 归档
        success, _ = manager.archive(
            sample_memory.id,
            archived_by="manager",
            reason="No longer needed",
        )
        assert success is True
        
        # 6. 验证历史
        record = manager.get_record(sample_memory.id)
        assert len(record.transitions) == 3
