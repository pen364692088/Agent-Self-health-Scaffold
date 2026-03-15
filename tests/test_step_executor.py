"""
Tests for Checkpointed Step Loop v2 - Real Execution
"""

import json
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.task_dossier import TaskDossier, TaskContract
from runtime.step_executor import StepExecutor, ExecutionResult, execute_step
from runtime.resume_execute_bridge import ResumeExecuteBridge


class TestStepExecutor:
    """测试步骤执行器"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(
            objective="Test execution",
            repository="/tmp/test"
        )
        
        plan = [
            {"step_id": "S01", "title": "Echo test", "goal": "Test shell execution"}
        ]
        
        dossier.initialize(contract, plan)
        
        # 保存步骤包
        dossier.save_step_packet("S01", {
            "step_id": "S01",
            "step_type": "execute_shell",
            "title": "Echo test",
            "goal": "Test shell execution",
            "execution": {
                "command": "echo 'Hello, World!'"
            }
        })
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_execute_shell_success(self, setup):
        """测试 shell 执行成功"""
        dossier = setup
        executor = StepExecutor(dossier)
        
        step_packet = dossier.get_step_packet("S01")
        result = executor.execute_step(step_packet)
        
        assert result.status == "success"
        assert result.exit_code == 0
        assert result.stdout_path is not None
        assert Path(result.stdout_path).exists()
        
        # 检查 stdout 内容
        stdout = Path(result.stdout_path).read_text()
        assert "Hello, World!" in stdout
    
    def test_execute_shell_failure(self, setup):
        """测试 shell 执行失败"""
        dossier = setup
        
        # 使用 exit 127 (command not found) 会返回 fatal
        dossier.save_step_packet("S01", {
            "step_id": "S01",
            "step_type": "execute_shell",
            "title": "Fail test",
            "goal": "Test failure",
            "execution": {
                "command": "nonexistent_command_xyz 2>/dev/null || exit 127"
            }
        })
        
        executor = StepExecutor(dossier)
        step_packet = dossier.get_step_packet("S01")
        result = executor.execute_step(step_packet)
        
        # exit_code != 0 表示执行有问题
        assert result.exit_code != 0
        assert result.status in ("failed", "fatal", "retryable")
    
    def test_execution_receipt_saved(self, setup):
        """测试执行收据保存"""
        dossier = setup
        executor = StepExecutor(dossier)
        
        step_packet = dossier.get_step_packet("S01")
        result = executor.execute_step(step_packet)
        
        # 检查收据文件
        receipt_path = dossier.steps_dir / "S01" / "execution_receipt.json"
        assert receipt_path.exists()
        
        with open(receipt_path) as f:
            receipt = json.load(f)
        
        assert receipt["step_id"] == "S01"
        assert receipt["status"] == "success"
        assert "checksum" in receipt
    
    def test_evidence_collection(self, setup):
        """测试证据收集"""
        dossier = setup
        executor = StepExecutor(dossier)
        
        step_packet = dossier.get_step_packet("S01")
        result = executor.execute_step(step_packet)
        evidence = executor.collect_evidence(step_packet, result)
        
        # 检查证据文件
        evidence_dir = dossier.evidence_dir / "S01"
        assert evidence_dir.exists()
        assert (evidence_dir / "stdout.txt").exists()
        assert (evidence_dir / "timing.json").exists()


class TestExecutionTypes:
    """测试不同执行类型"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(objective="Test", repository="/tmp/test")
        plan = [{"step_id": "S01", "title": "Test", "goal": "Test"}]
        dossier.initialize(contract, plan)
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_analyze_directory(self, setup):
        """测试目录分析"""
        dossier = setup
        
        # 创建测试目录
        test_dir = Path(tempfile.mkdtemp())
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        try:
            dossier.save_step_packet("S01", {
                "step_id": "S01",
                "step_type": "analyze",
                "title": "Analyze directory",
                "goal": "List directory contents",
                "execution": {
                    "target_path": str(test_dir)
                }
            })
            
            executor = StepExecutor(dossier)
            result = executor.execute_step(dossier.get_step_packet("S01"))
            
            assert result.status == "success"
            assert "result" in result.outputs
            assert result.outputs["result"]["type"] == "directory"
            assert result.outputs["result"]["file_count"] == 2
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_modify_files_create(self, setup):
        """测试文件创建"""
        dossier = setup
        temp_dir = tempfile.mkdtemp()
        
        try:
            dossier.save_step_packet("S01", {
                "step_id": "S01",
                "step_type": "modify_files",
                "title": "Create file",
                "goal": "Create a new file",
                "execution": {
                    "operations": [
                        {
                            "action": "create",
                            "path": str(Path(temp_dir) / "new_file.txt"),
                            "content": "Hello from executor"
                        }
                    ]
                }
            })
            
            executor = StepExecutor(dossier)
            result = executor.execute_step(dossier.get_step_packet("S01"))
            
            assert result.status == "success"
            assert len(result.changed_files) == 1
            assert len(result.generated_files) == 1
            
            # 验证文件实际创建
            created_file = Path(temp_dir) / "new_file.txt"
            assert created_file.exists()
            assert created_file.read_text() == "Hello from executor"
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_verify_outputs(self, setup):
        """测试输出验证"""
        dossier = setup
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 创建一个文件
            existing_file = Path(temp_dir) / "exists.txt"
            existing_file.write_text("content")
            
            dossier.save_step_packet("S01", {
                "step_id": "S01",
                "step_type": "verify_outputs",
                "title": "Verify files",
                "goal": "Check file existence",
                "execution": {
                    "expected_files": [
                        str(existing_file),
                        str(Path(temp_dir) / "missing.txt")
                    ]
                }
            })
            
            executor = StepExecutor(dossier)
            result = executor.execute_step(dossier.get_step_packet("S01"))
            
            assert result.status == "failed"  # 因为 missing.txt 不存在
            assert result.outputs["all_passed"] is False
            
        finally:
            shutil.rmtree(temp_dir)


