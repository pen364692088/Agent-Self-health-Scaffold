#!/usr/bin/env python3
"""
Telegram Integration Test Script

测试 Telegram 消息通过 Python 模块处理的完整链路。
"""

import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path("/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold")
sys.path.insert(0, str(PROJECT_DIR))

from adapters.telegram_ingress import (
    TelegramIngressAdapter,
    MessageEvent,
    create_message_event
)
from runtime.message_to_task_router import (
    MessageToTaskRouter,
    TaskClassifier,
    RouteDecision
)
from runtime.auto_start_controller import (
    AutoStartController,
    FeatureFlags,
    AutoStartDecision
)
from runtime.risk_gate import (
    RiskGate,
    Operation,
    RiskLevel
)
from runtime.telegram_status_bridge import (
    TelegramStatusBridge,
    TaskStatus
)
from runtime.telegram_control_commands import (
    TelegramControlCommands,
    CommandContext
)


def test_message_flow():
    """测试消息处理流程"""
    print("=" * 60)
    print("Telegram Integration Test")
    print("=" * 60)
    
    # 1. 创建模拟 Telegram update
    print("\n[1] 创建模拟 Telegram update...")
    
    update = {
        "update_id": 99999,
        "message": {
            "message_id": 12345,
            "from": {
                "id": 8420019401,
                "username": "test_user"
            },
            "chat": {
                "id": 8420019401,
                "type": "private"
            },
            "text": "帮我整理 docs 目录"
        }
    }
    
    # 2. 通过 ingress adapter 标准化
    print("\n[2] 通过 ingress adapter 标准化...")
    
    ingress = TelegramIngressAdapter()
    result = ingress.process_update(update)
    
    print(f"   Status: {result['status']}")
    print(f"   Idempotency Key: {result.get('idempotency_key', 'N/A')}")
    
    event = result.get('event')
    if not event:
        print("   ERROR: Failed to normalize update")
        return False
    
    print(f"   Event ID: {event.event_id}")
    print(f"   Text: {event.content.text}")
    
    # 3. 通过 router 路由
    print("\n[3] 通过 message-to-task router 路由...")
    
    router = MessageToTaskRouter()
    route_decision = router.route(event.to_dict())
    
    print(f"   Route Type: {route_decision.type}")
    print(f"   Confidence: {route_decision.confidence}")
    print(f"   Reason: {route_decision.reason}")
    
    # 4. 评估风险
    print("\n[4] 评估风险...")
    
    risk_gate = RiskGate()
    operation = Operation(
        type="shell_command",
        description="整理 docs 目录",
        command="find docs -type f"
    )
    risk_assessment = risk_gate.assess(operation, {"mode": "guarded-auto"})
    
    print(f"   Risk Level: {risk_assessment.risk_level}")
    print(f"   Action: {risk_assessment.action['type']}")
    
    # 5. 通过 auto-start controller 决策
    print("\n[5] 通过 auto-start controller 决策...")
    
    controller = AutoStartController()
    auto_decision = controller.decide(
        event.to_dict(),
        route_decision.to_dict(),
        {"risk_level": risk_assessment.risk_level}
    )
    
    print(f"   Decision Type: {auto_decision.decision_type}")
    print(f"   Mode: {auto_decision.mode}")
    print(f"   Action: {auto_decision.action.get('type')}")
    print(f"   Requires Approval: {auto_decision.action.get('requires_approval', False)}")
    
    # 6. 测试控制命令
    print("\n[6] 测试控制命令...")
    
    cmd_controller = TelegramControlCommands(
        auto_start_controller=controller,
        status_bridge=TelegramStatusBridge(str(PROJECT_DIR / "artifacts"))
    )
    
    # 测试 /status 命令
    status_context = CommandContext(
        chat_id="8420019401",
        user_id="8420019401",
        message_id="999",
        command="/status"
    )
    status_result = cmd_controller.handle(status_context)
    print(f"   /status Result: {status_result.success}")
    
    # 测试 /help 命令
    help_context = CommandContext(
        chat_id="8420019401",
        user_id="8420019401",
        message_id="1000",
        command="/help"
    )
    help_result = cmd_controller.handle(help_context)
    print(f"   /help Result: {help_result.success}")
    
    # 7. 验证幂等性
    print("\n[7] 验证幂等性...")
    
    result2 = ingress.process_update(update)
    print(f"   Second Process Status: {result2['status']}")
    print(f"   Should Skip: {result2['status'] == 'skipped'}")
    
    # 8. 测试高风险操作
    print("\n[8] 测试高风险操作...")
    
    dangerous_operation = Operation(
        type="shell_command",
        description="删除目录",
        command="rm -rf /tmp/test"
    )
    dangerous_assessment = risk_gate.assess(dangerous_operation, {"mode": "guarded-auto"})
    
    print(f"   Risk Level: {dangerous_assessment.risk_level}")
    print(f"   Action: {dangerous_assessment.action['type']}")
    print(f"   Requires Approval: {dangerous_assessment.action['type'] == 'pause_for_approval'}")
    
    print("\n" + "=" * 60)
    print("✅ Telegram Integration Test Complete")
    print("=" * 60)
    
    return True


