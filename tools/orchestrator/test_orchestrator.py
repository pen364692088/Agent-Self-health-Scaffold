#!/usr/bin/env python3
"""
Orchestrator Integration Tests
Tests all 4 required scenarios from Callback.txt
"""

import json
import os
import sys
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator, Subtask, SubtaskStatus
from subagent_receipt import SubagentReceiptHandler, subtask_done, subtask_fail


class TestOrchestrator:
    """Test suite for the orchestrator system"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="orchestrator_test_")
        self.orch = None
        self.passed = 0
        self.failed = 0
    
    def setup(self):
        """Setup fresh orchestrator for each test"""
        self.orch = Orchestrator(workspace_dir=self.test_dir)
    
    def teardown(self):
        """Cleanup after each test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.test_dir = tempfile.mkdtemp(prefix="orchestrator_test_")
    
    def assert_true(self, condition, message):
        """Simple assertion with tracking"""
        if condition:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            print(f"  ❌ {message}")
    
    def test_scenario_1_announce_normal(self):
        """
        Scenario 1: announce 正常（回执到达）→ 主流程继续
        Test that explicit receipts allow main flow to continue
        """
        print("\n📝 Scenario 1: Normal announce/receipt flow")
        self.setup()
        
        # Spawn a subtask
        task_id = self.orch.spawn_subtask(
            run_id="run_001",
            child_session_key="session_001",
            description="Test task 1"
        )
        
        self.assert_true(task_id is not None, "Task spawned successfully")
        self.assert_true(len(self.orch.pending_subtasks) == 1, "Task in pending queue")
        
        # Simulate explicit receipt
        receipt = {
            "task_id": task_id,
            "run_id": "run_001",
            "status": "ok",
            "summary": "Task completed successfully",
            "output_paths": []
        }
        
        result = self.orch.process_explicit_receipt(receipt)
        self.assert_true(result, "Receipt processed successfully")
        self.assert_true(len(self.orch.pending_subtasks) == 0, "No pending tasks after receipt")
        self.assert_true(len(self.orch.completed_subtasks) == 1, "Task moved to completed")
        
        self.teardown()
    
    def test_scenario_2_announce_lost(self):
        """
        Scenario 2: announce 丢失（无回执）→ join/poll 仍能继续
        Test that mailbox fallback works when announce is lost
        """
        print("\n📝 Scenario 2: Announce lost, mailbox fallback")
        self.setup()
        
        # Spawn a subtask
        task_id = self.orch.spawn_subtask(
            run_id="run_002",
            child_session_key="session_002",
            description="Test task 2"
        )
        
        self.assert_true(len(self.orch.pending_subtasks) == 1, "Task in pending queue")
        
        # Write mailbox file (simulating subagent completion without announce)
        handler = SubagentReceiptHandler(workspace_dir=self.test_dir)
        handler.send_done_receipt(
            task_id=task_id,
            run_id="run_002",
            summary="Completed via mailbox"
        )
        
        # Poll should find the mailbox file
        task = self.orch.pending_subtasks[task_id]
        result = self.orch._poll_single_task(task)
        
        self.assert_true(result, "Poll found mailbox completion")
        self.assert_true(task.status == SubtaskStatus.COMPLETED, "Task marked completed")
        self.assert_true(len(self.orch.pending_subtasks) == 0, "No pending after poll")
        
        self.teardown()
    
    def test_scenario_3_timeout_retry(self):
        """
        Scenario 3: subagent 卡死/超时 → 重试后成功 / 降级兜底成功
        Test timeout handling and retry logic
        """
        print("\n📝 Scenario 3: Timeout and retry handling")
        self.setup()
        
        # Spawn with short deadline for testing
        task_id = self.orch.spawn_subtask(
            run_id="run_003",
            child_session_key="session_003",
            description="Test timeout",
            deadline=datetime.now() + timedelta(seconds=1),
            max_retries=2
        )
        
        task = self.orch.pending_subtasks[task_id]
        self.assert_true(task.max_retries == 2, "Max retries configured")
        
        # Wait for timeout
        time.sleep(1.5)
        
        # First timeout should trigger retry
        result = self.orch._poll_single_task(task)
        self.assert_true(task.retries == 1, "First timeout triggers retry")
        self.assert_true(task.status == SubtaskStatus.RETRYING, "Status is retrying")
        
        # Simulate success after retry
        handler = SubagentReceiptHandler(workspace_dir=self.test_dir)
        handler.send_done_receipt(
            task_id=task_id,
            run_id="run_003",
            summary="Succeeded on retry"
        )
        
        result = self.orch._poll_single_task(task)
        self.assert_true(result, "Task completed after retry")
        self.assert_true(task.status == SubtaskStatus.COMPLETED, "Final status is completed")
        
        self.teardown()
    
    def test_scenario_4_restart_recovery(self):
        """
        Scenario 4: 主 agent 重启 → 能从持久化 pending/邮箱恢复并继续
        Test recovery from persistent storage
        """
        print("\n📝 Scenario 4: Restart recovery from storage")
        self.setup()
        
        # Spawn a task
        task_id = self.orch.spawn_subtask(
            run_id="run_004",
            child_session_key="session_004",
            description="Recovery test"
        )
        
        # Write mailbox
        handler = SubagentReceiptHandler(workspace_dir=self.test_dir)
        handler.send_done_receipt(
            task_id=task_id,
            run_id="run_004",
            summary="Completed before restart"
        )
        
        # Simulate restart by creating new orchestrator instance
        orch2 = Orchestrator(workspace_dir=self.test_dir)
        
        # Should load pending task
        self.assert_true(len(orch2.pending_subtasks) == 1, "Loaded pending task after restart")
        
        # Poll should complete from mailbox
        orch2._poll_all()
        self.assert_true(len(orch2.pending_subtasks) == 0, "No pending after poll")
        self.assert_true(len(orch2.completed_subtasks) == 1, "Task completed after recovery")
        
        self.teardown()
    
    def test_parallel_subtasks(self):
        """
        Test parallel subtasks with unified sync point
        """
        print("\n📝 Parallel subtasks test")
        self.setup()
        
        # Spawn 3 parallel tasks
        task_ids = []
        for i in range(3):
            task_id = self.orch.spawn_subtask(
                run_id=f"run_p{i}",
                child_session_key=f"session_p{i}",
                description=f"Parallel task {i}"
            )
            task_ids.append(task_id)
        
        self.assert_true(len(self.orch.pending_subtasks) == 3, "3 parallel tasks spawned")
        
        # Complete all via mailbox
        handler = SubagentReceiptHandler(workspace_dir=self.test_dir)
        for task_id in task_ids:
            handler.send_done_receipt(
                task_id=task_id,
                run_id=f"run_p{task_ids.index(task_id)}",
                summary=f"Parallel task completed"
            )
        
        # Join should complete all
        success = self.orch.join_all(timeout=5)
        self.assert_true(success, "Join completed all parallel tasks")
        self.assert_true(len(self.orch.completed_subtasks) == 3, "All 3 tasks completed")
        
        self.teardown()
    
    def test_run_report(self):
        """
        Test run report generation
        """
        print("\n📝 Run report test")
        self.setup()
        
        # Spawn and complete a task
        task_id = self.orch.spawn_subtask(
            run_id="run_report",
            child_session_key="session_report",
            description="Report test"
        )
        
        handler = SubagentReceiptHandler(workspace_dir=self.test_dir)
        handler.send_done_receipt(
            task_id=task_id,
            run_id="run_report",
            summary="For report"
        )
        
        self.orch.join_all(timeout=2)
        
        # Generate report
        report = self.orch.generate_run_report()
        
        self.assert_true('total_tasks' in report, "Report has total_tasks")
        self.assert_true(report['completed_tasks'] == 1, "Report shows 1 completed")
        self.assert_true('summary_stats' in report, "Report has summary stats")
        
        # Check report file was written
        report_files = list(Path(self.test_dir).glob("tools/orchestrator/run_report_*.json"))
        self.assert_true(len(report_files) > 0, "Report file written to disk")
        
        self.teardown()
    
    def run_all(self):
        """Run all tests"""
        print("=" * 60)
        print("Orchestrator Integration Tests")
        print("=" * 60)
        
        self.test_scenario_1_announce_normal()
        self.test_scenario_2_announce_lost()
        self.test_scenario_3_timeout_retry()
        self.test_scenario_4_restart_recovery()
        self.test_parallel_subtasks()
        self.test_run_report()
        
        print("\n" + "=" * 60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        # Final cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestOrchestrator()
    success = tester.run_all()
    sys.exit(0 if success else 1)
