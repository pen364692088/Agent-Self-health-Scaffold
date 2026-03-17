"""
Execution Runtime - B2 Minimal Verification Test

验证 execution_runtime 模块的基本功能。

Run: python tests/test_execution_runtime_b2.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile


def test_import():
    """测试模块导入"""
    print("1. Testing imports...")
    
    try:
        from execution_runtime import (
            TaskRuntime,
            TaskConfig,
            PreflightChecker,
            PreflightConfig,
            MutationGuard,
            MutationConfig,
            CanonicalGuard,
            CanonicalConfig,
            RetryManager,
            RetryConfig,
            ReceiptManager,
            ReceiptConfig,
        )
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_task_runtime():
    """测试任务运行时"""
    print("2. Testing TaskRuntime...")
    
    from execution_runtime.task_runtime import TaskRuntime, TaskConfig, StepResult
    
    try:
        config = TaskConfig(
            task_id="test-task-001",
            agent_id="test",
            max_steps=10,
        )
        
        runtime = TaskRuntime(config)
        
        # 启动
        task_id = runtime.start()
        assert task_id == "test-task-001"
        
        # 添加步骤
        runtime.add_step(StepResult(
            step_id="step-1",
            success=True,
            output="Output 1",
        ))
        
        runtime.add_step(StepResult(
            step_id="step-2",
            success=True,
            output="Output 2",
        ))
        
        # 获取进度
        progress = runtime.get_progress()
        assert progress["total_steps"] == 2
        assert progress["completed_steps"] == 2
        
        # 完成
        result = runtime.complete(success=True, output="All done")
        
        assert result.success
        assert result.steps_completed == 2
        assert result.started_at is not None
        assert result.completed_at is not None
        
        print("   ✅ TaskRuntime start/step/complete works")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preflight_checker():
    """测试 Preflight 检查器"""
    print("3. Testing PreflightChecker...")
    
    from execution_runtime.preflight import (
        PreflightChecker,
        PreflightConfig,
        PreflightCheck,
    )
    
    try:
        config = PreflightConfig(
            agent_id="test",
            checks=[PreflightCheck.STATE],  # 只检查状态，避免依赖其他模块
        )
        
        checker = PreflightChecker(config)
        result = checker.check_all()
        
        # 状态检查应该通过（无历史状态）
        assert result.agent_id == "test"
        
        print("   ✅ PreflightChecker works")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mutation_guard():
    """测试变更守卫"""
    print("4. Testing MutationGuard...")
    
    from execution_runtime.mutation_guard import (
        MutationGuard,
        MutationConfig,
        MutationType,
        MutationDecision,
    )
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MutationConfig(
                agent_id="test",
                allow_create=True,
                allow_update=True,
                allow_delete=False,
            )
            
            guard = MutationGuard(config)
            
            # 测试 CREATE
            result = guard.check_create(Path(tmpdir) / "test.txt", "content")
            assert result.decision == MutationDecision.ALLOW
            
            # 测试 DELETE（应该被阻止）
            result = guard.check_delete(Path(tmpdir) / "test.txt")
            assert result.decision == MutationDecision.BLOCK
            assert "DELETE not allowed" in result.reason
            
            # 测试保护路径
            config2 = MutationConfig(
                agent_id="test",
                protected_paths=[Path(tmpdir) / "protected"],
            )
            guard2 = MutationGuard(config2)
            
            result = guard2.check_create(Path(tmpdir) / "protected" / "test.txt")
            assert result.decision == MutationDecision.BLOCK
            
            print("   ✅ MutationGuard check/block works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_canonical_guard():
    """测试 Canonical 守卫"""
    print("5. Testing CanonicalGuard...")
    
    from execution_runtime.canonical_guard import (
        CanonicalGuard,
        CanonicalConfig,
    )
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical"
            canonical.mkdir()
            
            config = CanonicalConfig(canonical_repo=canonical)
            guard = CanonicalGuard(config)
            
            # 测试在 canonical 内
            result = guard.check_path(canonical / "test.txt")
            assert result.allowed
            assert result.relative_path == Path("test.txt")
            
            # 测试在 canonical 外
            result = guard.check_path(Path(tmpdir) / "outside.txt")
            assert not result.allowed
            assert "outside canonical" in result.reason.lower()
            
            # 测试 is_canonical
            assert guard.is_canonical(canonical / "test.txt")
            assert not guard.is_canonical(Path("/tmp/outside.txt"))
            
            print("   ✅ CanonicalGuard check_path works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retry_manager():
    """测试重试管理器"""
    print("6. Testing RetryManager...")
    
    from execution_runtime.retry import (
        RetryManager,
        RetryConfig,
        RetryStrategy,
    )
    
    try:
        config = RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.FIXED,
            base_delay_ms=10,  # 短延迟用于测试
        )
        
        manager = RetryManager(config)
        
        # 测试延迟计算
        delay = manager.calculate_delay(1)
        assert delay == 10
        
        delay = manager.calculate_delay(2)
        assert delay == 10  # FIXED 策略
        
        # 测试指数退避
        config2 = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay_ms=100,
            multiplier=2.0,
        )
        manager2 = RetryManager(config2)
        
        delay = manager2.calculate_delay(1)
        assert delay == 100
        
        delay = manager2.calculate_delay(2)
        assert delay == 200
        
        delay = manager2.calculate_delay(3)
        assert delay == 400
        
        # 测试 should_retry
        assert manager.should_retry("Connection timeout")
        assert manager.should_retry("Temporary error")
        assert not manager.should_retry("Permission denied")
        
        print("   ✅ RetryManager delay/should_retry works")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_receipt_manager():
    """测试凭证管理器"""
    print("7. Testing ReceiptManager...")
    
    from execution_runtime.receipt import (
        ReceiptManager,
        ReceiptConfig,
    )
    from execution_runtime.task_runtime import TaskResult
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReceiptConfig(
                agent_id="test",
                receipt_dir=Path(tmpdir) / "receipts",
            )
            
            manager = ReceiptManager(config)
            
            # 创建任务结果
            task_result = TaskResult(
                success=True,
                task_id="test-task-001",
                steps_completed=5,
                steps_failed=0,
                output="Task completed",
                started_at="2026-03-17T00:00:00Z",
                completed_at="2026-03-17T00:01:00Z",
            )
            
            # 创建凭证
            receipt = manager.create_receipt(
                task_result,
                evidence_ids=["ev:001", "ev:002"],
                metadata={"key": "value"},
            )
            
            assert receipt.receipt_id.startswith("rcpt:")
            assert receipt.task_id == "test-task-001"
            assert receipt.success
            assert len(receipt.evidence_ids) == 2
            assert receipt.duration_seconds == 60.0
            
            # 获取凭证
            loaded = manager.get_receipt(receipt.receipt_id)
            assert loaded is not None
            assert loaded.task_id == "test-task-001"
            
            # 列出凭证
            recent = manager.list_recent_receipts()
            assert len(recent) == 1
            
            print("   ✅ ReceiptManager create/get/list works")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Execution Runtime B2 - Minimal Verification Test")
    print("=" * 60)
    
    tests = [
        test_import,
        test_task_runtime,
        test_preflight_checker,
        test_mutation_guard,
        test_canonical_guard,
        test_retry_manager,
        test_receipt_manager,
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
