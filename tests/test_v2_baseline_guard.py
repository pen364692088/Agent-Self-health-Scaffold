"""
test_v2_baseline_guard.py - V2 Baseline 回归保护测试

这些测试确保 v2 baseline 的关键约束不被破坏。
任何破坏这些约束的改动都将被视为 Breaking Change。
"""

import json
import pytest
from pathlib import Path


# Repository root
REPO_ROOT = Path(__file__).parent.parent
TASK_DIR = REPO_ROOT / "artifacts" / "tasks" / "pilot_docs_index_v2"
FINAL_DIR = TASK_DIR / "final"


class TestBaselineArtifacts:
    """测试基线产物存在性"""

    def test_summary_exists(self):
        """SUMMARY.md 必须存在"""
        summary_path = FINAL_DIR / "SUMMARY.md"
        assert summary_path.exists(), f"SUMMARY.md missing: {summary_path}"

    def test_gate_report_exists(self):
        """gate_report.json 必须存在"""
        gate_report_path = FINAL_DIR / "gate_report.json"
        assert gate_report_path.exists(), f"gate_report.json missing: {gate_report_path}"

    def test_receipt_exists(self):
        """receipt.json 必须存在"""
        receipt_path = FINAL_DIR / "receipt.json"
        assert receipt_path.exists(), f"receipt.json missing: {receipt_path}"

    def test_task_state_exists(self):
        """task_state.json 必须存在"""
        task_state_path = TASK_DIR / "task_state.json"
        assert task_state_path.exists(), f"task_state.json missing: {task_state_path}"

    def test_ledger_exists(self):
        """ledger.jsonl 必须存在"""
        ledger_path = TASK_DIR / "ledger.jsonl"
        assert ledger_path.exists(), f"ledger.jsonl missing: {ledger_path}"


class TestGateConsistency:
    """测试 Gate 一致性"""

    @pytest.fixture
    def gate_report(self):
        """加载 gate_report.json"""
        gate_report_path = FINAL_DIR / "gate_report.json"
        with open(gate_report_path) as f:
            return json.load(f)

    @pytest.fixture
    def receipt(self):
        """加载 receipt.json"""
        receipt_path = FINAL_DIR / "receipt.json"
        with open(receipt_path) as f:
            return json.load(f)

    def test_all_passed_is_true(self, gate_report):
        """gate_report.all_passed 必须为 true"""
        assert gate_report.get("all_passed") is True, \
            "all_passed should be true for accepted baseline"

    def test_no_gate_contradiction(self, gate_report):
        """如果 all_passed=true，则不应有 failed checks"""
        all_passed = gate_report.get("all_passed", False)
        gates = gate_report.get("gates", {})

        failed_checks = []
        for gate_name, gate_data in gates.items():
            for check in gate_data.get("checks", []):
                if not check.get("passed", True):
                    failed_checks.append(f"{gate_name}: {check.get('name')}")

        if all_passed:
            assert len(failed_checks) == 0, \
                f"Gate contradiction: all_passed=true but {len(failed_checks)} checks failed: {failed_checks}"

    def test_receipt_gate_report_sync(self, gate_report, receipt):
        """receipt 中的 gate_report 必须与 gate_report.json 同步"""
        receipt_gate = receipt.get("gate_report", {})

        assert receipt_gate.get("all_passed") == gate_report.get("all_passed"), \
            "all_passed mismatch between receipt and gate_report"

        for gate_name in ["gate_a", "gate_b", "gate_c"]:
            receipt_passed = receipt_gate.get("gates", {}).get(gate_name, {}).get("passed")
            gate_passed = gate_report.get("gates", {}).get(gate_name, {}).get("passed")
            assert receipt_passed == gate_passed, \
                f"{gate_name}.passed mismatch: receipt={receipt_passed}, gate_report={gate_passed}"


class TestTaskStateConsistency:
    """测试任务状态一致性"""

    @pytest.fixture
    def task_state(self):
        """加载 task_state.json"""
        task_state_path = TASK_DIR / "task_state.json"
        with open(task_state_path) as f:
            return json.load(f)

    def test_status_is_completed(self, task_state):
        """任务状态必须是 completed"""
        assert task_state.get("status") == "completed", \
            f"Expected status=completed, got {task_state.get('status')}"

    def test_all_steps_success(self, task_state):
        """所有步骤必须成功"""
        steps = task_state.get("steps", [])
        failed_steps = [s for s in steps if s.get("status") != "success"]

        assert len(failed_steps) == 0, \
            f"Found {len(failed_steps)} non-success steps: {[s.get('step_id') for s in failed_steps]}"

    def test_no_excessive_attempts(self, task_state):
        """成功步骤不应有过多的重试"""
        steps = task_state.get("steps", [])

        for step in steps:
            if step.get("status") == "success":
                attempts = step.get("attempts", 1)
                assert attempts <= 3, \
                    f"{step.get('step_id')}: {attempts} attempts suggests re-execution bug"


class TestLedgerConsistency:
    """测试 Ledger 一致性"""

    def test_task_completed_event_exists(self):
        """ledger 必须包含 task_completed 事件"""
        ledger_path = TASK_DIR / "ledger.jsonl"

        events = []
        with open(ledger_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        completed_events = [e for e in events if e.get("action") == "task_completed"]

        assert len(completed_events) > 0, \
            "No task_completed event found in ledger"


class TestPilotOutput:
    """测试 Pilot 产出"""

    def test_index_md_exists(self):
        """docs/INDEX.md 必须存在"""
        index_path = REPO_ROOT / "docs" / "INDEX.md"
        assert index_path.exists(), f"Pilot output missing: {index_path}"

    def test_index_md_has_content(self):
        """docs/INDEX.md 必须有实际内容"""
        index_path = REPO_ROOT / "docs" / "INDEX.md"
        content = index_path.read_text().strip()

        assert len(content) >= 500, \
            f"INDEX.md too short ({len(content)} chars), expected substantial content"


class TestBaselineDocuments:
    """测试基线文档存在性"""

    def test_baseline_accepted_doc_exists(self):
        """BASELINE_V2_ACCEPTED.md 必须存在"""
        doc_path = REPO_ROOT / "docs" / "BASELINE_V2_ACCEPTED.md"
        assert doc_path.exists(), f"Baseline document missing: {doc_path}"

    def test_baseline_lock_file_exists(self):
        """checkpointed_step_loop_v2.json 必须存在"""
        lock_path = REPO_ROOT / "artifacts" / "baselines" / "checkpointed_step_loop_v2.json"
        assert lock_path.exists(), f"Baseline lock file missing: {lock_path}"


class TestNoReexecution:
    """测试防重跑能力"""

    def test_step_packets_unique(self):
        """步骤包应该唯一（无重复）"""
        steps_dir = TASK_DIR / "steps"

        if not steps_dir.exists():
            pytest.skip("steps directory not found")

        step_packets = list(steps_dir.glob("*.json"))

        # 检查步骤 ID 唯一性
        step_ids = []
        for packet_path in step_packets:
            with open(packet_path) as f:
                packet = json.load(f)
                step_ids.append(packet.get("step_id"))

        assert len(step_ids) == len(set(step_ids)), \
            f"Duplicate step IDs found: {step_ids}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
