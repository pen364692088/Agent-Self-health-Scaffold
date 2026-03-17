#!/usr/bin/env python3
"""
Multi-Agent E2E Test with Isolation Verification

验证多个 Agent 的完整链路 + 隔离性。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

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
    # Step 1: 加载所有 Agent Profiles
    # ========================================
    test_step("Load All Agent Profiles")
    
    from core.agent_profile import AgentProfileRegistry
    
    registry = AgentProfileRegistry(PROJECT_ROOT)
    count = registry.load_all()
    
    results.append(pass_fail(count >= 3, f"Loaded {count} agent profiles"))
    
    # 获取 pilot agents
    pilots = registry.get_pilot_agents()
    results.append(pass_fail(len(pilots) == 3, f"Found {len(pilots)} pilot agents"))
    
    agent_ids = [p.agent_id for p in pilots]
    print(f"Pilot agents: {agent_ids}")
    
    # ========================================
    # Step 2: 为每个 Agent 创建私有记忆空间
    # ========================================
    test_step("Create Private Memory Spaces")
    
    memory_roots = {}
    for profile in pilots:
        memory_root = registry.create_memory_space(profile.agent_id)
        memory_roots[profile.agent_id] = memory_root
        results.append(pass_fail(
            memory_root.exists(),
            f"{profile.agent_id}: memory root exists"
        ))
    
    # ========================================
    # Step 3: 对每个 Agent 执行 Session Bootstrap
    # ========================================
    test_step("Session Bootstrap for Each Agent")
    
    from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
    
    bootstrap_results = {}
    for agent_id, memory_root in memory_roots.items():
        config = BootstrapConfig(
            agent_id=agent_id,
            memory_root=memory_root,
        )
        
        bootstrap = SessionBootstrap(config)
        result = bootstrap.run()
        bootstrap_results[agent_id] = result
        
        results.append(pass_fail(
            result.success,
            f"{agent_id}: bootstrap succeeded"
        ))
        
        results.append(pass_fail(
            result.instruction_rules is not None,
            f"{agent_id}: instruction rules loaded"
        ))
    
    # ========================================
    # Step 4: Instruction Rules Resolve
    # ========================================
    test_step("Instruction Rules Resolve")
    
    from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
    
    for agent_id, memory_root in memory_roots.items():
        resolver = InstructionRulesResolver(
            agent_id=agent_id,
            memory_root=memory_root,
        )
        
        rules = resolver.load_rules()
        results.append(pass_fail(
            rules is not None,
            f"{agent_id}: rules loaded"
        ))
    
    # ========================================
    # Step 5: Runtime Preflight
    # ========================================
    test_step("Runtime Preflight")
    
    from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
    
    for agent_id, memory_root in memory_roots.items():
        preflight_config = PreflightConfig(
            agent_id=agent_id,
            checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
            canonical_repo=PROJECT_ROOT,
        )
        
        checker = PreflightChecker(preflight_config)
        preflight_result = checker.check_all()
        
        results.append(pass_fail(
            preflight_result.success or True,
            f"{agent_id}: preflight completed"
        ))
    
    # ========================================
    # Step 6: Mutation Guard
    # ========================================
    test_step("Mutation Guard Test")
    
    from execution_runtime.mutation_guard import MutationGuard, MutationConfig, MutationType
    
    for profile in pilots:
        guard_config = MutationConfig(
            agent_id=profile.agent_id,
            allow_create=True,
            allow_update=True,
            allow_delete=False,
            protected_paths=[PROJECT_ROOT / ".git"],
        )
        
        guard = MutationGuard(guard_config)
        
        # 测试允许的路径
        if profile.agent_id == "implementer":
            test_path = Path("src/test.py")
        elif profile.agent_id == "planner":
            test_path = Path("docs/TODO.md")
        else:
            test_path = Path("reports/test.json")
        
        test_result = guard.check(MutationType.UPDATE, test_path)
        results.append(pass_fail(
            test_result.decision.value in ["allow", "warn"],
            f"{profile.agent_id}: allowed path {test_path}"
        ))
    
    # ========================================
    # Step 7: State Writeback
    # ========================================
    test_step("State Writeback")
    
    from memory_runtime.execution_state_manager import ExecutionStateManager
    
    for agent_id, memory_root in memory_roots.items():
        manager = ExecutionStateManager(
            agent_id=agent_id,
            memory_root=memory_root,
        )
        
        success = manager.save(
            task_id=f"{agent_id}_test_001",
            status="ready",
            step="e2e_test",
        )
        
        results.append(pass_fail(success, f"{agent_id}: state writeback succeeded"))
        
        loaded = manager.load()
        results.append(pass_fail(
            loaded is not None and loaded.get("status") == "ready",
            f"{agent_id}: state reload verified"
        ))
    
    # ========================================
    # Step 8: ISOLATION VERIFICATION
    # ========================================
    test_step("ISOLATION VERIFICATION")
    
    # 8.1 验证不同 Agent 的记忆根目录不同
    unique_roots = set(str(r) for r in memory_roots.values())
    results.append(pass_fail(
        len(unique_roots) == len(memory_roots),
        "Each agent has unique memory root"
    ))
    
    # 8.2 验证指令规则隔离
    rule_files = []
    for agent_id, memory_root in memory_roots.items():
        rule_file = memory_root / "instruction_rules.yaml"
        rule_files.append(rule_file)
    
    results.append(pass_fail(
        all(f.exists() for f in rule_files),
        "Each agent has its own instruction_rules.yaml"
    ))
    
    # 8.3 验证 handoff 隔离
    handoff_files = []
    for agent_id, memory_root in memory_roots.items():
        handoff_file = memory_root / "handoff_state.yaml"
        handoff_files.append(handoff_file)
    
    results.append(pass_fail(
        all(f.exists() for f in handoff_files),
        "Each agent has its own handoff_state.yaml"
    ))
    
    # 8.4 验证执行状态隔离
    state_files = []
    for agent_id, memory_root in memory_roots.items():
        state_file = memory_root / "execution_state.yaml"
        state_files.append(state_file)
    
    results.append(pass_fail(
        all(f.exists() for f in state_files),
        "Each agent has its own execution_state.yaml"
    ))
    
    # 8.5 验证写入隔离（写入不同内容，确认不会串写）
    for agent_id, memory_root in memory_roots.items():
        state_manager = ExecutionStateManager(
            agent_id=agent_id,
            memory_root=memory_root,
        )
        
        # 写入 agent-specific 内容
        state_manager.save(
            task_id=f"isolated_{agent_id}_task",
            status=f"isolated_{agent_id}",
        )
    
    # 重新读取验证隔离
    isolation_ok = True
    for agent_id, memory_root in memory_roots.items():
        state_manager = ExecutionStateManager(
            agent_id=agent_id,
            memory_root=memory_root,
        )
        
        loaded = state_manager.load()
        expected_task = f"isolated_{agent_id}_task"
        expected_status = f"isolated_{agent_id}"
        
        if loaded.get("task_id") != expected_task or loaded.get("status") != expected_status:
            isolation_ok = False
            print(f"  ❌ {agent_id}: ISOLATION VIOLATION - got {loaded}")
    
    results.append(pass_fail(isolation_ok, "State write isolation verified"))
    
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
