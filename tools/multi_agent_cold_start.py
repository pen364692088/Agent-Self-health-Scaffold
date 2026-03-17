#!/usr/bin/env python3
"""
Multi-Agent Cold Start Sample

对每个 Agent 执行无人工干预的冷启动。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def log_step(agent: str, step: str, message: str):
    """记录步骤"""
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] [{agent}] {step}: {message}")


def cold_start_agent(agent_id: str, memory_root: Path) -> bool:
    """单个 Agent 冷启动"""
    print(f"\n{'='*60}")
    print(f"COLD START: {agent_id.upper()}")
    print(f"{'='*60}")
    
    # Phase 1: Session Bootstrap
    log_step(agent_id, "BOOTSTRAP", "Running session bootstrap")
    
    from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
    
    config = BootstrapConfig(
        agent_id=agent_id,
        memory_root=memory_root,
    )
    
    bootstrap = SessionBootstrap(config)
    result = bootstrap.run()
    
    if not result.success:
        log_step(agent_id, "BOOTSTRAP", "❌ FAILED")
        return False
    
    log_step(agent_id, "BOOTSTRAP", f"✅ Rules: {result.instruction_rules.get('rule_count', 0)}")
    
    # Phase 2: Instruction Rules
    log_step(agent_id, "RULES", "Validating instruction rules")
    
    from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
    
    resolver = InstructionRulesResolver(
        agent_id=agent_id,
        memory_root=memory_root,
    )
    
    rules = resolver.load_rules()
    enabled_rules = [r for r in rules.get("rules", []) if r.get("enabled", True)]
    
    log_step(agent_id, "RULES", f"✅ {len(enabled_rules)} rules active")
    
    # Phase 3: Runtime Preflight
    log_step(agent_id, "PREFLIGHT", "Running runtime preflight")
    
    from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
    
    preflight_config = PreflightConfig(
        agent_id=agent_id,
        checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
        canonical_repo=PROJECT_ROOT,
    )
    
    checker = PreflightChecker(preflight_config)
    preflight_result = checker.check_all()
    
    if preflight_result.get_failed_checks():
        log_step(agent_id, "PREFLIGHT", f"⚠️  {len(preflight_result.get_failed_checks())} checks failed")
    else:
        log_step(agent_id, "PREFLIGHT", "✅ All checks passed")
    
    # Phase 4: Mutation Guard
    log_step(agent_id, "GUARD", "Setting up mutation guard")
    
    from execution_runtime.mutation_guard import MutationGuard, MutationConfig
    
    guard_config = MutationConfig(
        agent_id=agent_id,
        allow_create=True,
        allow_update=True,
        allow_delete=False,
        protected_paths=[PROJECT_ROOT / ".git"],
    )
    
    guard = MutationGuard(guard_config)
    log_step(agent_id, "GUARD", "✅ Mutation guard configured")
    
    # Phase 5: State Writeback
    log_step(agent_id, "STATE", "Writing initial state")
    
    from memory_runtime.execution_state_manager import ExecutionStateManager
    
    state_manager = ExecutionStateManager(
        agent_id=agent_id,
        memory_root=memory_root,
    )
    
    state_manager.save(
        task_id=f"{agent_id}_cold_start_001",
        status="ready",
        step="initialized",
    )
    
    loaded = state_manager.load()
    if loaded and loaded.get("status") == "ready":
        log_step(agent_id, "STATE", "✅ State writeback verified")
    else:
        log_step(agent_id, "STATE", "❌ State writeback failed")
        return False
    
    print(f"\n✅ {agent_id.upper()} COLD START COMPLETE")
    return True


def main():
    """主流程"""
    print("="*70)
    print("MULTI-AGENT COLD START")
    print("="*70)
    
    from core.agent_profile import AgentProfileRegistry
    
    registry = AgentProfileRegistry(PROJECT_ROOT)
    registry.load_all()
    
    pilots = registry.get_pilot_agents()
    
    results = {}
    for profile in pilots:
        memory_root = registry.create_memory_space(profile.agent_id)
        success = cold_start_agent(profile.agent_id, memory_root)
        results[profile.agent_id] = success
    
    # Summary
    print(f"\n{'='*70}")
    print("COLD START SUMMARY")
    print(f"{'='*70}")
    
    for agent_id, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{agent_id}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ALL AGENTS COLD START PASSED")
        return True
    else:
        print("\n❌ SOME AGENTS FAILED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
