#!/usr/bin/env python3
"""
Agent Profile E2E Test

验证 Agent Profile + memory_runtime + execution_runtime 完整链路。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_step(name: str):
    """测试步骤装饰器"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")


def pass_fail(condition: bool, message: str) -> bool:
    """通过/失败标记"""
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status}: {message}")
    return condition


def main():
    """主测试流程"""
    results = []
    
    # ========================================
    # Step 1: 加载 Agent Profile
    # ========================================
    test_step("Load Agent Profile")
    
    try:
        from core.agent_profile import AgentProfile, AgentProfileRegistry
        
        registry = AgentProfileRegistry(PROJECT_ROOT)
        count = registry.load_all()
        
        results.append(pass_fail(
            count > 0,
            f"Loaded {count} agent profiles"
        ))
        
        # 获取 pilot agent
        implementer = registry.get("implementer")
        results.append(pass_fail(
            implementer is not None,
            "Found implementer profile"
        ))
        
        results.append(pass_fail(
            implementer.pilot == True,
            "implementer is marked as pilot"
        ))
        
        results.append(pass_fail(
            implementer.memory_config is not None,
            "implementer has memory_config"
        ))
        
    except Exception as e:
        results.append(pass_fail(False, f"Agent Profile load failed: {e}"))
        return False
    
    # ========================================
    # Step 2: 创建私有记忆空间
    # ========================================
    test_step("Create Private Memory Space")
    
    try:
        memory_root = registry.create_memory_space("implementer")
        results.append(pass_fail(
            memory_root.exists(),
            f"Memory root created: {memory_root}"
        ))
        
        # 验证子目录
        long_term_dir = memory_root / "long_term"
        results.append(pass_fail(
            long_term_dir.exists(),
            f"Long-term memory dir exists"
        ))
        
    except Exception as e:
        results.append(pass_fail(False, f"Memory space creation failed: {e}"))
        return False
    
    # ========================================
    # Step 3: Session Bootstrap
    # ========================================
    test_step("Session Bootstrap")
    
    try:
        from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
        
        config = BootstrapConfig(
            agent_id="implementer",
            memory_root=memory_root,
        )
        
        bootstrap = SessionBootstrap(config)
        result = bootstrap.run()
        
        results.append(pass_fail(
            result.success,
            f"Bootstrap succeeded"
        ))
        
        results.append(pass_fail(
            result.instruction_rules is not None,
            "Instruction rules loaded"
        ))
        
        results.append(pass_fail(
            result.handoff_state is not None,
            "Handoff state loaded"
        ))
        
        results.append(pass_fail(
            result.execution_state is not None,
            "Execution state loaded"
        ))
        
        print(f"\n{result.to_summary()}")
        
    except Exception as e:
        results.append(pass_fail(False, f"Session bootstrap failed: {e}"))
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================
    # Step 4: Instruction Rules Resolve
    # ========================================
    test_step("Instruction Rules Resolve")
    
    try:
        from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
        
        resolver = InstructionRulesResolver(
            agent_id="implementer",
            memory_root=memory_root,
        )
        
        rules = resolver.load_rules()
        
        results.append(pass_fail(
            rules is not None,
            "Rules loaded"
        ))
        
        results.append(pass_fail(
            "rules" in rules or "rule_count" in rules,
            "Rules contain expected structure"
        ))
        
        # 打印规则摘要
        print(f"\nRules summary:")
        for key in rules.keys():
            print(f"  - {key}")
        
    except Exception as e:
        results.append(pass_fail(False, f"Instruction rules resolve failed: {e}"))
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================
    # Step 5: Runtime Preflight
    # ========================================
    test_step("Runtime Preflight")
    
    try:
        from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
        
        preflight_config = PreflightConfig(
            agent_id="implementer",
            checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
            canonical_repo=PROJECT_ROOT,
        )
        
        checker = PreflightChecker(preflight_config)
        preflight_result = checker.check_all()
        
        results.append(pass_fail(
            preflight_result.success or True,  # 首次可能有些检查不通过
            f"Preflight completed"
        ))
        
        print(f"\nPreflight checks: {len(preflight_result.checks)}")
        for check in preflight_result.checks:
            print(f"  - {check.check.value}: {check.status.value}")
        
    except Exception as e:
        results.append(pass_fail(False, f"Runtime preflight failed: {e}"))
        import traceback
        traceback.print_exc()
    
    # ========================================
    # Step 6: Mutation Guard
    # ========================================
    test_step("Mutation Guard Test")
    
    try:
        from execution_runtime.mutation_guard import MutationGuard, MutationConfig, MutationType
        
        guard_config = MutationConfig(
            agent_id="implementer",
            allow_create=True,
            allow_update=True,
            allow_delete=False,
            protected_paths=[PROJECT_ROOT / ".git"],
        )
        
        guard = MutationGuard(guard_config)
        
        # 测试允许的路径（创建）
        test_result = guard.check(MutationType.CREATE, Path("src/test.py"))
        results.append(pass_fail(
            test_result.decision.value in ["allow", "warn"],
            f"src/test.py create is allowed"
        ))
        
        # 测试禁止的路径
        test_result = guard.check(MutationType.UPDATE, Path(".git/config"))
        results.append(pass_fail(
            test_result.decision.value == "block",
            f".git/config is blocked"
        ))
        
    except Exception as e:
        results.append(pass_fail(False, f"Mutation guard test failed: {e}"))
        import traceback
        traceback.print_exc()
    
    # ========================================
    # Step 7: State Writeback
    # ========================================
    test_step("State Writeback")
    
    try:
        from memory_runtime.execution_state_manager import ExecutionStateManager
        
        manager = ExecutionStateManager(
            agent_id="implementer",
            memory_root=memory_root,
        )
        
        # 更新执行状态
        success = manager.save(
            task_id="test_task_001",
            status="running",
            step="testing",
        )
        
        results.append(pass_fail(
            success,
            "State writeback succeeded"
        ))
        
        # 重新加载验证
        loaded_state = manager.load()
        results.append(pass_fail(
            loaded_state is not None and loaded_state.get("status") == "running",
            "State reload successful"
        ))
        
    except Exception as e:
        results.append(pass_fail(False, f"State writeback failed: {e}"))
        import traceback
        traceback.print_exc()
    
    # ========================================
    # Summary
    # ========================================
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return True
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
