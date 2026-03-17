#!/usr/bin/env python3
"""
Implementer Agent Cold Start Sample

模拟无人工干预的完整冷启动流程：
1. Session Bootstrap
2. Memory Load
3. Instruction Rules Resolve
4. Runtime Preflight / Mutation Guard
5. State Writeback

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def log_step(step: str, message: str):
    """记录步骤"""
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] {step}: {message}")


def main():
    """冷启动主流程"""
    print("="*70)
    print("IMPLEMENTER AGENT COLD START")
    print("="*70)
    
    # ========================================
    # Phase 1: Agent Profile Load
    # ========================================
    log_step("PHASE_1", "Loading Agent Profile")
    
    from core.agent_profile import AgentProfileRegistry
    
    registry = AgentProfileRegistry(PROJECT_ROOT)
    registry.load_all()
    
    implementer = registry.get("implementer")
    if not implementer:
        print("❌ FATAL: implementer profile not found")
        return False
    
    log_step("PHASE_1", f"✅ Loaded: {implementer.name} (pilot={implementer.pilot})")
    
    # ========================================
    # Phase 2: Memory Space Setup
    # ========================================
    log_step("PHASE_2", "Setting up memory space")
    
    memory_root = registry.create_memory_space("implementer")
    log_step("PHASE_2", f"✅ Memory root: {memory_root}")
    
    # ========================================
    # Phase 3: Session Bootstrap
    # ========================================
    log_step("PHASE_3", "Running session bootstrap")
    
    from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
    
    config = BootstrapConfig(
        agent_id="implementer",
        memory_root=memory_root,
    )
    
    bootstrap = SessionBootstrap(config)
    result = bootstrap.run()
    
    if not result.success:
        print("❌ FATAL: Bootstrap failed")
        return False
    
    log_step("PHASE_3", f"✅ Bootstrap succeeded")
    log_step("PHASE_3", f"  - Rules: {result.instruction_rules.get('rule_count', 0)} loaded")
    log_step("PHASE_3", f"  - Handoff: {'✅' if result.handoff_state else '❌'}")
    log_step("PHASE_3", f"  - Execution: {result.execution_state.get('status', 'unknown') if result.execution_state else 'none'}")
    
    # ========================================
    # Phase 4: Instruction Rules Validation
    # ========================================
    log_step("PHASE_4", "Validating instruction rules")
    
    from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
    
    resolver = InstructionRulesResolver(
        agent_id="implementer",
        memory_root=memory_root,
    )
    
    rules = resolver.load_rules()
    enabled_rules = [r for r in rules.get("rules", []) if r.get("enabled", True)]
    
    log_step("PHASE_4", f"✅ {len(enabled_rules)} rules active")
    
    # 打印关键约束
    for rule in enabled_rules[:3]:
        log_step("PHASE_4", f"  - {rule.get('id')}: {rule.get('description', '')[:50]}...")
    
    # ========================================
    # Phase 5: Runtime Preflight
    # ========================================
    log_step("PHASE_5", "Running runtime preflight")
    
    from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
    
    preflight_config = PreflightConfig(
        agent_id="implementer",
        checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
        canonical_repo=PROJECT_ROOT,
    )
    
    checker = PreflightChecker(preflight_config)
    preflight_result = checker.check_all()
    
    failed_checks = preflight_result.get_failed_checks()
    if failed_checks:
        log_step("PHASE_5", f"⚠️  {len(failed_checks)} checks failed")
        for check in failed_checks:
            log_step("PHASE_5", f"  - {check.check.value}: {check.message}")
    else:
        log_step("PHASE_5", "✅ All preflight checks passed")
    
    # ========================================
    # Phase 6: Mutation Guard Setup
    # ========================================
    log_step("PHASE_6", "Setting up mutation guard")
    
    from execution_runtime.mutation_guard import MutationGuard, MutationConfig
    
    guard_config = MutationConfig(
        agent_id="implementer",
        allow_create=True,
        allow_update=True,
        allow_delete=False,
        protected_paths=[PROJECT_ROOT / ".git"],
    )
    
    guard = MutationGuard(guard_config)
    log_step("PHASE_6", "✅ Mutation guard configured")
    
    # ========================================
    # Phase 7: State Writeback
    # ========================================
    log_step("PHASE_7", "Writing initial state")
    
    from memory_runtime.execution_state_manager import ExecutionStateManager
    
    state_manager = ExecutionStateManager(
        agent_id="implementer",
        memory_root=memory_root,
    )
    
    state_manager.save(
        task_id="cold_start_001",
        status="ready",
        step="initialized",
    )
    
    # 验证写入
    loaded = state_manager.load()
    if loaded and loaded.get("status") == "ready":
        log_step("PHASE_7", "✅ State writeback verified")
    else:
        log_step("PHASE_7", "❌ State writeback failed")
        return False
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*70)
    print("COLD START COMPLETE")
    print("="*70)
    print(f"Agent: {implementer.name} ({implementer.agent_id})")
    print(f"Memory: {memory_root}")
    print(f"Rules: {len(enabled_rules)} active")
    print(f"Preflight: {'✅' if not failed_checks else '⚠️'}")
    print(f"Status: {loaded.get('status')}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*70)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
