"""
State Consistency Checker - 状态一致性检查器

验证 task_state、ledger、artifacts 之间的一致性
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class ConsistencyReport:
    """一致性报告"""
    is_consistent: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "checks": self.checks,
            "issues": self.issues,
            "warnings": self.warnings
        }


class StateConsistencyChecker:
    """状态一致性检查器"""
    
    def __init__(self, task_dossier):
        self.dossier = task_dossier
    
    def check_all(self) -> ConsistencyReport:
        """执行所有一致性检查"""
        report = ConsistencyReport(is_consistent=True)
        
        # 1. 检查 task_state 存在性
        self._check_task_state_exists(report)
        
        # 2. 检查 ledger 存在性
        self._check_ledger_exists(report)
        
        # 3. 检查状态与 ledger 一致性
        self._check_state_ledger_consistency(report)
        
        # 4. 检查步骤文件完整性
        self._check_step_files_integrity(report)
        
        # 5. 检查证据完整性
        self._check_evidence_integrity(report)
        
        # 6. 检查 handoff 完整性
        self._check_handoff_integrity(report)
        
        # 7. 检查最终状态一致性
        self._check_final_state_consistency(report)
        
        report.is_consistent = len(report.issues) == 0
        return report
    
    def _check_task_state_exists(self, report: ConsistencyReport) -> None:
        """检查 task_state 文件存在"""
        if self.dossier.state_file.exists():
            try:
                with open(self.dossier.state_file) as f:
                    state = json.load(f)
                report.checks.append({
                    "name": "task_state exists and parseable",
                    "passed": True,
                    "details": f"task_id: {state.get('task_id')}"
                })
            except Exception as e:
                report.issues.append(f"Cannot parse task_state.json: {e}")
                report.checks.append({"name": "task_state exists and parseable", "passed": False})
        else:
            report.issues.append("task_state.json not found")
            report.checks.append({"name": "task_state exists and parseable", "passed": False})
    
    def _check_ledger_exists(self, report: ConsistencyReport) -> None:
        """检查 ledger 文件存在"""
        if self.dossier.ledger_file.exists():
            try:
                events = self.dossier.get_ledger_events()
                report.checks.append({
                    "name": "ledger exists and parseable",
                    "passed": True,
                    "details": f"{len(events)} events"
                })
            except Exception as e:
                report.issues.append(f"Cannot read ledger: {e}")
                report.checks.append({"name": "ledger exists and parseable", "passed": False})
        else:
            report.warnings.append("ledger.jsonl not found")
            report.checks.append({"name": "ledger exists and parseable", "passed": False})
    
    def _check_state_ledger_consistency(self, report: ConsistencyReport) -> None:
        """检查状态与 ledger 一致性"""
        state = self.dossier.load_state()
        if state is None:
            return
        
        events = self.dossier.get_ledger_events()
        
        # 检查步骤状态
        for step in state.steps:
            step_id = step["step_id"]
            step_status = step["status"]
            
            # 查找对应的 ledger 事件
            step_events = [e for e in events if e.get("data", {}).get("step_id") == step_id]
            
            if step_status == "success":
                # 应该有 step_updated 事件记录成功
                success_events = [e for e in step_events if e.get("data", {}).get("status") == "success"]
                if not success_events:
                    report.issues.append(f"Step {step_id} marked success but no success event in ledger")
                    report.checks.append({
                        "name": f"step {step_id} ledger consistency",
                        "passed": False
                    })
                else:
                    report.checks.append({
                        "name": f"step {step_id} ledger consistency",
                        "passed": True
                    })
    
    def _check_step_files_integrity(self, report: ConsistencyReport) -> None:
        """检查步骤文件完整性"""
        state = self.dossier.load_state()
        if state is None:
            return
        
        for step in state.steps:
            step_id = step["step_id"]
            step_dir = self.dossier.steps_dir / step_id
            
            # 检查步骤目录存在
            if not step_dir.exists():
                report.issues.append(f"Step directory missing: {step_id}")
                report.checks.append({"name": f"step dir {step_id}", "passed": False})
                continue
            
            # 检查 step_packet.json
            packet_file = step_dir / "step_packet.json"
            if not packet_file.exists():
                report.warnings.append(f"Step packet missing for {step_id}")
            
            # 如果步骤成功，检查 result.json
            if step["status"] == "success":
                result_file = step_dir / "result.json"
                if not result_file.exists():
                    report.issues.append(f"Result missing for successful step {step_id}")
                    report.checks.append({"name": f"result {step_id}", "passed": False})
                else:
                    report.checks.append({"name": f"result {step_id}", "passed": True})
    
    def _check_evidence_integrity(self, report: ConsistencyReport) -> None:
        """检查证据完整性"""
        state = self.dossier.load_state()
        if state is None:
            return
        
        for step in state.steps:
            if step["status"] == "success":
                step_id = step["step_id"]
                evidence_dir = self.dossier.evidence_dir / step_id
                
                if not evidence_dir.exists() or not any(evidence_dir.iterdir() if evidence_dir.exists() else []):
                    report.issues.append(f"Successful step {step_id} has no evidence")
                    report.checks.append({"name": f"evidence {step_id}", "passed": False})
                else:
                    file_count = len(list(evidence_dir.iterdir())) if evidence_dir.exists() else 0
                    report.checks.append({
                        "name": f"evidence {step_id}",
                        "passed": True,
                        "details": f"{file_count} files"
                    })
    
    def _check_handoff_integrity(self, report: ConsistencyReport) -> None:
        """检查 handoff 完整性"""
        state = self.dossier.load_state()
        if state is None:
            return
        
        for step in state.steps:
            if step["status"] == "success":
                step_id = step["step_id"]
                handoff_file = self.dossier.handoff_dir / f"{step_id}.md"
                
                if not handoff_file.exists():
                    report.warnings.append(f"Successful step {step_id} has no handoff")
                    report.checks.append({"name": f"handoff {step_id}", "passed": False})
                else:
                    report.checks.append({"name": f"handoff {step_id}", "passed": True})
    
    def _check_final_state_consistency(self, report: ConsistencyReport) -> None:
        """检查最终状态一致性"""
        state = self.dossier.load_state()
        if state is None:
            return
        
        # 如果状态是 completed，检查所有步骤都是 success
        if state.status == "completed":
            all_success = all(s["status"] == "success" for s in state.steps)
            if not all_success:
                report.issues.append("Task marked completed but not all steps are successful")
                report.checks.append({"name": "final state consistency", "passed": False})
            else:
                report.checks.append({"name": "final state consistency", "passed": True})
        
        # 如果有步骤是 failed，检查任务状态不是 completed
        has_failed = any(s["status"].startswith("failed") for s in state.steps)
        if has_failed and state.status == "completed":
            report.issues.append("Task marked completed but has failed steps")
            report.checks.append({"name": "failed step check", "passed": False})


def check_task_consistency(task_dossier) -> ConsistencyReport:
    """便捷函数：检查任务一致性"""
    checker = StateConsistencyChecker(task_dossier)
    return checker.check_all()
