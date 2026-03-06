#!/usr/bin/env python3
"""
E2E 测试：子代理显式回调架构
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
HANDLER = str(WORKSPACE / "tools" / "subagent-completion-handler")
LEDGER = str(WORKSPACE / "tools" / "task-ledger")


def run_tool(cmd: list) -> dict:
    """运行工具并返回 JSON 结果"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Tool failed: {result.stderr}")
    return json.loads(result.stdout)


def test_subagent_tools_config():
    """测试子代理工具配置"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    with open(config_path) as f:
        config = json.load(f)
    
    subagent_tools = config.get("tools", {}).get("subagents", {}).get("tools", {})
    allowed = subagent_tools.get("allow", [])
    
    assert "sessions_send" in allowed, "子代理必须有 sessions_send 权限"
    assert "sessions_history" in allowed, "子代理必须有 sessions_history 权限"
    print("✅ 子代理工具配置正确")


def test_handler_structured_payload():
    """测试 handler 处理结构化 payload"""
    payload = json.dumps({
        "type": "subagent_done",
        "task_id": "test_payload_001",
        "child_session_key": "agent:main:subagent:test",
        "status": "completed",
        "summary": "测试完成"
    })
    
    output = run_tool([HANDLER, "--payload", payload])
    assert output.get("action") in ("notify_user", "ignore"), f"Unexpected action: {output}"
    print("✅ handler 能处理结构化 payload")


def test_task_ledger():
    """测试 task ledger 功能"""
    # 初始化
    result = run_tool([LEDGER, "init", "test_ledger_e2e", "agent:main:test", "E2E测试任务"])
    assert result.get("status") == "ok"
    
    # spawn
    result = run_tool([LEDGER, "spawn", "test_ledger_e2e", "agent:main:subagent:test", "run_e2e"])
    
    # complete
    result = run_tool([LEDGER, "complete", "test_ledger_e2e", "completed", "E2E测试完成"])
    assert result.get("status") == "ok"
    
    # show
    entry = run_tool([LEDGER, "show", "test_ledger_e2e"])
    assert entry.get("task_id") == "test_ledger_e2e"
    assert entry.get("state") == "completed"
    print("✅ task-ledger 功能正常")


def test_template_exists():
    """测试模板文件存在"""
    template_path = WORKSPACE / "templates" / "subagent_callback_task.md"
    assert template_path.exists(), f"模板文件不存在: {template_path}"
    
    content = template_path.read_text()
    assert "parentSessionKey" in content
    assert "sessions_send" in content
    assert "ANNOUNCE_SKIP" in content
    print("✅ 子代理回调模板存在且正确")


def test_handler_health():
    """测试 handler 健康检查"""
    output = run_tool([HANDLER, "--health"])
    assert output.get("status") == "healthy"
    print("✅ subagent-completion-handler 健康")


def main():
    tests = [
        test_subagent_tools_config,
        test_handler_structured_payload,
        test_task_ledger,
        test_template_exists,
        test_handler_health,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed} passed, {failed} failed")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
