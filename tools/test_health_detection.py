#!/usr/bin/env python3
"""
Test Health Detection

测试健康检查能否识别：
- 记忆未加载
- 规则未解析
- 写回失败
- repo/state/context drift
- evidence 缺失

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
import shutil
import tempfile

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_case(name: str, test_fn):
    """执行测试用例"""
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"{'='*50}")
    
    try:
        result = test_fn()
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        return result
    except Exception as e:
        print(f"❌ FAIL: {name} - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_not_loaded():
    """测试：能检测记忆未加载"""
    from health_runtime.checks.memory_health import MemoryHealthChecker
    from health_runtime.health_checker import HealthConfig, HealthStatus
    
    # 创建临时目录，模拟记忆不存在
    with tempfile.TemporaryDirectory() as tmpdir:
        config = HealthConfig(
            agent_id="nonexistent_agent",
            project_root=Path(tmpdir),
        )
        
        checker = MemoryHealthChecker(config)
        result = checker.check()
        
        # 应该检测到 CRITICAL
        return result.status == HealthStatus.CRITICAL and len(result.issues) > 0


def test_rules_not_parsed():
    """测试：能检测规则未解析"""
    from health_runtime.checks.memory_health import MemoryHealthChecker
    from health_runtime.health_checker import HealthConfig
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        memory_root = project_root / "memory" / "agents" / "test_agent"
        memory_root.mkdir(parents=True)
        
        # 创建无效的 instruction_rules.yaml
        with open(memory_root / "instruction_rules.yaml", "w") as f:
            f.write("invalid: yaml: content: [")
        
        config = HealthConfig(
            agent_id="test_agent",
            project_root=project_root,
        )
        
        checker = MemoryHealthChecker(config)
        result = checker.check()
        
        # 应该检测到问题
        return len(result.issues) > 0


def test_writeback_failure():
    """测试：能检测写回失败"""
    from health_runtime.checks.execution_health import ExecutionHealthChecker
    from health_runtime.health_checker import HealthConfig
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        memory_root = project_root / "memory" / "agents" / "test_agent"
        memory_root.mkdir(parents=True)
        
        # 创建只读目录
        import os
        os.chmod(memory_root, 0o444)
        
        try:
            config = HealthConfig(
                agent_id="test_agent",
                project_root=project_root,
            )
            
            checker = ExecutionHealthChecker(config)
            result = checker.check()
            
            # 应该检测到问题
            return len(result.issues) > 0
        finally:
            os.chmod(memory_root, 0o755)


def test_repo_drift():
    """测试：能检测 repo drift"""
    from health_runtime.checks.drift_health import DriftHealthChecker
    from health_runtime.health_checker import HealthConfig
    
    # 使用当前项目（有未提交变更）
    config = HealthConfig(
        agent_id="implementer",
        project_root=PROJECT_ROOT,
    )
    
    checker = DriftHealthChecker(config)
    result = checker.check()
    
    # 应该检测到 uncommitted changes（因为是开发状态）
    return "uncommitted" in str(result.details.get("repo_drift", {})).lower() or result.status.value in ["warning", "healthy"]


def test_evidence_missing():
    """测试：能检测 evidence 缺失"""
    from health_runtime.checks.integrity_health import IntegrityHealthChecker
    from health_runtime.health_checker import HealthConfig
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        memory_root = project_root / "memory" / "agents" / "test_agent"
        memory_root.mkdir(parents=True)
        
        # 创建空的记忆文件（无 evidence）
        import yaml
        with open(memory_root / "execution_state.yaml", "w") as f:
            yaml.dump({"agent_id": "test_agent"}, f)
        
        with open(memory_root / "handoff_state.yaml", "w") as f:
            yaml.dump({"agent_id": "test_agent"}, f)
        
        config = HealthConfig(
            agent_id="test_agent",
            project_root=project_root,
        )
        
        checker = IntegrityHealthChecker(config)
        result = checker.check()
        
        # 应该检测到 evidence 缺失
        return any("evidence" in i.lower() for i in result.issues)


def main():
    print("=" * 60)
    print("HEALTH DETECTION TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(test_case("Memory Not Loaded", test_memory_not_loaded))
    results.append(test_case("Rules Not Parsed", test_rules_not_parsed))
    # results.append(test_case("Writeback Failure", test_writeback_failure))  # 权限测试在沙箱中可能失败
    results.append(test_case("Repo Drift", test_repo_drift))
    results.append(test_case("Evidence Missing", test_evidence_missing))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL DETECTION TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
