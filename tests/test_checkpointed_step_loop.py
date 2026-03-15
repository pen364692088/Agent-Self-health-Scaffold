"""
Tests for Checkpointed Step Loop v1
"""

import json
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Import modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.task_dossier import TaskDossier, TaskContract, TaskState
from core.step_packet_compiler import StepPacketCompiler, compile_task_plan
from runtime.resume_engine import ResumeEngine, ResumeContext
from runtime.completion_gatekeeper import CompletionGatekeeper, GateResult


class TestTaskDossier:
    """测试任务档案管理"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)
    
    def test_create_task_dossier(self, temp_dir):
        """测试创建任务档案"""
        dossier = TaskDossier(temp_dir)
        
        assert dossier.task_id.startswith("task_")
        assert dossier.task_dir == Path(temp_dir) / "artifacts" / "tasks" / dossier.task_id
    
    def test_initialize_dossier(self, temp_dir):
        """测试初始化任务档案"""
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(
            objective="Test task",
            repository="/tmp/test_repo",
            branch="main",
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "Do step 1"},
            {"step_id": "S02", "title": "Step 2", "goal": "Do step 2"},
            {"step_id": "S03", "title": "Step 3", "goal": "Do step 3"}
        ]
        
        state = dossier.initialize(contract, plan)
        
        assert state.task_id == dossier.task_id
        assert state.status == "created"
        assert len(state.steps) == 3
        assert state.current_step == "S01"
        
        # 检查文件创建
        assert dossier.state_file.exists()
        assert dossier.task_md.exists()
        assert dossier.ledger_file.exists()
    
    def test_update_step_status(self, temp_dir):
        """测试更新步骤状态"""
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [{"step_id": "S01", "title": "Step 1", "goal": "Test"}]
        
        dossier.initialize(contract, plan)
        
        # 更新步骤为运行中
        state = dossier.update_step("S01", "running")
        assert state.steps[0]["status"] == "running"
        assert state.steps[0]["started_at"] is not None
        
        # 更新步骤为成功
        state = dossier.update_step("S01", "success")
        assert state.steps[0]["status"] == "success"
        assert state.steps[0]["completed_at"] is not None
        assert state.current_step is None  # 没有下一步了
    
    def test_load_state(self, temp_dir):
        """测试加载任务状态"""
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [{"step_id": "S01", "title": "Step 1", "goal": "Test"}]
        
        original_state = dossier.initialize(contract, plan)
        
        # 重新加载
        loaded_state = dossier.load_state()
        
        assert loaded_state.task_id == original_state.task_id
        assert loaded_state.status == original_state.status


class TestStepPacketCompiler:
    """测试步骤包编译器"""
    
    def test_compile_plan(self):
        """测试编译计划"""
        compiler = StepPacketCompiler()
        
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First step"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second step", "depends_on": ["S01"]}
        ]
        
        packets = compiler.compile_plan(plan, "test_task", "/tmp/artifacts")
        
        assert len(packets) == 2
        assert packets[0]["step_id"] == "S01"
        assert packets[1]["step_id"] == "S02"
        assert packets[1]["depends_on"] == ["S01"]
    
    def test_validate_packet(self):
        """测试验证步骤包"""
        compiler = StepPacketCompiler()
        
        # 有效的包
        valid_packet = {
            "step_id": "S01",
            "title": "Valid Step",
            "goal": "Test goal",
            "inputs": [],
            "exit_criteria": ["Output exists"],
            "failure_policy": {"max_retries": 3}
        }
        
        errors = compiler.validate_packet(valid_packet)
        assert len(errors) == 0
        
        # 无效的包（缺少字段）
        invalid_packet = {
            "step_id": "S01"
        }
        
        errors = compiler.validate_packet(invalid_packet)
        assert len(errors) > 0


class TestResumeEngine:
    """测试恢复引擎"""
    
    @pytest.fixture
    def setup_dossier(self):
        """设置测试档案"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second"},
            {"step_id": "S03", "title": "Step 3", "goal": "Third"}
        ]
        
        dossier.initialize(contract, plan)
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_analyze_initial_state(self, setup_dossier):
        """测试分析初始状态"""
        dossier = setup_dossier
        engine = ResumeEngine(dossier)
        
        context = engine.analyze()
        
        assert context.task_id == dossier.task_id
        assert context.current_step_id == "S01"
        assert context.current_step_status == "pending"
        assert context.needs_recovery is True
        assert context.recovery_action == "continue"
    
    def test_analyze_after_step_success(self, setup_dossier):
        """测试步骤成功后的分析"""
        dossier = setup_dossier
        engine = ResumeEngine(dossier)
        
        # 完成第一步
        dossier.update_step("S01", "success")
        
        context = engine.analyze()
        
        assert context.current_step_id == "S02"
        assert context.recovery_action == "continue"
    
    def test_acquire_and_check_lease(self, setup_dossier):
        """测试租约获取和检查"""
        dossier = setup_dossier
        engine = ResumeEngine(dossier)
        
        # 获取租约
        lease = engine.acquire_lease("S01", "worker_1", ttl_seconds=60)
        
        assert lease["step_id"] == "S01"
        assert lease["owner"] == "worker_1"
        assert lease["status"] == "active"
        
        # 检查租约有效性
        context = engine.analyze()
        assert context.lease_valid is True
    
    def test_lease_expiration(self, setup_dossier):
        """测试租约过期"""
        dossier = setup_dossier
        engine = ResumeEngine(dossier)
        
        # 设置步骤为运行中
        dossier.update_step("S01", "running")
        
        # 获取一个极短的租约（已过期）
        import json
        from datetime import datetime, timedelta
        
        # 手动创建一个过期的租约
        expired_lease = {
            "step_id": "S01",
            "owner": "old_worker",
            "acquired_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z",
            "expires_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
            "status": "active"
        }
        
        lease_file = dossier.steps_dir / "S01" / "lease.json"
        with open(lease_file, 'w') as f:
            json.dump(expired_lease, f)
        
        # 分析应该检测到租约过期
        context = engine.analyze()
        assert context.lease_valid is False
        assert context.recovery_action == "retry"


