"""
Tests for Phase 3: 幂等与防漂移强化
"""

import json
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.task_dossier import TaskDossier, TaskContract, TaskState
from core.lease_manager import LeaseManager, DuplicateCompletionProtection
from core.consistency_checker import StateConsistencyChecker, check_task_consistency


class TestLeaseManager:
    """测试租约管理器"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second"}
        ]
        
        dossier.initialize(contract, plan)
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_acquire_lease(self, setup):
        """测试获取租约"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        success, lease = manager.acquire("S01", "worker_1")
        
        assert success is True
        assert lease["owner"] == "worker_1"
        assert lease["status"] == "active"
    
    def test_idempotent_acquire(self, setup):
        """测试幂等获取"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        # 第一次获取
        success1, lease1 = manager.acquire("S01", "worker_1")
        
        # 同一个 owner 再次获取
        success2, lease2 = manager.acquire("S01", "worker_1")
        
        assert success1 is True
        assert success2 is True
        assert lease1["acquired_at"] == lease2["acquired_at"]
    
    def test_acquire_held_lease(self, setup):
        """测试获取被持有的租约"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        # worker_1 获取租约
        manager.acquire("S01", "worker_1", ttl_seconds=300)
        
        # worker_2 尝试获取
        success, result = manager.acquire("S01", "worker_2")
        
        assert success is False
        assert result["reason"] == "lease_held"
    
    def test_acquire_expired_lease(self, setup):
        """测试获取过期租约"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        # 获取一个短租约
        manager.acquire("S01", "worker_1", ttl_seconds=1)
        
        # 等待过期
        import time
        time.sleep(2)
        
        # worker_2 尝试获取
        success, lease = manager.acquire("S01", "worker_2")
        
        assert success is True
        assert lease["owner"] == "worker_2"
        assert lease["reclaim_count"] == 1
    
    def test_lease_renewal(self, setup):
        """测试租约续期"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        manager.acquire("S01", "worker_1", ttl_seconds=60)
        
        # 续期
        success, lease = manager.renew("S01", "worker_1", extend_seconds=120)
        
        assert success is True
        # 检查过期时间延长了
    
    def test_lease_release(self, setup):
        """测试租约释放"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        manager.acquire("S01", "worker_1")
        
        # 释放
        success, message = manager.release("S01", "worker_1", reason="completed")
        
        assert success is True
        
        # 检查状态
        is_valid, lease = manager.check("S01")
        assert is_valid is False
        assert lease["status"] == "released"
    
    def test_lease_heartbeat(self, setup):
        """测试心跳"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        manager.acquire("S01", "worker_1")
        
        # 发送心跳
        success, lease = manager.heartbeat("S01", "worker_1")
        
        assert success is True
        assert lease["heartbeat"]["missed_count"] == 0
    
    def test_lease_checksum_protection(self, setup):
        """测试校验和保护"""
        dossier = setup
        manager = LeaseManager(dossier.steps_dir)
        
        manager.acquire("S01", "worker_1")
        
        # 篡改租约文件
        lease_file = dossier.steps_dir / "S01" / "lease.json"
        with open(lease_file) as f:
            lease = json.load(f)
        
        lease["owner"] = "hacker"
        
        with open(lease_file, 'w') as f:
            json.dump(lease, f)
        
        # 检查应该失败
        is_valid, result = manager.check("S01")
        assert is_valid is False


