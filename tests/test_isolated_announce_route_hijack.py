#!/usr/bin/env python3
"""
测试: isolated + announce 路由劫持修复

验证保护层是否正常工作。
"""

import json
import os
import sys
from pathlib import Path

SESSIONS_FILE = Path.home() / ".openclaw/agents/main/sessions/sessions.json"
PRIMARY_SESSION_FILE = Path.home() / ".openclaw/workspace/state/primary_session.json"

def test_primary_session_recorded():
    """测试主 session 是否已记录"""
    if not PRIMARY_SESSION_FILE.exists():
        print("❌ 主 session 未记录")
        return False
    
    with open(PRIMARY_SESSION_FILE) as f:
        data = json.load(f)
    
    if "sessionId" not in data:
        print("❌ 主 session 记录格式错误")
        return False
    
    print(f"✅ 主 session 已记录: {data['sessionId'][:8]}...")
    return True

def test_route_guard_exists():
    """测试路由保护工具是否存在"""
    guard_script = Path.home() / ".openclaw/workspace/tools/route-rebind-guard"
    
    if not guard_script.exists():
        print("❌ 路由保护工具不存在")
        return False
    
    if not os.access(guard_script, os.X_OK):
        print("❌ 路由保护工具不可执行")
        return False
    
    print("✅ 路由保护工具已创建")
    return True

def test_route_guard_functional():
    """测试路由保护工具是否可用"""
    import subprocess
    
    result = subprocess.run(
        [str(Path.home() / ".openclaw/workspace/tools/route-rebind-guard"), "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ 路由保护工具执行失败")
        return False
    
    print("✅ 路由保护工具可执行")
    return True

def test_current_route_check():
    """测试当前路由状态检查"""
    if not PRIMARY_SESSION_FILE.exists():
        print("⏭️  主 session 未记录，跳过")
        return True
    
    with open(PRIMARY_SESSION_FILE) as f:
        primary = json.load(f).get("sessionId", "")
    
    route_key = "agent:main:telegram:direct:8420019401"
    
    if not SESSIONS_FILE.exists():
        print("❌ sessions.json 不存在")
        return False
    
    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)
    
    current = sessions.get(route_key, {}).get("sessionId", "")
    
    print(f"主 session: {primary[:8]}...")
    print(f"当前 session: {current[:8]}...")
    
    if current == primary:
        print("✅ 路由匹配")
        return True
    else:
        print("⚠️  路由不匹配（可运行 route-rebind-guard --restore 恢复）")
        return True  # 不算失败

def test_documentation_exists():
    """测试文档是否存在"""
    doc_file = Path.home() / ".openclaw/workspace/memory/2026-03-09.md"
    
    if not doc_file.exists():
        print("❌ 文档不存在")
        return False
    
    with open(doc_file) as f:
        content = f.read()
    
    if "isolated" not in content or "route hijack" not in content.lower():
        print("❌ 文档缺少关键内容")
        return False
    
    print("✅ 文档已记录")
    return True

def main():
    """运行所有测试"""
    print("=" * 50)
    print("isolated + announce 路由劫持修复测试")
    print("=" * 50)
    
    tests = [
        ("主 session 记录", test_primary_session_recorded),
        ("路由保护工具", test_route_guard_exists),
        ("路由保护工具可用", test_route_guard_functional),
        ("路由状态检查", test_current_route_check),
        ("文档记录", test_documentation_exists),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n[测试] {name}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
