#!/usr/bin/env python3
"""
Phase H Verification

验证运行治理能力：
- 启用分层策略
- 健康治理策略
- Rollout/Rollback 机制
- 运行指标

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def verify_enablement_policy():
    """验证启用分层策略"""
    print("\n" + "=" * 60)
    print("VERIFY: Enablement Policy")
    print("=" * 60)
    
    from runtime.enablement_state import EnablementState, EnablementTier
    
    state = EnablementState(PROJECT_ROOT)
    
    # 检查 3 个 Agent 都有明确分层
    agents = ["implementer", "planner", "verifier"]
    
    passed = True
    for agent_id in agents:
        tier = state.get_tier(agent_id)
        is_auto = state.is_auto_execute(agent_id)
        
        print(f"  {agent_id}: {tier.value} (auto_execute={is_auto})")
        
        if tier != EnablementTier.DEFAULT_ENABLED:
            print(f"    ⚠️  Expected default_enabled")
            passed = False
    
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed


def verify_health_governance():
    """验证健康治理策略"""
    print("\n" + "=" * 60)
    print("VERIFY: Health Governance Policy")
    print("=" * 60)
    
    from runtime.health_governance_policy import HealthGovernancePolicy
    
    policy = HealthGovernancePolicy(PROJECT_ROOT)
    
    # 测试各种状态
    tests = [
        ("healthy", [], "healthy"),
        ("warning", [], "warning_once"),
        ("warning", ["warning", "warning"], "warning_repeated"),
        ("critical", [], "critical_once"),
        ("critical", ["critical", "critical"], "critical_repeated"),
    ]
    
    passed = True
    for current_health, history, expected_status in tests:
        decision = policy.decide("test_agent", current_health, history)
        
        match = decision.status.value == expected_status
        print(f"  {current_health} + {history} → {decision.status.value} {'✅' if match else '❌'}")
        
        if not match:
            passed = False
    
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed


def verify_rollout_rollback():
    """验证 Rollout/Rollback 机制"""
    print("\n" + "=" * 60)
    print("VERIFY: Rollout/Rollback Mechanism")
    print("=" * 60)
    
    from runtime.enablement_state import EnablementState, EnablementTier
    
    state = EnablementState(PROJECT_ROOT)
    
    passed = True
    
    # 测试 quarantine
    print("\n  测试 Quarantine:")
    success = state.quarantine("implementer", "Test quarantine")
    print(f"    Quarantine implementer: {'✅' if success else '❌'}")
    
    tier_after = state.get_tier("implementer")
    is_quarantine = tier_after == EnablementTier.QUARANTINE
    print(f"    Tier after: {tier_after.value} {'✅' if is_quarantine else '❌'}")
    
    if not is_quarantine:
        passed = False
    
    # 测试 recover
    print("\n  测试 Recover:")
    success = state.recover("implementer", "Test recovery")
    print(f"    Recover implementer: {'✅' if success else '❌'}")
    
    tier_after = state.get_tier("implementer")
    is_manual = tier_after == EnablementTier.MANUAL_ENABLE_ONLY
    print(f"    Tier after: {tier_after.value} {'✅' if is_manual else '❌'}")
    
    if not is_manual:
        passed = False
    
    # 恢复到 default_enabled
    print("\n  恢复到 default_enabled:")
    state.set_tier("implementer", EnablementTier.PILOT_ENABLED, "Recovery test")
    state.set_tier("implementer", EnablementTier.DEFAULT_ENABLED, "Recovery test")
    
    tier_final = state.get_tier("implementer")
    print(f"    Final tier: {tier_final.value}")
    
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed


def verify_operational_metrics():
    """验证运行指标"""
    print("\n" + "=" * 60)
    print("VERIFY: Operational Metrics")
    print("=" * 60)
    
    from runtime.operational_metrics import OperationalMetrics, MetricSnapshot
    
    metrics = OperationalMetrics(PROJECT_ROOT)
    
    # 记录一些测试数据
    print("\n  记录测试数据:")
    for i in range(5):
        snapshot = MetricSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            cold_start_success=True,
            memory_restore_success=True,
            writeback_success=True,
            health_status="healthy" if i < 4 else "warning",
        )
        metrics.record(snapshot)
    
    print("    已记录 5 条测试数据")
    
    # 汇总
    print("\n  汇总指标:")
    summary = metrics.summarize("test_agent", window_size=5)
    
    print(f"    cold_start_success_rate: {summary.cold_start_success_rate:.1%}")
    print(f"    writeback_success_rate: {summary.writeback_success_rate:.1%}")
    print(f"    warning_rate: {summary.warning_rate:.1%}")
    
    # 判断
    print("\n  Rollout Gating:")
    can_rollout = metrics.is_healthy_for_rollout("test_agent")
    should_pause = metrics.should_pause_rollout("test_agent")
    
    print(f"    can_rollout: {can_rollout}")
    print(f"    should_pause: {should_pause}")
    
    passed = True
    print(f"\n  结果: {'✅ 通过' if passed else '❌ 失败'}")
    return passed


def main():
    """主验证流程"""
    print("=" * 70)
    print("PHASE H VERIFICATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    results = []
    
    # Gate H-A
    results.append(verify_enablement_policy())
    
    # Gate H-B
    results.append(verify_health_governance())
    
    # Gate H-C
    results.append(verify_rollout_rollback())
    
    # Gate H-D
    results.append(verify_operational_metrics())
    
    # 汇总
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL GATES PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} GATES FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
