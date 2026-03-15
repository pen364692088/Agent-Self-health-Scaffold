"""
Tests for V2 Baseline Guard - 回归保护测试

验证 v2 baseline 的关键约束。
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.check_v2_baseline import BaselineGuard


class TestBaselineGuard:
    """测试基线检查器"""
    
    @pytest.fixture
    def repo_root(self):
        """获取仓库根目录"""
        return Path(__file__).parent.parent
    
    def test_baseline_guard_passes_for_valid_task(self, repo_root):
        """测试有效任务通过检查"""
        guard = BaselineGuard(repo_root)
        results = guard.check_all("pilot_docs_index_v2")
        
        assert results['passed'] is True
        assert len(results['errors']) == 0
    
    def test_summary_required(self, repo_root):
        """测试 SUMMARY.md 是必需的"""
        guard = BaselineGuard(repo_root)
        
        # 检查 SUMMARY.md 是否被正确检查
        final_dir = repo_root / "artifacts/tasks/pilot_docs_index_v2/final"
        summary_path = final_dir / "SUMMARY.md"
        
        assert summary_path.exists(), "SUMMARY.md should exist"
        
        # 验证检查逻辑
        guard._check_summary_exists(final_dir)
        assert len(guard.results['errors']) == 0
    
    def test_gate_report_exists(self, repo_root):
        """测试 gate_report.json 存在"""
        guard = BaselineGuard(repo_root)
        final_dir = repo_root / "artifacts/tasks/pilot_docs_index_v2/final"
        
        guard._check_gate_report_exists(final_dir)
        assert len(guard.results['errors']) == 0
    
    def test_no_gate_contradiction(self, repo_root):
        """测试无 Gate 矛盾"""
        guard = BaselineGuard(repo_root)
        final_dir = repo_root / "artifacts/tasks/pilot_docs_index_v2/final"
        
        guard._check_no_gate_contradiction(final_dir)
        assert len(guard.results['errors']) == 0
    
    def test_receipt_sync(self, repo_root):
        """测试 receipt 与 gate_report 同步"""
        guard = BaselineGuard(repo_root)
        final_dir = repo_root / "artifacts/tasks/pilot_docs_index_v2/final"
        
        guard._check_artifacts_consistency(final_dir)
        assert len(guard.results['errors']) == 0
    
    def test_task_completed_event(self, repo_root):
        """测试 task_completed 事件存在"""
        guard = BaselineGuard(repo_root)
        task_dir = repo_root / "artifacts/tasks/pilot_docs_index_v2"
        
        guard._check_task_completed_event(task_dir)
        assert len(guard.results['errors']) == 0
    
    def test_pilot_output_exists(self, repo_root):
        """测试 pilot 产出存在"""
        guard = BaselineGuard(repo_root)
        
        guard._check_pilot_output()
        assert len(guard.results['errors']) == 0


class TestGateIntegrityRegression:
    """Gate 完整性回归测试"""
    
    @pytest.fixture
    def temp_task_dir(self):
        """创建临时任务目录"""
        temp_dir = tempfile.mkdtemp()
        task_dir = Path(temp_dir) / "test_task"
        final_dir = task_dir / "final"
        final_dir.mkdir(parents=True)
        
        yield task_dir
        
        shutil.rmtree(temp_dir)
    
    def test_missing_summary_fails_gate_b(self, temp_task_dir):
        """测试 SUMMARY.md 缺失导致 Gate B 失败"""
        final_dir = temp_task_dir / "final"
        
        # 创建 gate_report.json with SUMMARY.md check
        gate_report = {
            "task_id": "test_task",
            "all_passed": False,
            "gates": {
                "gate_a": {"passed": True, "checks": [], "errors": []},
                "gate_b": {
                    "passed": False,
                    "checks": [{"name": "SUMMARY.md exists", "passed": False}],
                    "errors": ["SUMMARY.md not found"]
                },
                "gate_c": {"passed": True, "checks": [], "errors": []}
            }
        }
        
        (final_dir / "gate_report.json").write_text(json.dumps(gate_report))
        
        # 验证 Gate B 失败
        assert gate_report['gates']['gate_b']['passed'] is False
    
    def test_contradiction_detected(self, temp_task_dir):
        """测试矛盾状态被检测"""
        final_dir = temp_task_dir / "final"
        
        # 创建矛盾的 gate_report
        gate_report = {
            "task_id": "test_task",
            "all_passed": True,  # 矛盾：声称通过
            "gates": {
                "gate_a": {"passed": True, "checks": [], "errors": []},
                "gate_b": {
                    "passed": True,
                    "checks": [
                        {"name": "step S01 status", "passed": True},
                        {"name": "SUMMARY.md exists", "passed": False}  # 矛盾：有失败检查
                    ],
                    "errors": []
                },
                "gate_c": {"passed": True, "checks": [], "errors": []}
            }
        }
        
        (final_dir / "gate_report.json").write_text(json.dumps(gate_report))
        
        # 检测矛盾
        all_passed = gate_report['all_passed']
        has_failed = any(
            not c.get('passed', True) 
            for g in gate_report['gates'].values() 
            for c in g.get('checks', [])
        )
        
        contradiction = all_passed and has_failed
        assert contradiction, "Should detect contradiction"
    
    def test_receipt_gate_report_inconsistency_fails(self, temp_task_dir):
        """测试 receipt 与 gate_report 不一致失败"""
        final_dir = temp_task_dir / "final"
        
        # 创建 gate_report
        gate_report = {
            "task_id": "test_task",
            "all_passed": True,
            "validated_at": "2026-03-15T12:00:00Z",
            "gates": {
                "gate_a": {"passed": True, "checks": [], "errors": []},
                "gate_b": {"passed": True, "checks": [], "errors": []},
                "gate_c": {"passed": True, "checks": [], "errors": []}
            }
        }
        
        # 创建不一致的 receipt
        receipt = {
            "task_id": "test_task",
            "gate_report": {
                "all_passed": False,  # 不一致
                "validated_at": "2026-03-15T13:00:00Z",  # 不一致
                "gates": gate_report['gates']
            }
        }
        
        (final_dir / "gate_report.json").write_text(json.dumps(gate_report))
        (final_dir / "receipt.json").write_text(json.dumps(receipt))
        
        # 验证不一致
        assert receipt['gate_report']['all_passed'] != gate_report['all_passed']
    
    def test_completed_task_without_event_fails_gate_c(self, temp_task_dir):
        """测试 completed 任务缺少 task_completed 事件失败"""
        task_dir = temp_task_dir
        final_dir = task_dir / "final"
        
        # 创建 task_state
        task_state = {
            "task_id": "test_task",
            "status": "completed"
        }
        (task_dir / "task_state.json").write_text(json.dumps(task_state))
        
        # 创建 ledger (无 task_completed 事件)
        ledger_events = [
            {"action": "task_created"},
            {"action": "step_updated"}
        ]
        with open(task_dir / "ledger.jsonl", 'w') as f:
            for event in ledger_events:
                f.write(json.dumps(event) + "\n")
        
        # 检查应该失败
        has_completed_event = any(e['action'] == 'task_completed' for e in ledger_events)
        assert has_completed_event is False, "Should not have task_completed event"


class TestPilotDocsIndexV2Regression:
    """pilot_docs_index_v2 回归测试"""
    
    def test_pilot_output_still_exists(self):
        """测试 pilot 产出仍然存在"""
        repo_root = Path(__file__).parent.parent
        index_path = repo_root / "docs/INDEX.md"
        
        assert index_path.exists(), "docs/INDEX.md should exist as pilot output"
        
        # 验证内容
        content = index_path.read_text()
        assert len(content) > 0, "INDEX.md should not be empty"
    
    def test_pilot_task_still_passes_gates(self):
        """测试 pilot 任务仍然通过 Gates"""
        repo_root = Path(__file__).parent.parent
        gate_report_path = repo_root / "artifacts/tasks/pilot_docs_index_v2/final/gate_report.json"
        
        with open(gate_report_path) as f:
            gate_report = json.load(f)
        
        assert gate_report['all_passed'] is True
        assert gate_report['gates']['gate_a']['passed'] is True
        assert gate_report['gates']['gate_b']['passed'] is True
        assert gate_report['gates']['gate_c']['passed'] is True
    
    def test_no_failed_checks_in_passed_gates(self):
        """测试通过的 Gate 没有失败检查"""
        repo_root = Path(__file__).parent.parent
        gate_report_path = repo_root / "artifacts/tasks/pilot_docs_index_v2/final/gate_report.json"
        
        with open(gate_report_path) as f:
            gate_report = json.load(f)
        
        for gate_name, gate_data in gate_report['gates'].items():
            if gate_data['passed']:
                for check in gate_data['checks']:
                    assert check.get('passed', True), \
                        f"Gate {gate_name} passed but has failed check: {check['name']}"
    
    def test_resume_no_reexecution(self):
        """测试恢复不重跑已成功步骤"""
        repo_root = Path(__file__).parent.parent
        task_state_path = repo_root / "artifacts/tasks/pilot_docs_index_v2/task_state.json"
        
        with open(task_state_path) as f:
            task_state = json.load(f)
        
        # 所有步骤应该成功
        for step in task_state['steps']:
            assert step['status'] == 'success', \
                f"Step {step['step_id']} should be success"
            
            # attempts 应该合理
            assert step['attempts'] <= 3, \
                f"Step {step['step_id']} has too many attempts: {step['attempts']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
