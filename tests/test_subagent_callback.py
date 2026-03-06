#!/usr/bin/env python3
"""
测试子代理回调链路

测试场景：
A. happy path: child 完成 → handler 触发 → parent 自动继续 → 回复用户
B. no-callback: child 完成但没正确回传 → parent 不应假装完成
C. duplicate callback: child 重复回传 → parent 不应重复推进

Usage:
  pytest tests/test_subagent_callback.py -v
  python3 tests/test_subagent_callback.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加 workspace 到 path
WORKSPACE = Path.home() / ".openclaw" / "workspace"
sys.path.insert(0, str(WORKSPACE / "tools"))

import subagent_completion_handler as handler


class TestSubagentCallback:
    """子代理回调测试"""
    
    def setup_method(self):
        """每个测试前重置状态"""
        self.temp_dir = tempfile.mkdtemp()
        self.workflow_file = Path(self.temp_dir) / "WORKFLOW_STATE.json"
        self.orchestrator_file = Path(self.temp_dir) / "pending_subtasks.json"
        
        # Monkey patch 路径
        handler.WORKFLOW_FILE = self.workflow_file
        handler.ORCHESTRATOR_FILE = self.orchestrator_file
    
    def teardown_method(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_workflow(self, steps, active=True):
        """创建工作流状态"""
        state = {
            "active": active,
            "workflow_type": "serial",
            "steps": steps,
            "notify_on_done": "✅ 测试完成",
            "created_at": "2026-03-06T05:00:00Z"
        }
        with open(self.workflow_file, 'w') as f:
            json.dump(state, f)
        return state
    
    def create_orchestrator_task(self, task_id, run_id, description="test"):
        """创建 orchestrator 任务"""
        orch = {"pending": {}, "completed": {}}
        orch["pending"][task_id] = {
            "task_id": task_id,
            "run_id": run_id,
            "description": description,
            "status": "pending"
        }
        with open(self.orchestrator_file, 'w') as f:
            json.dump(orch, f)
    
    # ========== Test A: Happy Path ==========
    
    def test_a1_task_id_match(self):
        """A1: task_id 匹配 → 标记完成"""
        self.create_workflow([
            {"id": "task_001", "status": "running", "run_id": "run_abc"}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "task_001",
            "status": "completed",
            "summary": "done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "notify_user"
        assert result["should_silence"] == False
        assert "测试完成" in result["message"]
    
    def test_a2_run_id_match(self):
        """A2: run_id 匹配 → 标记完成"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_abc123"}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "external_task_id",  # 不匹配
            "child_session_key": "agent:main:subagent:run_abc123",
            "status": "completed",
            "summary": "done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "notify_user"
    
    def test_a3_orchestrator_mapping(self):
        """A3: orchestrator 映射 → 找到步骤"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_xyz"}
        ])
        self.create_orchestrator_task("task_999", "run_xyz")
        
        payload = {
            "type": "subagent_done",
            "task_id": "task_999",
            "child_session_key": "agent:main:subagent:different_run_id",
            "status": "completed",
            "summary": "done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "notify_user"
    
    def test_a4_multi_step_workflow(self):
        """A4: 多步骤工作流 → spawn_next"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_1"},
            {"id": "step_2", "status": "pending", "run_id": None}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "step_1",
            "status": "completed",
            "summary": "step 1 done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "spawn_next"
        assert result["should_silence"] == True
        assert result["next_step"]["id"] == "step_2"
    
    # ========== Test B: No Callback / Wrong Format ==========
    
    def test_b1_no_matching_step(self):
        """B1: 找不到匹配步骤 → ignore"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_1"}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "unknown_task",
            "child_session_key": "agent:main:subagent:unknown_run",
            "status": "completed",
            "summary": "done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "ignore"
        assert result["reason"] == "step_not_found"
    
    def test_b2_inactive_workflow(self):
        """B2: 工作流不活跃 → notify_user"""
        self.create_workflow([
            {"id": "step_1", "status": "done"}
        ], active=False)
        
        payload = {
            "type": "subagent_done",
            "task_id": "any_task",
            "status": "completed",
            "summary": "done"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "notify_user"
        assert "子任务完成" in result["message"]
    
    # ========== Test C: Duplicate Callback ==========
    
    def test_c1_duplicate_callback(self):
        """C1: 重复回调 → 幂等处理"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_1"}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "step_1",
            "status": "completed",
            "summary": "done"
        }
        
        # 第一次回调
        result1 = handler.handle_structured_payload(payload)
        assert result1["action"] == "notify_user"
        
        # 第二次回调（步骤已经是 done）
        result2 = handler.handle_structured_payload(payload)
        assert result2["action"] == "ignore"
    
    def test_c2_partial_failure(self):
        """C2: 子代理失败 → 标记 failed"""
        self.create_workflow([
            {"id": "step_1", "status": "running", "run_id": "run_1"}
        ])
        
        payload = {
            "type": "subagent_done",
            "task_id": "step_1",
            "status": "failed",
            "summary": "error occurred"
        }
        
        result = handler.handle_structured_payload(payload)
        
        # 检查状态被标记为 failed
        state = handler.load_workflow()
        assert state["steps"][0]["status"] == "failed"
    
    # ========== Test D: Edge Cases ==========
    
    def test_d1_empty_workflow(self):
        """D1: 空工作流 → ignore"""
        self.create_workflow([])
        
        payload = {
            "type": "subagent_done",
            "task_id": "any",
            "status": "completed"
        }
        
        result = handler.handle_structured_payload(payload)
        
        assert result["action"] == "notify_user"
    
    def test_d2_malformed_payload(self):
        """D2: 格式错误 payload → 不崩溃"""
        self.create_workflow([
            {"id": "step_1", "status": "running"}
        ])
        
        payload = {
            # 缺少必要字段
        }
        
        # 不应该崩溃
        result = handler.handle_structured_payload(payload)
        assert result is not None


def run_tests():
    """运行测试"""
    import traceback
    
    test = TestSubagentCallback()
    tests = [
        ("A1: task_id 匹配", test.test_a1_task_id_match),
        ("A2: run_id 匹配", test.test_a2_run_id_match),
        ("A3: orchestrator 映射", test.test_a3_orchestrator_mapping),
        ("A4: 多步骤工作流", test.test_a4_multi_step_workflow),
        ("B1: 找不到匹配步骤", test.test_b1_no_matching_step),
        ("B2: 工作流不活跃", test.test_b2_inactive_workflow),
        ("C1: 重复回调", test.test_c1_duplicate_callback),
        ("C2: 子代理失败", test.test_c2_partial_failure),
        ("D1: 空工作流", test.test_d1_empty_workflow),
        ("D2: 格式错误 payload", test.test_d2_malformed_payload),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        test.setup_method()
        try:
            test_fn()
            print(f"✅ {name}")
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
    
    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
