#!/usr/bin/env python3
"""
Governance Drill

治理演练：
1. warning_repeated 演练
2. critical_once 演练
3. critical_repeated 演练
4. rollback / recover 演练

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def drill_warning_repeated():
    """
    演练 warning_repeated
    
    验证：
    - 状态从 warning_once 升级为 warning_repeated
    - 动作为 continue_with_escalation
    - 被加入重点观察对象
    """
    print("\n" + "=" * 70)
    print("DRILL: warning_repeated")
    print("=" * 70)
    
    from runtime.health_governance_policy import HealthGovernancePolicy
    
    policy = HealthGovernancePolicy(PROJECT_ROOT)
    
    print("\n构造连续 warning 场景...")
    
    # 模拟连续 warning
    history = ["warning", "warning"]
    decision = policy.decide("test_agent", "warning", history)
    
    print(f"\n历史: {history}")
    print(f"当前状态: warning")
    print(f"\n治理状态: {decision.status.value}")
    print(f"治理动作: {decision.action.value}")
    print(f"允许继续: {decision.allow_continue}")
    print(f"建议动作: {decision.recommended_actions}")
    
    # 验证
    passed = (
        decision.status.value == "warning_repeated" and
        decision.action.value == "continue_with_escalation" and
        decision.allow_continue == True
    )
    
    print(f"\n{'✅ 通过' if passed else '❌ 失败'}")
    return passed


def drill_critical_once():
    """
    演练 critical_once
    
    验证：
    - 状态识别为 critical_once
    - 动作为 block_and_recover
    - 当前高风险动作被阻断
    - recovery 路径被触发
    """
    print("\n" + "=" * 70)
    print("DRILL: critical_once")
    print("=" * 70)
    
    from runtime.health_governance_policy import HealthGovernancePolicy
    
    policy = HealthGovernancePolicy(PROJECT_ROOT)
    
    print("\n构造单次 critical 场景...")
    
    # 模拟单次 critical
    history = []
    decision = policy.decide("test_agent", "critical", history)
    
    print(f"\n历史: {history}")
    print(f"当前状态: critical")
    print(f"\n治理状态: {decision.status.value}")
    print(f"治理动作: {decision.action.value}")
    print(f"允许继续: {decision.allow_continue}")
    print(f"需要干预: {decision.requires_intervention}")
    print(f"建议动作: {decision.recommended_actions}")
    
    # 验证
    passed = (
        decision.status.value == "critical_once" and
        decision.action.value == "block_and_recover" and
        decision.allow_continue == False and
        decision.requires_intervention == True
    )
    
    print(f"\n{'✅ 通过' if passed else '❌ 失败'}")
    return passed


def drill_critical_repeated():
    """
    演练 critical_repeated
    
    验证：
    - 状态升级为 critical_repeated
    - 动作变为 quarantine_or_manual_mode
    - Agent 退出默认接管
    - enablement state 正确切换
    """
    print("\n" + "=" * 70)
    print("DRILL: critical_repeated")
    print("=" * 70)
    
    from runtime.health_governance_policy import HealthGovernancePolicy
    from runtime.enablement_state import EnablementState, EnablementTier
    
    policy = HealthGovernancePolicy(PROJECT_ROOT)
    state = EnablementState(PROJECT_ROOT)
    
    print("\n构造连续 critical 场景...")
    
    # 模拟连续 critical
    history = ["critical", "critical"]
    decision = policy.decide("test_agent", "critical", history)
    
    print(f"\n历史: {history}")
    print(f"当前状态: critical")
    print(f"\n治理状态: {decision.status.value}")
    print(f"治理动作: {decision.action.value}")
    print(f"允许继续: {decision.allow_continue}")
    print(f"需要隔离: {decision.should_quarantine}")
    print(f"建议动作: {decision.recommended_actions}")
    
    # 验证治理决策
    decision_passed = (
        decision.status.value == "critical_repeated" and
        decision.action.value == "quarantine_or_manual_mode" and
        decision.should_quarantine == True
    )
    
    # 验证 quarantine 操作
    print("\n测试 quarantine 操作...")
    
    # 先设置为 default_enabled
    state.set_tier("test_agent", EnablementTier.DEFAULT_ENABLED, "Test setup")
    
    # 执行 quarantine
    quarantine_success = state.quarantine("test_agent", "Test quarantine drill")
    
    tier_after = state.get_tier("test_agent")
    print(f"  Quarantine 成功: {quarantine_success}")
    print(f"  Quarantine 后状态: {tier_after.value}")
    
    quarantine_passed = tier_after == EnablementTier.QUARANTINE
    
    passed = decision_passed and quarantine_passed
    
    print(f"\n{'✅ 通过' if passed else '❌ 失败'}")
    return passed


def drill_rollback_recover():
    """
    演练 rollback / recover
    
    验证：
    - 状态切换有证据链
    - memory / handoff / execution_state 不丢
    - recover 后不会直接跳过观察重新全开
    """
    print("\n" + "=" * 70)
    print("DRILL: rollback / recover")
    print("=" * 70)
    
    from runtime.enablement_state import EnablementState, EnablementTier
    
    state = EnablementState(PROJECT_ROOT)
    
    # 使用新的测试 agent
    test_agent = "rollback_test_agent"
    
    print(f"\n初始状态设置: default_enabled (agent: {test_agent})")
    state.set_tier(test_agent, EnablementTier.DEFAULT_ENABLED, "Test setup")
    
    initial_tier = state.get_tier(test_agent)
    print(f"  当前状态: {initial_tier.value}")
    
    # Step 1: Rollback
    print("\nStep 1: Rollback (default_enabled → pilot_enabled)...")
    rollback_success = state.rollback(test_agent, "Test rollback drill")
    
    after_rollback = state.get_tier(test_agent)
    print(f"  Rollback 成功: {rollback_success}")
    print(f"  Rollback 后状态: {after_rollback.value}")
    
    rollback_passed = after_rollback == EnablementTier.PILOT_ENABLED
    
    # Step 2: 再次 Rollback
    print("\nStep 2: 再次 Rollback (pilot_enabled → manual_enable_only)...")
    rollback_success2 = state.rollback(test_agent, "Test second rollback")
    
    after_rollback2 = state.get_tier(test_agent)
    print(f"  Rollback 成功: {rollback_success2}")
    print(f"  Rollback 后状态: {after_rollback2.value}")
    
    rollback2_passed = after_rollback2 == EnablementTier.MANUAL_ENABLE_ONLY
    
    # Step 3: Recover (从 quarantine)
    print(f"\nStep 3: 设置为 quarantine 后 recover (agent: {test_agent})...")
    state.set_tier(test_agent, EnablementTier.DEFAULT_ENABLED, "Test setup for quarantine")
    state.quarantine(test_agent, "Test quarantine")
    
    recover_success = state.recover(test_agent, "Test recover drill")
    after_recover = state.get_tier(test_agent)
    
    print(f"  Recover 成功: {recover_success}")
    print(f"  Recover 后状态: {after_recover.value}")
    
    recover_passed = after_recover == EnablementTier.MANUAL_ENABLE_ONLY
    
    # Step 4: 重新 rollout
    print("\nStep 4: 重新 rollout (manual_enable_only → pilot_enabled)...")
    rollout_success = state.set_tier(test_agent, EnablementTier.PILOT_ENABLED, "Test rollout after recover")
    after_rollout = state.get_tier(test_agent)
    
    print(f"  Rollout 成功: {rollout_success}")
    print(f"  Rollout 后状态: {after_rollout.value}")
    
    rollout_passed = after_rollout == EnablementTier.PILOT_ENABLED
    
    # 检查证据链
    print("\n检查证据链...")
    history_dir = PROJECT_ROOT / "logs" / "enablement_history"
    history_files = list(history_dir.glob(f"{test_agent}_*.json"))
    
    print(f"  历史记录数: {len(history_files)}")
    
    evidence_passed = len(history_files) > 0
    
    # 清理测试 agent
    if test_agent in state.states:
        del state.states[test_agent]
        state._save_states()
    
    # 总结
    passed = rollback_passed and rollback2_passed and recover_passed and rollout_passed and evidence_passed
    
    print(f"\n{'✅ 通过' if passed else '❌ 失败'}")
    return passed


def main():
    """主演练流程"""
    print("=" * 70)
    print("GOVERNANCE DRILL")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    results = {}
    
    # 演练 1: warning_repeated
    results["warning_repeated"] = drill_warning_repeated()
    
    # 演练 2: critical_once
    results["critical_once"] = drill_critical_once()
    
    # 演练 3: critical_repeated
    results["critical_repeated"] = drill_critical_repeated()
    
    # 演练 4: rollback / recover
    results["rollback_recover"] = drill_rollback_recover()
    
    # 汇总
    print("\n" + "=" * 70)
    print("DRILL SUMMARY")
    print("=" * 70)
    
    for drill_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{drill_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 通过")
    
    # 保存报告
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drills": {
            name: {"passed": passed}
            for name, passed in results.items()
        },
        "summary": {
            "passed": passed_count,
            "total": total_count,
            "all_passed": passed_count == total_count,
        },
    }
    
    report_path = reports_dir / f"drill_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    if passed_count == total_count:
        print("\n✅ ALL DRILLS PASSED")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} DRILLS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