class TestResumeExecuteBridge:
    """测试恢复执行桥接"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        temp_dir = tempfile.mkdtemp()
        dossier = TaskDossier(temp_dir)
        
        contract = TaskContract(
            objective="Test bridge",
            repository="/tmp/test"
        )
        
        plan = [
            {"step_id": "S01", "title": "Step 1", "goal": "First"},
            {"step_id": "S02", "title": "Step 2", "goal": "Second", "depends_on": ["S01"]}
        ]
        
        dossier.initialize(contract, plan)
        
        # 保存步骤包
        dossier.save_step_packet("S01", {
            "step_id": "S01",
            "step_type": "execute_shell",
            "title": "Step 1",
            "goal": "First step",
            "execution": {"command": "echo 'step1'"}
        })
        
        dossier.save_step_packet("S02", {
            "step_id": "S02",
            "step_type": "execute_shell",
            "title": "Step 2",
            "goal": "Second step",
            "execution": {"command": "echo 'step2'"},
            "depends_on": ["S01"]
        })
        
        yield dossier
        
        shutil.rmtree(temp_dir)
    
    def test_bridge_execute_first_step(self, setup):
        """测试桥接执行第一步"""
        dossier = setup
        bridge = ResumeExecuteBridge(dossier)
        
        result = bridge.bridge_and_execute()
        
        assert result["executed"] is True
        assert result["step_id"] == "S01"
        assert result["status"] == "success"
        
        # 验证状态更新
        state = dossier.load_state()
        assert state.steps[0]["status"] == "success"
    
    def test_bridge_execute_subsequent_steps(self, setup):
        """测试桥接执行后续步骤"""
        dossier = setup
        bridge = ResumeExecuteBridge(dossier)
        
        # 执行所有待处理步骤
        result = bridge.execute_all_pending()
        
        assert result["steps_executed"] == 2
        
        # 验证所有步骤完成
        state = dossier.load_state()
        assert all(s["status"] == "success" for s in state.steps)
    
    def test_bridge_no_reexecution(self, setup):
        """测试不会重复执行已成功的步骤"""
        dossier = setup
        bridge = ResumeExecuteBridge(dossier)
        
        # 执行第一步
        result1 = bridge.bridge_and_execute()
        assert result1["executed"] is True
        
        # 获取 attempts
        state1 = dossier.load_state()
        attempts_s01 = state1.steps[0]["attempts"]
        
        # 尝试再次执行
        result2 = bridge.bridge_and_execute()
        
        # 应该执行 S02，而不是重复 S01
        assert result2["step_id"] == "S02"
        
        # S01 的 attempts 不应该增加
        state2 = dossier.load_state()
        assert state2.steps[0]["attempts"] == attempts_s01


class TestE2ERealTask:
    """端到端真实任务测试"""
    
    def test_docs_index_generation(self):
        """测试文档索引生成任务"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 创建任务
            dossier = TaskDossier(temp_dir)
            
            # 创建一个真实的 docs 目录
            docs_dir = Path(tempfile.mkdtemp())
            (docs_dir / "README.md").write_text("# Project\n\nThis is a test project.")
            (docs_dir / "API.md").write_text("# API\n\nAPI documentation.")
            (docs_dir / "GUIDE.md").write_text("# Guide\n\nUser guide.")
            
            try:
                contract = TaskContract(
                    objective="Generate docs index",
                    repository=str(docs_dir),
                    acceptance_criteria=[
                        "Index file created",
                        "Index contains all doc files",
                        "Index formatted correctly"
                    ]
                )
                
                # 4步任务：分析 → 执行 → 验证 → 收口
                plan = [
                    {
                        "step_id": "S01",
                        "step_type": "analyze",
                        "title": "Analyze docs",
                        "goal": "List all documentation files"
                    },
                    {
                        "step_id": "S02",
                        "step_type": "modify_files",
                        "title": "Create index",
                        "goal": "Generate index markdown file"
                    },
                    {
                        "step_id": "S03",
                        "step_type": "verify_outputs",
                        "title": "Verify index",
                        "goal": "Check index file exists and is valid"
                    },
                    {
                        "step_id": "S04",
                        "step_type": "execute_shell",
                        "title": "Closeout",
                        "goal": "Finalize and report"
                    }
                ]
                
                dossier.initialize(contract, plan)
                
                # 保存步骤包
                dossier.save_step_packet("S01", {
                    "step_id": "S01",
                    "step_type": "analyze",
                    "title": "Analyze docs",
                    "goal": "List all documentation files",
                    "execution": {"target_path": str(docs_dir)}
                })
                
                # S02 将在执行时动态生成内容
                dossier.save_step_packet("S02", {
                    "step_id": "S02",
                    "step_type": "modify_files",
                    "title": "Create index",
                    "goal": "Generate index markdown file",
                    "execution": {
                        "operations": [
                            {
                                "action": "create",
                                "path": str(docs_dir / "INDEX.md"),
                                "content": "# Documentation Index\n\n- [README](README.md)\n- [API](API.md)\n- [GUIDE](GUIDE.md)\n"
                            }
                        ]
                    }
                })
                
                dossier.save_step_packet("S03", {
                    "step_id": "S03",
                    "step_type": "verify_outputs",
                    "title": "Verify index",
                    "goal": "Check index file exists",
                    "execution": {
                        "expected_files": [str(docs_dir / "INDEX.md")]
                    }
                })
                
                dossier.save_step_packet("S04", {
                    "step_id": "S04",
                    "step_type": "execute_shell",
                    "title": "Closeout",
                    "goal": "Finalize",
                    "execution": {"command": f"ls {docs_dir}"}
                })
                
                # 执行所有步骤
                bridge = ResumeExecuteBridge(dossier)
                result = bridge.execute_all_pending()
                
                # 验证
                assert result["steps_executed"] == 4
                
                state = dossier.load_state()
                assert all(s["status"] == "success" for s in state.steps)
                
                # 验证真实文件创建
                index_file = docs_dir / "INDEX.md"
                assert index_file.exists()
                assert "README" in index_file.read_text()
                
                # 验证证据存在
                for step_id in ["S01", "S02", "S03", "S04"]:
                    receipt_path = dossier.steps_dir / step_id / "execution_receipt.json"
                    assert receipt_path.exists(), f"Missing receipt for {step_id}"
                    
                # 验证 handoff 存在
                for step_id in ["S01", "S02", "S03", "S04"]:
                    handoff_path = dossier.handoff_dir / f"{step_id}.md"
                    assert handoff_path.exists(), f"Missing handoff for {step_id}"
                
            finally:
                shutil.rmtree(docs_dir)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
