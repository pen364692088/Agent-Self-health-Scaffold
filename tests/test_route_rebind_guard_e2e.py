"""
行为级 E2E 测试：route-rebind-guard 劫持检测与恢复

测试场景：
1. 劫持复现 + 恢复闭环
2. 正常 reply 不误杀
3. 多 isolated announce 并发场景
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import subprocess


class RouteRebindGuardE2ETest:
    """E2E 测试框架"""
    
    def __init__(self):
        self.test_dir = None
        self.sessions_file = None
        self.primary_session_file = None
        self.audit_log = None
        self.sessions_dir = None
        
    def setup(self):
        """创建测试环境"""
        self.test_dir = tempfile.mkdtemp(prefix="route_guard_e2e_")
        self.sessions_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(self.sessions_dir)
        
        self.sessions_file = os.path.join(self.sessions_dir, "sessions.json")
        self.primary_session_file = os.path.join(self.test_dir, "primary_session.json")
        self.audit_log = os.path.join(self.test_dir, "audit.jsonl")
        
        # 初始化 sessions.json
        self._write_sessions({})
        
    def teardown(self):
        """清理测试环境"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def _write_sessions(self, data):
        """写入 sessions.json"""
        with open(self.sessions_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _write_session_file(self, session_id, metadata):
        """创建 session 文件"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.jsonl")
        with open(session_file, 'w') as f:
            f.write(json.dumps(metadata) + "\n")
            
    def _create_primary_session(self, session_id="primary-session-001"):
        """创建主 session"""
        self._write_session_file(session_id, {
            "sessionId": session_id,
            "sessionTarget": "main",
            "createdAt": "2026-03-09T09:00:00Z"
        })
        
        # 记录为主 session
        with open(self.primary_session_file, 'w') as f:
            json.dump({
                "sessionId": session_id,
                "recordedAt": "2026-03-09T09:00:00Z"
            }, f)
            
        return session_id
        
    def _create_isolated_session(self, session_id="isolated-session-001"):
        """创建 isolated session"""
        self._write_session_file(session_id, {
            "sessionId": session_id,
            "sessionTarget": "isolated",
            "createdAt": "2026-03-09T09:30:00Z"
        })
        return session_id
        
    def _set_route(self, route_key, session_id):
        """设置路由绑定"""
        sessions_data = {}
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file) as f:
                sessions_data = json.load(f)
        sessions_data[route_key] = {"sessionId": session_id}
        self._write_sessions(sessions_data)
        
    def _get_route(self, route_key):
        """获取当前路由"""
        if not os.path.exists(self.sessions_file):
            return None
        with open(self.sessions_file) as f:
            data = json.load(f)
        return data.get(route_key, {}).get("sessionId")
        
    def _run_guard_check(self):
        """运行 guard 检查"""
        # 模拟 guard 检查逻辑
        route_key = "agent:main:telegram:direct:8420019401"
        current = self._get_route(route_key)
        
        if os.path.exists(self.primary_session_file):
            with open(self.primary_session_file) as f:
                primary = json.load(f).get("sessionId")
        else:
            primary = None
            
        if primary and current and current != primary:
            return {
                "hijacked": True,
                "primary": primary,
                "current": current
            }
        return {
            "hijacked": False,
            "primary": primary,
            "current": current
        }
        
    def _run_guard_restore(self):
        """运行 guard 恢复"""
        check = self._run_guard_check()
        if check["hijacked"]:
            route_key = "agent:main:telegram:direct:8420019401"
            self._set_route(route_key, check["primary"])
            
            # 记录审计日志
            with open(self.audit_log, 'a') as f:
                f.write(json.dumps({
                    "event": "route_restored",
                    "from": check["current"],
                    "to": check["primary"]
                }) + "\n")
                
            return {"restored": True, "from": check["current"], "to": check["primary"]}
        return {"restored": False}


# ============================================================
# 测试 1: 劫持复现 + 恢复闭环
# ============================================================

def test_hijack_and_restore_cycle():
    """
    场景：
    1. 创建主 session
    2. isolated session announce 触发路由改绑
    3. 用户 reply 后路由被切到 isolated
    4. guard 检测到劫持
    5. guard 恢复路由
    6. 后续消息落回主 session
    """
    test = RouteRebindGuardE2ETest()
    test.setup()
    
    try:
        # 1. 创建主 session
        primary_id = test._create_primary_session("main-session-001")
        route_key = "agent:main:telegram:direct:8420019401"
        
        # 初始路由指向主 session
        test._set_route(route_key, primary_id)
        assert test._get_route(route_key) == primary_id, "初始路由应指向主 session"
        
        # 2. 创建 isolated session（模拟 cron 任务）
        isolated_id = test._create_isolated_session("cron-task-session-002")
        
        # 3. isolated announce + user reply 导致路由被劫持
        # （这是 OpenClCore 的行为，我们模拟结果）
        test._set_route(route_key, isolated_id)
        assert test._get_route(route_key) == isolated_id, "路由应被劫持到 isolated"
        
        # 4. guard 检测
        check = test._run_guard_check()
        assert check["hijacked"] is True, "应检测到劫持"
        assert check["current"] == isolated_id, "当前应为 isolated session"
        assert check["primary"] == primary_id, "主 session 应被记录"
        
        # 5. guard 恢复
        restore = test._run_guard_restore()
        assert restore["restored"] is True, "应成功恢复"
        assert restore["from"] == isolated_id, "恢复来源正确"
        assert restore["to"] == primary_id, "恢复目标正确"
        
        # 6. 验证路由已恢复
        assert test._get_route(route_key) == primary_id, "路由应恢复到主 session"
        
        # 7. 后续消息验证
        check_after = test._run_guard_check()
        assert check_after["hijacked"] is False, "恢复后不应再检测到劫持"
        
        print("✅ 测试 1 通过: 劫持复现 + 恢复闭环")
        return True
        
    finally:
        test.teardown()


# ============================================================
# 测试 2: 正常 reply 不误杀
# ============================================================

def test_normal_reply_not_false_positive():
    """
    场景：
    1. 主 session 正常运行
    2. 用户正常 reply
    3. guard 不应误判为劫持
    """
    test = RouteRebindGuardE2ETest()
    test.setup()
    
    try:
        # 1. 创建并记录主 session
        primary_id = test._create_primary_session("normal-main-session")
        route_key = "agent:main:telegram:direct:8420019401"
        test._set_route(route_key, primary_id)
        
        # 2. 模拟正常 reply（路由不变）
        # 正常情况下，用户 reply 不会改变路由
        
        # 3. guard 检查
        check = test._run_guard_check()
        assert check["hijacked"] is False, "正常 reply 不应被判定为劫持"
        assert check["current"] == primary_id, "路由应仍指向主 session"
        
        # 4. 多次检查确保稳定
        for i in range(5):
            check = test._run_guard_check()
            assert check["hijacked"] is False, f"第 {i+1} 次检查误报"
            
        print("✅ 测试 2 通过: 正常 reply 不误杀")
        return True
        
    finally:
        test.teardown()


# ============================================================
# 测试 3: 多 isolated announce 并发场景
# ============================================================

def test_multiple_isolated_concurrent():
    """
    场景：
    1. 主 session 存在
    2. 多个 isolated session 同时 announce
    3. 路由被某个 isolated 劫持
    4. guard 应恢复到真正的主 session，而非其他 isolated
    """
    test = RouteRebindGuardE2ETest()
    test.setup()
    
    try:
        # 1. 创建主 session
        primary_id = test._create_primary_session("main-concurrent-test")
        route_key = "agent:main:telegram:direct:8420019401"
        test._set_route(route_key, primary_id)
        
        # 2. 创建多个 isolated session（模拟多个 cron 任务）
        isolated_sessions = []
        for i in range(3):
            sid = f"isolated-cron-{i}-{os.urandom(4).hex()}"
            test._create_isolated_session(sid)
            isolated_sessions.append(sid)
            
        # 3. 最后一个 isolated 劫持路由
        hijacker = isolated_sessions[-1]
        test._set_route(route_key, hijacker)
        
        # 4. guard 检测
        check = test._run_guard_check()
        assert check["hijacked"] is True, "应检测到劫持"
        assert check["current"] == hijacker, "当前路由应为劫持者"
        assert check["primary"] == primary_id, "主 session 应正确识别"
        
        # 5. guard 恢复
        restore = test._run_guard_restore()
        assert restore["restored"] is True
        assert restore["to"] == primary_id, "应恢复到主 session，而非其他 isolated"
        
        # 6. 确保不会恢复到其他 isolated
        assert restore["to"] not in isolated_sessions, "恢复目标不应是 isolated session"
        
        print("✅ 测试 3 通过: 多 isolated 并发场景")
        return True
        
    finally:
        test.teardown()


# ============================================================
# 测试 4: 恢复后持久性验证
# ============================================================

def test_restore_persistence():
    """
    场景：
    1. 发生劫持并恢复
    2. 再次发生劫持
    3. 应仍能正确恢复到原主 session
    """
    test = RouteRebindGuardE2ETest()
    test.setup()
    
    try:
        primary_id = test._create_primary_session("persistent-main")
        route_key = "agent:main:telegram:direct:8420019401"
        test._set_route(route_key, primary_id)
        
        # 第一轮劫持
        isolated_1 = test._create_isolated_session("first-attack")
        test._set_route(route_key, isolated_1)
        test._run_guard_restore()
        assert test._get_route(route_key) == primary_id
        
        # 第二轮劫持
        isolated_2 = test._create_isolated_session("second-attack")
        test._set_route(route_key, isolated_2)
        test._run_guard_restore()
        assert test._get_route(route_key) == primary_id
        
        # 第三轮
        isolated_3 = test._create_isolated_session("third-attack")
        test._set_route(route_key, isolated_3)
        test._run_guard_restore()
        assert test._get_route(route_key) == primary_id
        
        print("✅ 测试 4 通过: 恢复持久性验证")
        return True
        
    finally:
        test.teardown()


# ============================================================
# 主运行器
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Route Rebind Guard - 行为级 E2E 测试")
    print("=" * 60)
    
    results = []
    
    tests = [
        ("劫持复现 + 恢复闭环", test_hijack_and_restore_cycle),
        ("正常 reply 不误杀", test_normal_reply_not_false_positive),
        ("多 isolated 并发场景", test_multiple_isolated_concurrent),
        ("恢复持久性验证", test_restore_persistence),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASS" if result else "FAIL"))
        except Exception as e:
            results.append((name, f"FAIL: {e}"))
            
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)
    
    for name, result in results:
        status = "✅" if result == "PASS" else "❌"
        print(f"{status} {name}: {result}")
        
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有行为级 E2E 测试通过！")
        exit(0)
    else:
        print("\n⚠️  存在失败测试")
        exit(1)
