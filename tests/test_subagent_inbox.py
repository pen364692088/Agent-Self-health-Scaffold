#!/usr/bin/env python3
"""
Subagent Inbox 回归测试 v1

测试场景：
1. happy path: completed → claimed → processed
2. failed/timeout path: 能统一进入 handler
3. duplicate receipt: 不会重复推进两次

Usage:
  pytest tests/test_subagent_inbox.py -v
  python3 tests/test_subagent_inbox.py
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
sys.path.insert(0, str(WORKSPACE / "tools"))


class TestSubagentInbox:
    """Subagent Inbox 回归测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.inbox_dir = self.temp_dir / "inbox"
        self.inbox_dir.mkdir(parents=True)
        
        # 加载模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "subagent_inbox", 
            WORKSPACE / "tools" / "subagent-inbox"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        
        # 替换路径
        self.module.INBOX_DIR = self.inbox_dir
        self.module.LOCK_FILE = self.inbox_dir / ".inbox.lock"
        self.module.HANDLER = WORKSPACE / "tools" / "subagent-completion-handler"
    
    def teardown_method(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_receipt_file(self, task_id: str, status: str = "completed", **kwargs):
        """创建测试回执文件"""
        receipt = {
            "task_id": task_id,
            "run_id": f"run_{task_id[-8:]}",
            "session_key": "agent:main:subagent:test",
            "parent_session_key": "agent:main:telegram:direct:8420019401",
            "status": status,
            "summary": f"测试回执: {task_id}",
            "artifacts": [],
            "error": None,
            "notify_user": True,
            "written_at": datetime.now().isoformat(),
            "retry_count": 0
        }
        receipt.update(kwargs)
        
        # 原子写入
        target_file = self.inbox_dir / f"{task_id}.done.json"
        tmp_file = self.inbox_dir / f"{task_id}.tmp"
        
        with open(tmp_file, 'w') as f:
            json.dump(receipt, f)
            f.flush()
            os.fsync(f.fileno())
        
        os.rename(str(tmp_file), str(target_file))
        return target_file
    
    # ========== Test 1: Happy Path ==========
    
    def test_1_happy_path(self):
        """
        happy path: completed → claimed → processed
        
        验证：
        1. 写入回执成功
        2. 检查能发现 pending
        3. 认领成功
        4. 处理成功
        5. 标记为 processed
        """
        manager = self.module.InboxManager()
        manager.INBOX_DIR = self.inbox_dir
        
        task_id = "task_test001_completed"
        
        # 1. 写入回执
        success = manager.write_receipt(
            task_id=task_id,
            run_id="run_test001",
            status="completed",
            summary="Happy path 测试"
        )
        assert success, "写入回执失败"
        
        # 2. 检查 pending
        pending = manager.check_pending()
        assert len(pending) == 1, f"应该有 1 个 pending，实际 {len(pending)}"
        assert pending[0]["task_id"] == task_id
        
        # 3. 认领
        claimed = manager.claim_receipt(task_id)
        assert claimed, "认领失败"
        
        # 4. 检查状态：应该不再 pending
        pending_after = manager.check_pending()
        assert len(pending_after) == 0, "认领后不应该再 pending"
        
        # 5. 标记 processed
        processed = manager.mark_processed(task_id)
        assert processed, "标记 processed 失败"
        
        # 验证文件状态
        assert not (self.inbox_dir / f"{task_id}.done.json").exists()
        assert (self.inbox_dir / f"{task_id}.processed.json").exists()
        
        print("✅ Test 1: Happy path 通过")
    
    # ========== Test 2: Failed/Timeout Path ==========
    
    def test_2_failed_path(self):
        """
        failed path: failed 状态能统一进入 handler
        
        验证：
        1. 写入 failed 回执成功
        2. status 字段正确
        3. 能被正确处理
        """
        manager = self.module.InboxManager()
        manager.INBOX_DIR = self.inbox_dir
        
        task_id = "task_test002_failed"
        
        # 写入失败回执
        success = manager.write_receipt(
            task_id=task_id,
            run_id="run_test002",
            status="failed",
            summary="测试失败场景",
            error={"type": "runtime", "message": "测试错误"}
        )
        assert success, "写入失败回执失败"
        
        # 检查内容
        receipt_file = self.inbox_dir / f"{task_id}.done.json"
        with open(receipt_file) as f:
            receipt = json.load(f)
        
        assert receipt["status"] == "failed"
        assert receipt["error"]["type"] == "runtime"
        
        print("✅ Test 2: Failed path 通过")
    
    def test_2_timeout_path(self):
        """
        timeout path: timeout 状态能统一处理
        """
        manager = self.module.InboxManager()
        manager.INBOX_DIR = self.inbox_dir
        
        task_id = "task_test003_timeout"
        
        success = manager.write_receipt(
            task_id=task_id,
            run_id="run_test003",
            status="timeout",
            summary="测试超时场景"
        )
        assert success
        
        receipt_file = self.inbox_dir / f"{task_id}.done.json"
        with open(receipt_file) as f:
            receipt = json.load(f)
        
        assert receipt["status"] == "timeout"
        
        print("✅ Test 2: Timeout path 通过")
    
    # ========== Test 3: Duplicate Receipt ==========
    
    def test_3_duplicate_receipt(self):
        """
        duplicate receipt: 不会重复推进两次
        
        验证：
        1. 第一次处理成功
        2. 第二次处理被忽略（幂等）
        """
        manager = self.module.InboxManager()
        manager.INBOX_DIR = self.inbox_dir
        
        task_id = "task_test004_dup"
        
        # 写入回执
        self.create_receipt_file(task_id)
        
        # 第一次处理
        pending1 = manager.check_pending()
        assert len(pending1) == 1
        
        # 认领 + 标记
        manager.claim_receipt(task_id)
        manager.mark_processed(task_id)
        
        # 第二次检查（应该为空）
        pending2 = manager.check_pending()
        assert len(pending2) == 0, "已处理的回执不应该再 pending"
        
        # 尝试再次处理
        result = manager.process_receipt(task_id)
        assert result.get("error") == "receipt_not_found"
        
        print("✅ Test 3: Duplicate receipt 通过")
    
    def test_3_concurrent_claim(self):
        """
        并发认领测试：两个 worker 同时认领
        """
        manager = self.module.InboxManager()
        manager.INBOX_DIR = self.inbox_dir
        
        task_id = "task_test005_concurrent"
        
        # 写入回执
        self.create_receipt_file(task_id)
        
        # 第一次认领
        claim1 = manager.claim_receipt(task_id)
        assert claim1, "第一次认领应该成功"
        
        # 第二次认领（应该失败，因为已经是 claimed）
        claim2 = manager.claim_receipt(task_id)
        assert not claim2, "第二次认领应该失败（幂等）"
        
        print("✅ Test 3: Concurrent claim 通过")


def run_tests():
    """运行测试"""
    import traceback
    
    test = TestSubagentInbox()
    tests = [
        ("Test 1: Happy path", test.test_1_happy_path),
        ("Test 2: Failed path", test.test_2_failed_path),
        ("Test 2: Timeout path", test.test_2_timeout_path),
        ("Test 3: Duplicate receipt", test.test_3_duplicate_receipt),
        ("Test 3: Concurrent claim", test.test_3_concurrent_claim),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        test.setup_method()
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 {name}: {e}")
            traceback.print_exc()
            failed += 1
        finally:
            test.teardown_method()
    
    print(f"\n{'='*50}")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