class TestDuplicateCompletionProtection:
    """测试重复完成保护"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [{"step_id": "S01", "title": "Step 1", "goal": "First"}]
        
        dossier.initialize(contract, plan)
        
        # 完成步骤
        dossier.update_step("S01", "success")
        dossier.save_handoff("S01", "# Handoff")
        evidence_dir = dossier.evidence_dir / "S01"
        evidence_dir.mkdir(exist_ok=True)
        (evidence_dir / "evidence.txt").write_text("evidence")
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_prevent_duplicate_completion(self, setup):
        """测试防止重复完成"""
        dossier = setup
        protection = DuplicateCompletionProtection(dossier)
        
        # 第一次标记完成
        success1, msg1 = protection.mark_completed({
            "task_id": dossier.task_id,
            "status": "completed"
        })
        
        assert success1 is True
        
        # 第二次尝试
        success2, msg2 = protection.mark_completed({
            "task_id": dossier.task_id,
            "status": "completed"
        })
        
        assert success2 is False
        assert "already" in msg2.lower()
    
    def test_verify_completion_integrity(self, setup):
        """测试完成完整性验证"""
        dossier = setup
        protection = DuplicateCompletionProtection(dossier)
        
        # 标记完成
        protection.mark_completed({
            "task_id": dossier.task_id,
            "status": "completed"
        })
        
        # 验证完整性
        is_valid, report = protection.verify_completion_integrity()
        
        assert is_valid is True
        assert len(report["issues"]) == 0


class TestConsistencyChecker:
    """测试一致性检查器"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second"}
        ]
        
        dossier.initialize(contract, plan)
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_consistency_check_passing(self, setup):
        """测试一致性检查通过"""
        dossier = setup
        
        # 完成步骤并添加证据
        dossier.update_step("S01", "success")
        dossier.save_step_result("S01", {
            "step_id": "S01",
            "status": "success",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "attempts": 1
        })
        dossier.save_handoff("S01", "# Handoff")
        evidence_dir = dossier.evidence_dir / "S01"
        evidence_dir.mkdir(exist_ok=True)
        (evidence_dir / "evidence.txt").write_text("evidence")
        
        # 检查一致性
        report = check_task_consistency(dossier)
        
        assert report.is_consistent is True
    
    def test_consistency_check_missing_evidence(self, setup):
        """测试缺少证据的一致性检查"""
        dossier = setup
        
        # 标记步骤成功但不添加证据
        dossier.update_step("S01", "success")
        dossier.save_step_result("S01", {
            "step_id": "S01",
            "status": "success",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "attempts": 1
        })
        
        # 检查一致性
        report = check_task_consistency(dossier)
        
        assert report.is_consistent is False
        assert any("no evidence" in i.lower() for i in report.issues)
    
    def test_consistency_check_completed_with_failed_step(self, setup):
        """测试已完成任务有失败步骤"""
        dossier = setup
        
        # 标记一个步骤失败
        dossier.update_step("S01", "failed_blocked")
        
        # 但任务状态设为完成
        state = dossier.load_state()
        state.status = "completed"
        dossier._save_state(state)
        
        # 检查一致性
        report = check_task_consistency(dossier)
        
        assert report.is_consistent is False
        assert any("failed" in i.lower() for i in report.issues)


class TestHandoffDriftProtection:
    """测试 handoff 漂移保护"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [{"step_id": "S01", "title": "Step 1", "goal": "First"}]
        
        dossier.initialize(contract, plan)
        
        # 完成步骤
        dossier.update_step("S01", "success")
        dossier.save_step_result("S01", {
            "step_id": "S01",
            "status": "success",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "attempts": 1
        })
        dossier.save_handoff("S01", "# Original Handoff\n\nThis is correct.")
        
        evidence_dir = dossier.evidence_dir / "S01"
        evidence_dir.mkdir(exist_ok=True)
        (evidence_dir / "evidence.txt").write_text("evidence")
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_handoff_cannot_override_state(self, setup):
        """测试 handoff 不能覆盖状态"""
        dossier = setup
        
        # 获取状态
        state = dossier.load_state()
        original_status = state.steps[0]["status"]
        
        # 修改 handoff（模拟漂移）
        handoff_file = dossier.handoff_dir / "S01.md"
        with open(handoff_file, 'w') as f:
            f.write("# Modified Handoff\n\nThis is WRONG but handoff is human-readable.")
        
        # 重新加载状态
        state_after = dossier.load_state()
        
        # 状态应该不受影响
        assert state_after.steps[0]["status"] == original_status
        
        # 一致性检查应该仍然通过（因为 result.json 和 evidence 存在）
        report = check_task_consistency(dossier)
        # 应该通过，因为 truth 在 result.json 和 state 中


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