def test_pilot_a_low_risk():
    """Pilot A: 低风险自动任务"""
    print("\n" + "=" * 60)
    print("Pilot A: Low Risk Auto Task")
    print("=" * 60)
    
    # 模拟低风险任务
    event = create_message_event(
        chat_id="8420019401",
        user_id="8420019401",
        text="生成 docs 目录的索引文件"
    )
    
    router = MessageToTaskRouter()
    route_decision = router.route(event.to_dict())
    
    risk_gate = RiskGate()
    operation = Operation(
        type="shell_command",
        description="生成索引",
        command="ls docs > docs/index.txt"
    )
    risk_assessment = risk_gate.assess(operation, {"mode": "guarded-auto"})
    
    controller = AutoStartController()
    auto_decision = controller.decide(
        event.to_dict(),
        route_decision.to_dict(),
        {"risk_level": risk_assessment.risk_level}
    )
    
    print(f"Route Type: {route_decision.type}")
    print(f"Risk Level: {risk_assessment.risk_level}")
    print(f"Decision Type: {auto_decision.decision_type}")
    print(f"Auto Proceed: {auto_decision.action.get('type') == 'auto_proceed'}")
    
    # 验证：低风险应自动执行
    assert risk_assessment.risk_level == "low", "Low risk expected"
    assert auto_decision.action.get('type') == 'auto_proceed', "Auto proceed expected"
    
    print("✅ Pilot A: Low risk task auto-proceeds correctly")
    return True


def test_pilot_b_high_risk():
    """Pilot B: 高风险阻断任务"""
    print("\n" + "=" * 60)
    print("Pilot B: High Risk Blocked Task")
    print("=" * 60)
    
    # 模拟高风险任务
    event = create_message_event(
        chat_id="8420019401",
        user_id="8420019401",
        text="删除整个项目目录"
    )
    
    router = MessageToTaskRouter()
    route_decision = router.route(event.to_dict())
    
    risk_gate = RiskGate()
    operation = Operation(
        type="shell_command",
        description="删除目录",
        command="rm -rf ./project"
    )
    risk_assessment = risk_gate.assess(operation, {"mode": "guarded-auto"})
    
    controller = AutoStartController()
    auto_decision = controller.decide(
        event.to_dict(),
        route_decision.to_dict(),
        {"risk_level": risk_assessment.risk_level}
    )
    
    print(f"Route Type: {route_decision.type}")
    print(f"Risk Level: {risk_assessment.risk_level}")
    print(f"Decision Type: {auto_decision.decision_type}")
    print(f"Requires Approval: {auto_decision.action.get('requires_approval', False)}")
    
    # 验证：高风险应暂停等待审批
    assert risk_assessment.risk_level == "high", "High risk expected"
    assert auto_decision.action.get('type') == 'pause_for_approval', "Pause for approval expected"
    assert auto_decision.action.get('requires_approval') == True, "Requires approval expected"
    
    print("✅ Pilot B: High risk task blocked correctly")
    return True


def test_kill_switch():
    """测试 Kill Switch"""
    print("\n" + "=" * 60)
    print("Kill Switch Test")
    print("=" * 60)
    
    controller = AutoStartController()
    
    # 启用 kill switch
    result = controller.enable_kill_switch()
    print(f"Kill Switch Enabled: {result['kill_switch_enabled']}")
    
    # 尝试执行任务
    event = create_message_event(
        chat_id="8420019401",
        user_id="8420019401",
        text="执行任务"
    )
    route_decision = {"type": "new_task", "objective": "test"}
    
    auto_decision = controller.decide(event.to_dict(), route_decision)
    print(f"Decision Type: {auto_decision.decision_type}")
    print(f"Action: {auto_decision.action.get('type')}")
    
    # 验证：kill switch 启用时应进入安全模式
    assert auto_decision.decision_type == "SAFE_MODE", "Safe mode expected"
    
    # 禁用 kill switch
    controller.disable_kill_switch()
    auto_decision = controller.decide(event.to_dict(), route_decision)
    print(f"After Disable - Decision Type: {auto_decision.decision_type}")
    
    assert auto_decision.decision_type != "SAFE_MODE", "Should not be safe mode"
    
    print("✅ Kill Switch works correctly")
    return True


if __name__ == "__main__":
    results = []
    
    print("\n" + "#" * 60)
    print("# Telegram Integration Tests")
    print("#" * 60)
    
    try:
        results.append(("Message Flow", test_message_flow()))
    except Exception as e:
        print(f"❌ Message Flow FAILED: {e}")
        results.append(("Message Flow", False))
    
    try:
        results.append(("Pilot A (Low Risk)", test_pilot_a_low_risk()))
    except Exception as e:
        print(f"❌ Pilot A FAILED: {e}")
        results.append(("Pilot A (Low Risk)", False))
    
    try:
        results.append(("Pilot B (High Risk)", test_pilot_b_high_risk()))
    except Exception as e:
        print(f"❌ Pilot B FAILED: {e}")
        results.append(("Pilot B (High Risk)", False))
    
    try:
        results.append(("Kill Switch", test_kill_switch()))
    except Exception as e:
        print(f"❌ Kill Switch FAILED: {e}")
        results.append(("Kill Switch", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    sys.exit(0 if passed == total else 1)
