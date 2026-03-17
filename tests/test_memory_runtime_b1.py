"""
Memory Runtime - B1 Minimal Verification Test

验证 memory_runtime 模块的基本功能。

Run: python tests/test_memory_runtime_b1.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import shutil


def test_import():
    """测试模块导入"""
    print("1. Testing imports...")
    
    try:
        from memory_runtime import (
            MemoryLoader,
            MemoryWriter,
            SessionBootstrap,
            HandoffManager,
            ExecutionStateManager,
            InstructionRulesResolver,
            EvidenceLogger,
        )
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_instruction_rules_resolver():
    """测试指令规则解析器"""
    print("2. Testing InstructionRulesResolver...")
    
    from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
    
    try:
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = InstructionRulesResolver(
                agent_id="test",
                memory_root=Path(tmpdir),
            )
            
            # 加载规则（应该包含全局规则）
            rules = resolver.load_rules()
            
            assert rules is not None, "Rules should not be None"
            assert "rules" in rules, "Rules should have 'rules' key"
            assert rules["rule_count"] > 0, "Should have at least global rules"
            
            # 加载 RuleSet
            rule_set = resolver.load_rule_set()
            assert len(rule_set.rules) > 0, "RuleSet should have rules"
            
            # 检查约束
            allowed, reason = rule_set.check_constraint("create", {})
            # create 不在 block 列表中，所以应该允许
            assert allowed, "create should be allowed"
            
            print(f"   ✅ Loaded {rules['rule_count']} rules")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_handoff_manager():
    """测试 Handoff 管理器"""
    print("3. Testing HandoffManager...")
    
    from memory_runtime.handoff_manager import HandoffManager
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HandoffManager(
                agent_id="test",
                memory_root=Path(tmpdir),
            )
            
            # 初始应该没有状态
            state = manager.load()
            assert state is None, "Initial state should be None"
            
            # 保存状态
            success = manager.save(
                objective="Test objective",
                phase="testing",
                next_actions=["action1", "action2"],
            )
            assert success, "Save should succeed"
            
            # 加载状态
            state = manager.load()
            assert state is not None, "State should not be None after save"
            assert state["objective"] == "Test objective"
            assert state["phase"] == "testing"
            assert len(state["next_actions"]) == 2
            
            # 获取摘要
            summary = manager.get_summary()
            assert "Test objective" in summary
            
            print("   ✅ Handoff save/load works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_state_manager():
    """测试执行状态管理器"""
    print("4. Testing ExecutionStateManager...")
    
    from memory_runtime.execution_state_manager import ExecutionStateManager
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(
                agent_id="test",
                memory_root=Path(tmpdir),
            )
            
            # 初始应该没有状态
            state = manager.load()
            assert state is None, "Initial state should be None"
            
            # 保存状态
            success = manager.save(
                task_id="task-001",
                step="step-1",
                status="running",
            )
            assert success, "Save should succeed"
            
            # 加载状态
            state = manager.load()
            assert state is not None
            assert state["task_id"] == "task-001"
            assert state["step"] == "step-1"
            assert state["status"] == "running"
            
            # 检查点测试
            success = manager.save_checkpoint("checkpoint-1", {"data": "test"})
            assert success, "Checkpoint save should succeed"
            
            checkpoint = manager.load_checkpoint("checkpoint-1")
            assert checkpoint is not None
            assert checkpoint["data"] == "test"
            
            checkpoints = manager.list_checkpoints()
            assert "checkpoint-1" in checkpoints
            
            print("   ✅ Execution state save/load/checkpoint works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evidence_logger():
    """测试证据日志器"""
    print("5. Testing EvidenceLogger...")
    
    from memory_runtime.evidence_logger import EvidenceLogger
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvidenceLogger(
                agent_id="test",
                memory_root=Path(tmpdir),
            )
            
            # 记录加载操作
            record = logger.log_load(
                source="test_source",
                record_count=5,
                query="test query",
            )
            
            assert record.evidence_id.startswith("ev:"), "Evidence ID should start with 'ev:'"
            assert record.operation == "load"
            
            # 记录写入操作
            record2 = logger.log_write(
                target="test_target",
                content_hash="abc123",
                category="fact",
            )
            
            assert record2.operation == "write"
            
            # 列出证据
            records = logger.list_evidence(limit=10)
            assert len(records) >= 2, "Should have at least 2 records"
            
            # 获取证据链
            chain = logger.get_evidence_chain(record2.evidence_id)
            assert len(chain) >= 1, "Chain should have at least 1 record"
            
            print("   ✅ Evidence log/query works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_bootstrap():
    """测试会话启动引导"""
    print("6. Testing SessionBootstrap...")
    
    from memory_runtime.session_bootstrap import SessionBootstrap
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            bootstrap = SessionBootstrap(
                agent_id="test",
                memory_root=Path(tmpdir),
            )
            
            # 执行启动引导
            result = bootstrap.run()
            
            assert result.agent_id == "test"
            # 即使没有保存的记忆，也应该成功（因为有全局规则）
            assert result.instruction_rules is not None, "Should load global rules"
            assert result.instruction_rules["rule_count"] > 0
            
            # 生成摘要
            summary = result.to_summary()
            assert "Bootstrap Summary" in summary
            
            print("   ✅ Session bootstrap works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Memory Runtime B1 - Minimal Verification Test")
    print("=" * 60)
    
    tests = [
        test_import,
        test_instruction_rules_resolver,
        test_handoff_manager,
        test_execution_state_manager,
        test_evidence_logger,
        test_session_bootstrap,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"❌ {total - passed}/{total} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