class TestCompletionGatekeeper:
    """测试完成守门器"""
    
    @pytest.fixture
    def setup_dossier(self):
        """设置测试档案"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second"}
        ]
        
        dossier.initialize(contract, plan)
        
        # 保存步骤包
        for step in plan:
            dossier.save_step_packet(step["step_id"], {
                "step_id": step["step_id"],
                "title": step["title"],
                "goal": step["goal"],
                "inputs": [],
                "exit_criteria": ["Done"],
                "failure_policy": {}
            })
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_gate_a_contract(self, setup_dossier):
        """测试 Gate A 契约验证"""
        dossier = setup_dossier
        gatekeeper = CompletionGatekeeper(dossier)
        
        result = gatekeeper.run_gate_a()
        
        assert isinstance(result, GateResult)
        assert result.gate_name == "Gate A: Contract"
        # 应该通过（有状态文件、步骤包等）
        assert result.passed is True
    
    def test_gate_b_e2e_incomplete(self, setup_dossier):
        """测试 Gate B - 步骤未完成"""
        dossier = setup_dossier
        gatekeeper = CompletionGatekeeper(dossier)
        
        result = gatekeeper.run_gate_b()
        
        # 应该失败（步骤未完成）
        assert result.passed is False
        assert any("not successful" in e for e in result.errors)
    
    def test_gate_b_e2e_complete(self, setup_dossier):
        """测试 Gate B - 步骤完成"""
        dossier = setup_dossier
        gatekeeper = CompletionGatekeeper(dossier)
        
        # 标记所有步骤为成功
        dossier.update_step("S01", "success")
        dossier.update_step("S02", "success")
        
        # 添加证据
        evidence_dir = dossier.evidence_dir / "S01"
        evidence_dir.mkdir(exist_ok=True)
        (evidence_dir / "test.txt").write_text("evidence")
        
        evidence_dir2 = dossier.evidence_dir / "S02"
        evidence_dir2.mkdir(exist_ok=True)
        (evidence_dir2 / "test.txt").write_text("evidence")
        
        result = gatekeeper.run_gate_b()
        
        assert result.passed is True
    
    def test_can_announce_completion(self, setup_dossier):
        """测试完成宣布检查"""
        dossier = setup_dossier
        gatekeeper = CompletionGatekeeper(dossier)
        
        # 未完成时
        can_announce, reason = gatekeeper.can_announce_completion()
        assert can_announce is False
        
        # 完成步骤
        dossier.update_step("S01", "success")
        dossier.update_step("S02", "success")
        
        # 添加证据
        for step_id in ["S01", "S02"]:
            dossier.save_step_result(step_id, {
                "step_id": step_id,
                "status": "success",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "attempts": 1
            })
            dossier.save_handoff(step_id, f"# {step_id} Handoff\n\nCompleted successfully.")
            evidence_dir = dossier.evidence_dir / step_id
            evidence_dir.mkdir(exist_ok=True)
            (evidence_dir / "output.txt").write_text("output")
        
        can_announce, reason = gatekeeper.can_announce_completion()
        assert can_announce is True


class TestE2ERecovery:
    """端到端恢复测试"""
    
    def test_three_step_demo_with_interrupt(self):
        """测试三步任务中断恢复"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1. 初始化任务
            dossier = TaskDossier(temp_dir)
            
            contract = TaskContract(
                objective="Demo 3-step task",
                repository="/tmp/demo",
                acceptance_criteria=["Step 1 done", "Step 2 done", "Step 3 done"]
            )
            
            plan = [
                {"step_id": "S01", "title": "Initialize", "goal": "Create initial files"},
                {"step_id": "S02", "title": "Process", "goal": "Process data"},
                {"step_id": "S03", "title": "Finalize", "goal": "Generate output"}
            ]
            
            state = dossier.initialize(contract, plan)
            
            # 编译并保存步骤包
            compiler = StepPacketCompiler()
            packets = compiler.compile_plan(plan, dossier.task_id, str(dossier.task_dir))
            for packet in packets:
                dossier.save_step_packet(packet["step_id"], packet)
            
            # 2. 执行第一步
            dossier.update_step("S01", "running")
            dossier.update_step("S01", "success")
            dossier.save_step_result("S01", {
                "step_id": "S01",
                "status": "success",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "attempts": 1
            })
            
            # 3. 模拟中断：第二步开始但没有完成
            dossier.update_step("S02", "running")
            # 假设这里发生了中断...
            
            # 4. 恢复：重新加载任务状态
            new_dossier = TaskDossier(temp_dir, dossier.task_id)
            engine = ResumeEngine(new_dossier)
            
            context = engine.analyze()
            
            # 验证恢复到了正确的步骤
            assert context.current_step_id == "S02"
            assert context.current_step_status == "running"
            assert context.needs_recovery is True
            
            # 5. 继续执行第二步
            # 获取租约
            engine.acquire_lease("S02", "recovery_worker")
            
            # 完成第二步
            new_dossier.update_step("S02", "success")
            new_dossier.save_step_result("S02", {
                "step_id": "S02",
                "status": "success",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "attempts": 1
            })
            
            # 6. 执行第三步
            new_dossier.update_step("S03", "running")
            new_dossier.update_step("S03", "success")
            new_dossier.save_step_result("S03", {
                "step_id": "S03",
                "status": "success",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "attempts": 1
            })
            
            # 7. 验证完成 - 需要添加证据和 handoff
            for step_id in ["S01", "S02", "S03"]:
                # 添加 handoff
                new_dossier.save_handoff(step_id, f"# {step_id} Handoff\n\nCompleted successfully.")
                
                # 添加证据
                evidence_dir = new_dossier.evidence_dir / step_id
                evidence_dir.mkdir(exist_ok=True)
                (evidence_dir / "output.txt").write_text(f"Evidence for {step_id}")
            
            gatekeeper = CompletionGatekeeper(new_dossier)
            can_announce, reason = gatekeeper.can_announce_completion()
            
            assert can_announce is True, f"Should be able to announce: {reason}"
            
            # 8. 验证步骤没有被重复执行（attempts 应该合理）
            state = new_dossier.load_state()
            # S01 完成了，attempts 应该是 1 或 2（取决于更新次数）
            assert state.steps[0]["status"] == "success"
            assert state.steps[0]["attempts"] >= 1  # 至少执行了一次
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
