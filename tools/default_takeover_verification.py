#!/usr/bin/env python3
"""
Default Takeover Verification

验证已接入 Agent 是否被默认主链接管。

场景：
A. 冷启动 - 验证 session bootstrap / 规则解析 / health check
B. 真实任务执行 - 验证 preflight / task runtime / writeback / health / receipt
C. 触发 warning - 验证系统继续运行并正确记录风险
D. 触发 critical - 验证高风险动作被 block

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


def test_scenario_a_cold_start(agent_id: str) -> dict:
    """
    场景 A: 冷启动
    
    验证是否自动走：
    - session bootstrap
    - 规则解析
    - health check
    """
    print(f"\n{'='*60}")
    print(f"场景 A: 冷启动 - {agent_id}")
    print(f"{'='*60}")
    
    result = {
        "scenario": "cold_start",
        "agent_id": agent_id,
        "passed": False,
        "steps": {},
    }
    
    try:
        # 运行默认主链
        from runtime.default_runtime_chain import DefaultRuntimeChain
        
        chain = DefaultRuntimeChain(agent_id, PROJECT_ROOT)
        chain_result = chain.run()
        
        # 验证各阶段
        steps = chain_result.stages
        
        # Session Bootstrap
        result["steps"]["session_bootstrap"] = steps.get("session_bootstrap", {}).get("success", False)
        print(f"  Session Bootstrap: {'✅' if result['steps']['session_bootstrap'] else '❌'}")
        
        # Instruction Rules
        result["steps"]["instruction_rules"] = steps.get("instruction_rules", {}).get("success", False)
        print(f"  Instruction Rules: {'✅' if result['steps']['instruction_rules'] else '❌'}")
        
        # Preflight
        result["steps"]["preflight"] = "runtime_preflight" in steps
        print(f"  Preflight: {'✅' if result['steps']['preflight'] else '❌'}")
        
        # Health Check
        result["steps"]["health_check"] = steps.get("health_check", {}).get("success", False)
        print(f"  Health Check: {'✅' if result['steps']['health_check'] else '❌'}")
        
        # Receipt
        result["steps"]["receipt"] = chain_result.receipt is not None
        print(f"  Receipt: {'✅' if result['steps']['receipt'] else '❌'}")
        
        # 判断是否通过
        result["passed"] = all(result["steps"].values())
        
        print(f"\n  结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ 错误: {e}")
    
    return result


def test_scenario_b_task_execution(agent_id: str) -> dict:
    """
    场景 B: 真实任务执行
    
    验证是否自动走：
    - preflight
    - task runtime
    - writeback
    - health report
    - receipt/evidence
    """
    print(f"\n{'='*60}")
    print(f"场景 B: 任务执行 - {agent_id}")
    print(f"{'='*60}")
    
    result = {
        "scenario": "task_execution",
        "agent_id": agent_id,
        "passed": False,
        "steps": {},
    }
    
    def sample_task(context):
        """示例任务"""
        return {"status": "completed", "output": "test_result"}
    
    try:
        from runtime.default_runtime_chain import DefaultRuntimeChain
        
        chain = DefaultRuntimeChain(agent_id, PROJECT_ROOT)
        chain_result = chain.run(task_fn=sample_task)
        
        steps = chain_result.stages
        
        # Preflight
        result["steps"]["preflight"] = "runtime_preflight" in steps
        print(f"  Preflight: {'✅' if result['steps']['preflight'] else '❌'}")
        
        # Task Runtime
        result["steps"]["task_runtime"] = "task_runtime" in steps
        print(f"  Task Runtime: {'✅' if result['steps']['task_runtime'] else '❌'}")
        
        # Writeback
        result["steps"]["writeback"] = "memory_writeback" in steps
        print(f"  Writeback: {'✅' if result['steps']['writeback'] else '❌'}")
        
        # Health Report
        result["steps"]["health_report"] = "health_check" in steps
        print(f"  Health Report: {'✅' if result['steps']['health_report'] else '❌'}")
        
        # Receipt
        result["steps"]["receipt"] = chain_result.receipt is not None
        print(f"  Receipt: {'✅' if result['steps']['receipt'] else '❌'}")
        
        result["passed"] = all(result["steps"].values())
        
        print(f"\n  结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ 错误: {e}")
    
    return result


def test_scenario_c_warning(agent_id: str) -> dict:
    """
    场景 C: 触发 warning
    
    验证：
    - 系统继续运行
    - 正确记录风险
    - 给出治理动作
    """
    print(f"\n{'='*60}")
    print(f"场景 C: Warning 处理 - {agent_id}")
    print(f"{'='*60}")
    
    result = {
        "scenario": "warning_handling",
        "agent_id": agent_id,
        "passed": False,
        "checks": {},
    }
    
    try:
        from runtime.health_action_matrix import HealthActionMatrix
        
        matrix = HealthActionMatrix(PROJECT_ROOT)
        
        # 模拟 warning 状态
        decision = matrix.decide("warning")
        
        # 检查是否允许继续
        result["checks"]["allow_continue"] = decision.allow_continue
        print(f"  Allow Continue: {'✅' if decision.allow_continue else '❌'}")
        
        # 检查是否有治理动作
        result["checks"]["has_action"] = decision.action.value != "none"
        print(f"  Has Action: {'✅' if result['checks']['has_action'] else '❌'}")
        
        # 检查是否有建议动作
        result["checks"]["has_recommendations"] = len(decision.recommended_actions) > 0
        print(f"  Has Recommendations: {'✅' if result['checks']['has_recommendations'] else '❌'}")
        
        # 执行动作
        exec_result = matrix.execute(decision, agent_id)
        result["checks"]["action_executed"] = exec_result.get("executed", False)
        print(f"  Action Executed: {'✅' if result['checks']['action_executed'] else '❌'}")
        
        # 检查日志
        result["checks"]["log_created"] = exec_result.get("log_path") is not None
        print(f"  Log Created: {'✅' if result['checks']['log_created'] else '❌'}")
        
        result["passed"] = all(result["checks"].values())
        
        print(f"\n  结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ 错误: {e}")
    
    return result


def test_scenario_d_critical(agent_id: str) -> dict:
    """
    场景 D: 触发 critical
    
    验证：
    - 高风险动作被 block
    - recovery / intervention 被触发或明确提示
    """
    print(f"\n{'='*60}")
    print(f"场景 D: Critical 处理 - {agent_id}")
    print(f"{'='*60}")
    
    result = {
        "scenario": "critical_handling",
        "agent_id": agent_id,
        "passed": False,
        "checks": {},
    }
    
    try:
        from runtime.health_action_matrix import HealthActionMatrix
        
        matrix = HealthActionMatrix(PROJECT_ROOT)
        
        # 模拟 critical 状态
        decision = matrix.decide("critical")
        
        # 检查是否阻断
        result["checks"]["should_block"] = not decision.allow_continue
        print(f"  Should Block: {'✅' if not decision.allow_continue else '❌'}")
        
        # 检查是否需要干预
        result["checks"]["require_intervention"] = decision.require_intervention
        print(f"  Require Intervention: {'✅' if decision.require_intervention else '❌'}")
        
        # 检查是否有治理动作
        result["checks"]["has_action"] = decision.action.value in ["block_and_recover", "require_intervention"]
        print(f"  Has Block Action: {'✅' if result['checks']['has_action'] else '❌'}")
        
        # 执行动作
        exec_result = matrix.execute(decision, agent_id)
        result["checks"]["action_executed"] = exec_result.get("executed", False)
        print(f"  Action Executed: {'✅' if result['checks']['action_executed'] else '❌'}")
        
        # 检查干预请求
        result["checks"]["intervention_created"] = exec_result.get("intervention_id") is not None
        print(f"  Intervention Created: {'✅' if result['checks']['intervention_created'] else '❌'}")
        
        # 使用 should_block 方法验证
        should_block = matrix.should_block("critical")
        result["checks"]["block_method_correct"] = should_block
        print(f"  Block Method Correct: {'✅' if should_block else '❌'}")
        
        result["passed"] = all(result["checks"].values())
        
        print(f"\n  结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ 错误: {e}")
    
    return result


def main():
    """主验证流程"""
    print("=" * 70)
    print("DEFAULT TAKEOVER VERIFICATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    from core.agent_profile import AgentProfileRegistry
    
    registry = AgentProfileRegistry(PROJECT_ROOT)
    registry.load_all()
    
    pilots = registry.get_pilot_agents()
    
    if not pilots:
        print("❌ No pilot agents found")
        return 1
    
    agent_ids = [p.agent_id for p in pilots]
    print(f"Pilot Agents: {agent_ids}")
    
    all_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": {},
    }
    
    total_passed = 0
    total_tests = 0
    
    for agent_id in agent_ids:
        print(f"\n{'#'*70}")
        print(f"# Agent: {agent_id.upper()}")
        print(f"{'#'*70}")
        
        agent_results = {
            "scenario_a": test_scenario_a_cold_start(agent_id),
            "scenario_b": test_scenario_b_task_execution(agent_id),
            "scenario_c": test_scenario_c_warning(agent_id),
            "scenario_d": test_scenario_d_critical(agent_id),
        }
        
        all_results["agents"][agent_id] = agent_results
        
        # 统计
        for scenario, result in agent_results.items():
            total_tests += 1
            if result.get("passed"):
                total_passed += 1
    
    # 汇总
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    
    for agent_id, agent_results in all_results["agents"].items():
        passed = sum(1 for r in agent_results.values() if r.get("passed"))
        print(f"{agent_id}: {passed}/4 scenarios passed")
    
    print(f"\nTotal: {total_passed}/{total_tests} passed")
    
    # 保存报告
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_path = reports_dir / f"takeover_verification_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    if total_passed == total_tests:
        print("\n✅ ALL VERIFICATION PASSED")
        return 0
    else:
        print(f"\n❌ {total_tests - total_passed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
