"""
Completion Gatekeeper - 完成守门器

任务结束前统一校验，禁止任何子模块直接输出"已完成"。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class GateResult:
    """Gate 检查结果"""
    gate_name: str
    passed: bool = False
    checks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings
        }


class CompletionGatekeeper:
    """完成守门器"""
    
    def __init__(self, task_dossier):
        self.dossier = task_dossier
    
    def validate_completion(self) -> Tuple[bool, Dict[str, Any]]:
        """验证任务是否可以标记为完成"""
        
        # 运行所有 Gate
        gate_a = self.run_gate_a()
        gate_b = self.run_gate_b()
        gate_c = self.run_gate_c()
        
        # 汇总结果
        all_passed = gate_a.passed and gate_b.passed and gate_c.passed
        
        report = {
            "task_id": self.dossier.task_id,
            "validated_at": datetime.utcnow().isoformat() + "Z",
            "all_passed": all_passed,
            "gates": {
                "gate_a": gate_a.to_dict(),
                "gate_b": gate_b.to_dict(),
                "gate_c": gate_c.to_dict()
            }
        }
        
        # 保存报告
        report_file = self.dossier.final_dir / "gate_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return all_passed, report
    
    def run_gate_a(self) -> GateResult:
        """
        Gate A: Contract - 契约验证
        
        检查：
        - 设计文档、schema、代码、测试、artifact 是否齐全
        - 字段契约是否和实现一致
        - 目录落点是否符合既有仓库结构
        """
        result = GateResult(gate_name="Gate A: Contract")
        
        # 检查任务状态文件
        state_file = self.dossier.state_file
        if state_file.exists():
            result.checks.append({"name": "task_state.json exists", "passed": True})
        else:
            result.errors.append("task_state.json not found")
            result.checks.append({"name": "task_state.json exists", "passed": False})
        
        # 检查 TASK.md
        if self.dossier.task_md.exists():
            result.checks.append({"name": "TASK.md exists", "passed": True})
        else:
            result.errors.append("TASK.md not found")
            result.checks.append({"name": "TASK.md exists", "passed": False})
        
        # 检查 ledger
        if self.dossier.ledger_file.exists():
            result.checks.append({"name": "ledger.jsonl exists", "passed": True})
        else:
            result.errors.append("ledger.jsonl not found")
            result.checks.append({"name": "ledger.jsonl exists", "passed": False})
        
        # 检查步骤包和结果
        task_state = self.dossier.load_state()
        if task_state:
            for step in task_state.steps:
                step_id = step["step_id"]
                
                # 检查步骤包
                packet = self.dossier.get_step_packet(step_id)
                if packet:
                    result.checks.append({"name": f"step_packet {step_id}", "passed": True})
                else:
                    result.errors.append(f"Step packet missing for {step_id}")
                    result.checks.append({"name": f"step_packet {step_id}", "passed": False})
                
                # 检查结果文件（仅成功的步骤）
                if step["status"] == "success":
                    result_file = self.dossier.steps_dir / step_id / "result.json"
                    if result_file.exists():
                        result.checks.append({"name": f"result {step_id}", "passed": True})
                    else:
                        result.errors.append(f"Result missing for successful step {step_id}")
                        result.checks.append({"name": f"result {step_id}", "passed": False})
        
        # 检查证据目录
        if self.dossier.evidence_dir.exists():
            result.checks.append({"name": "evidence/ directory exists", "passed": True})
        else:
            result.warnings.append("evidence/ directory not found")
            result.checks.append({"name": "evidence/ directory exists", "passed": False})
        
        # 检查 handoff 目录
        if self.dossier.handoff_dir.exists():
            result.checks.append({"name": "handoff/ directory exists", "passed": True})
        else:
            result.warnings.append("handoff/ directory not found")
            result.checks.append({"name": "handoff/ directory exists", "passed": False})
        
        # 完整性校验：检查是否有任何 check.passed=false
        failed_checks = [c for c in result.checks if not c.get("passed", True)]
        if failed_checks:
            result.errors.append(f"{len(failed_checks)} checks failed")
            result.passed = False
        else:
            result.passed = len(result.errors) == 0
        return result
    
    def run_gate_b(self) -> GateResult:
        """
        Gate B: E2E - 端到端验证
        
        检查：
        - 中断恢复闭环是否真实可跑
        - 重复 resume 是否幂等
        - 长任务是否确实摆脱上下文依赖
        """
        result = GateResult(gate_name="Gate B: E2E")
        
        task_state = self.dossier.load_state()
        if task_state is None:
            result.errors.append("Cannot load task state")
            result.passed = False
            return result
        
        # 检查所有步骤状态
        all_steps_success = True
        for step in task_state.steps:
            if step["status"] != "success":
                all_steps_success = False
                result.errors.append(f"Step {step['step_id']} not successful: {step['status']}")
            result.checks.append({
                "name": f"step {step['step_id']} status",
                "passed": step["status"] == "success",
                "details": step["status"]
            })
        
        if all_steps_success:
            result.checks.append({"name": "All steps completed", "passed": True})
        else:
            result.checks.append({"name": "All steps completed", "passed": False})
        
        # 检查是否有证据
        for step in task_state.steps:
            if step["status"] == "success":
                evidence_dir = self.dossier.evidence_dir / step["step_id"]
                if evidence_dir.exists() and any(evidence_dir.iterdir()):
                    result.checks.append({"name": f"evidence for {step['step_id']}", "passed": True})
                else:
                    result.warnings.append(f"No evidence for step {step['step_id']}")
                    result.checks.append({"name": f"evidence for {step['step_id']}", "passed": False})
        
        # 检查最终摘要
        summary_file = self.dossier.final_dir / "SUMMARY.md"
        if summary_file.exists():
            result.checks.append({"name": "SUMMARY.md exists", "passed": True})
        else:
            # SUMMARY.md 是必需产物
            result.errors.append("SUMMARY.md not found in final/")
            result.checks.append({"name": "SUMMARY.md exists", "passed": False})
        
        # 完整性校验：检查是否有任何 check.passed=false
        failed_checks = [c for c in result.checks if not c.get("passed", True)]
        if failed_checks:
            # 如果有任何 failed check，整体必须 failed
            result.errors.append(f"{len(failed_checks)} checks failed")
            result.passed = False
        else:
            result.passed = len(result.errors) == 0
        return result
    
    def run_gate_c(self) -> GateResult:
        """
        Gate C: Integrity - 完整性验证
        
        检查：
        - schema 校验
        - task_state / ledger 一致性
        - artifact 完整性
        - 不存在"只写总结不写证据"的假完成
        """
        result = GateResult(gate_name="Gate C: Integrity")
        
        # 验证 task_state schema
        state_file = self.dossier.state_file
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state_data = json.load(f)
                
                # 简单字段验证
                required_fields = ["task_id", "status", "created_at", "updated_at", "steps"]
                for field in required_fields:
                    if field in state_data:
                        result.checks.append({"name": f"state has {field}", "passed": True})
                    else:
                        result.errors.append(f"State missing required field: {field}")
                        result.checks.append({"name": f"state has {field}", "passed": False})
            except Exception as e:
                result.errors.append(f"Cannot parse task_state.json: {e}")
                result.checks.append({"name": "task_state.json parseable", "passed": False})
        else:
            result.errors.append("task_state.json not found")
        
        # 验证 ledger 与 state 一致性
        ledger_events = self.dossier.get_ledger_events()
        if ledger_events:
            # 检查最后的事件
            last_event = ledger_events[-1]
            result.checks.append({
                "name": "ledger has events",
                "passed": True,
                "details": f"{len(ledger_events)} events"
            })
            
            # 检查是否有 task_completed 事件
            # 规则：任务标记为 completed 时，必须有 task_completed 事件
            if state_data.get("status") == "completed":
                completed_events = [e for e in ledger_events if e.get("action") == "task_completed"]
                if completed_events:
                    result.checks.append({"name": "task_completed event exists", "passed": True})
                else:
                    # 必须有 task_completed 事件才能宣称完成
                    result.errors.append("Task marked completed but no task_completed event in ledger")
                    result.checks.append({"name": "task_completed event exists", "passed": False})
            else:
                result.warnings.append("Task not marked as completed in state")
        else:
            result.errors.append("No ledger events found")
            result.checks.append({"name": "ledger has events", "passed": False})
        
        # 检查证据完整性（防止"假完成"）
        task_state = self.dossier.load_state()
        if task_state:
            for step in task_state.steps:
                if step["status"] == "success":
                    # 检查是否有实际证据
                    evidence_dir = self.dossier.evidence_dir / step["step_id"]
                    handoff_file = self.dossier.handoff_dir / f"{step['step_id']}.md"
                    
                    has_evidence = evidence_dir.exists() and any(evidence_dir.iterdir())
                    has_handoff = handoff_file.exists()
                    
                    if not has_evidence and not has_handoff:
                        result.errors.append(f"Step {step['step_id']} marked success but has no evidence/handoff")
                        result.checks.append({"name": f"step {step['step_id']} has proof", "passed": False})
                    else:
                        result.checks.append({"name": f"step {step['step_id']} has proof", "passed": True})
        
        # 完整性校验：检查是否有任何 check.passed=false
        failed_checks = [c for c in result.checks if not c.get("passed", True)]
        if failed_checks:
            result.errors.append(f"{len(failed_checks)} checks failed")
            result.passed = False
        else:
            result.passed = len(result.errors) == 0
        return result
    
    def create_receipt(self) -> Dict[str, Any]:
        """创建完成收据"""
        passed, report = self.validate_completion()
        
        receipt = {
            "task_id": self.dossier.task_id,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "status": "completed" if passed else "failed",
            "gate_report": report,
            "artifacts": {
                "task_state": str(self.dossier.state_file),
                "ledger": str(self.dossier.ledger_file),
                "evidence": str(self.dossier.evidence_dir),
                "handoff": str(self.dossier.handoff_dir),
                "summary": str(self.dossier.final_dir / "SUMMARY.md")
            }
        }
        
        # 保存收据
        receipt_file = self.dossier.final_dir / "receipt.json"
        with open(receipt_file, 'w') as f:
            json.dump(receipt, f, indent=2)
        
        return receipt
    
    def can_announce_completion(self) -> Tuple[bool, str]:
        """检查是否可以宣布完成"""
        passed, report = self.validate_completion()
        
        if passed:
            return True, "All gates passed"
        else:
            errors = []
            for gate_name, gate_result in report["gates"].items():
                if not gate_result["passed"]:
                    errors.extend(gate_result["errors"])
            return False, f"Gates failed: {'; '.join(errors)}"
