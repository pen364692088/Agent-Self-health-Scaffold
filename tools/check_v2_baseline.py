#!/usr/bin/env python3
"""
V2 Baseline Guard - Checkpointed Step Loop v2 回归保护检查器

检查 v2 baseline 的关键约束是否被破坏。
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any


class BaselineGuard:
    """v2 Baseline 回归检查器"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.baseline_file = repo_root / "artifacts/baselines/checkpointed_step_loop_v2.json"
        self.results = {
            "passed": True,
            "checks": [],
            "errors": [],
            "warnings": []
        }
    
    def check_all(self, task_id: str = "pilot_docs_index_v2") -> Dict[str, Any]:
        """执行所有回归检查"""
        
        task_dir = self.repo_root / "artifacts/tasks" / task_id
        final_dir = task_dir / "final"
        
        # 1. SUMMARY.md 存在
        self._check_summary_exists(final_dir)
        
        # 2. gate_report.json 存在
        self._check_gate_report_exists(final_dir)
        
        # 3. receipt.json 存在
        self._check_receipt_exists(final_dir)
        
        # 4. 三者一致
        self._check_artifacts_consistency(final_dir)
        
        # 5. 无 Gate 矛盾
        self._check_no_gate_contradiction(final_dir)
        
        # 6. task_completed 事件存在
        self._check_task_completed_event(task_dir)
        
        # 7. pilot 产出存在
        self._check_pilot_output()
        
        # 8. baseline lock 文件存在
        self._check_baseline_lock_exists()
        
        # 9. baseline 文档存在
        self._check_baseline_doc_exists()
        
        # 10. 已成功步骤不重跑 (检查 attempts)
        self._check_no_reexecution(task_dir)
        
        return self.results
    
    def _check_summary_exists(self, final_dir: Path) -> None:
        """检查 SUMMARY.md 存在"""
        summary_path = final_dir / "SUMMARY.md"
        
        if summary_path.exists():
            self._add_check("SUMMARY.md exists", True, str(summary_path))
        else:
            self._add_error("SUMMARY.md not found", f"Expected: {summary_path}")
    
    def _check_gate_report_exists(self, final_dir: Path) -> None:
        """检查 gate_report.json 存在"""
        gate_report_path = final_dir / "gate_report.json"
        
        if gate_report_path.exists():
            self._add_check("gate_report.json exists", True, str(gate_report_path))
        else:
            self._add_error("gate_report.json not found", f"Expected: {gate_report_path}")
    
    def _check_receipt_exists(self, final_dir: Path) -> None:
        """检查 receipt.json 存在"""
        receipt_path = final_dir / "receipt.json"
        
        if receipt_path.exists():
            self._add_check("receipt.json exists", True, str(receipt_path))
        else:
            self._add_error("receipt.json not found", f"Expected: {receipt_path}")
    
    def _check_artifacts_consistency(self, final_dir: Path) -> None:
        """检查三件套一致"""
        gate_report_path = final_dir / "gate_report.json"
        receipt_path = final_dir / "receipt.json"
        
        if not gate_report_path.exists() or not receipt_path.exists():
            return
        
        with open(gate_report_path) as f:
            gate_report = json.load(f)
        
        with open(receipt_path) as f:
            receipt = json.load(f)
        
        # 检查 all_passed 一致
        if receipt['gate_report']['all_passed'] != gate_report['all_passed']:
            self._add_error("all_passed mismatch", 
                f"receipt: {receipt['gate_report']['all_passed']}, gate_report: {gate_report['all_passed']}")
        else:
            self._add_check("all_passed consistent", True, str(gate_report['all_passed']))
        
        # 检查 gates passed 一致
        for gate_name in ['gate_a', 'gate_b', 'gate_c']:
            r_passed = receipt['gate_report']['gates'][gate_name]['passed']
            g_passed = gate_report['gates'][gate_name]['passed']
            
            if r_passed != g_passed:
                self._add_error(f"{gate_name}.passed mismatch",
                    f"receipt: {r_passed}, gate_report: {g_passed}")
            else:
                self._add_check(f"{gate_name}.passed consistent", True, str(r_passed))
    
    def _check_no_gate_contradiction(self, final_dir: Path) -> None:
        """检查无 Gate 矛盾"""
        gate_report_path = final_dir / "gate_report.json"
        
        if not gate_report_path.exists():
            return
        
        with open(gate_report_path) as f:
            gate_report = json.load(f)
        
        all_passed = gate_report['all_passed']
        
        # 检查是否有任何 failed check
        contradictions = []
        for gate_name, gate_data in gate_report['gates'].items():
            for check in gate_data['checks']:
                if not check.get('passed', True):
                    contradictions.append({
                        'gate': gate_name,
                        'check': check['name']
                    })
        
        if all_passed and contradictions:
            self._add_error("Gate contradiction", 
                f"all_passed=true but {len(contradictions)} checks failed")
            for c in contradictions:
                self._add_error(f"  Failed check", f"{c['gate']}: {c['check']}")
        elif not all_passed and not contradictions and not any(g['errors'] for g in gate_report['gates'].values()):
            self._add_warning("Unusual state", "all_passed=false but no failed checks or errors")
        else:
            self._add_check("No gate contradiction", True, f"all_passed={all_passed}, failed_checks={len(contradictions)}")
    
    def _check_task_completed_event(self, task_dir: Path) -> None:
        """检查 task_completed 事件存在"""
        ledger_path = task_dir / "ledger.jsonl"
        task_state_path = task_dir / "task_state.json"
        
        if not ledger_path.exists():
            self._add_warning("Ledger not found", str(ledger_path))
            return
        
        # 读取 task_state
        task_status = None
        if task_state_path.exists():
            with open(task_state_path) as f:
                task_state = json.load(f)
                task_status = task_state.get('status')
        
        # 检查 ledger 中是否有 task_completed 事件
        has_completed_event = False
        with open(ledger_path) as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event.get('action') == 'task_completed':
                        has_completed_event = True
                        break
        
        if task_status == 'completed':
            if has_completed_event:
                self._add_check("task_completed event exists", True, "Required for completed status")
            else:
                self._add_error("Missing task_completed event", 
                    "task_state.status=completed but no task_completed event in ledger")
        else:
            self._add_check("task_completed event check", True, f"task_status={task_status}")
    
    def _check_pilot_output(self) -> None:
        """检查 pilot 产出存在"""
        index_path = self.repo_root / "docs/INDEX.md"
        
        if index_path.exists():
            size = index_path.stat().st_size
            self._add_check("Pilot output exists", True, f"{index_path} ({size} bytes)")
        else:
            self._add_error("Pilot output missing", f"Expected: {index_path}")
    
    def _check_baseline_lock_exists(self) -> None:
        """检查 baseline lock 文件存在"""
        if self.baseline_file.exists():
            self._add_check("Baseline lock file exists", True, str(self.baseline_file))
        else:
            self._add_error("Baseline lock file missing", str(self.baseline_file))
    
    def _check_baseline_doc_exists(self) -> None:
        """检查 baseline 文档存在"""
        doc_path = self.repo_root / "docs/BASELINE_V2_ACCEPTED.md"
        
        if doc_path.exists():
            self._add_check("Baseline document exists", True, str(doc_path))
        else:
            self._add_error("Baseline document missing", str(doc_path))
    
    def _check_no_reexecution(self, task_dir: Path) -> None:
        """检查已成功步骤不重跑"""
        task_state_path = task_dir / "task_state.json"
        
        if not task_state_path.exists():
            return
        
        with open(task_state_path) as f:
            task_state = json.load(f)
        
        # 检查成功步骤的 attempts
        issues = []
        for step in task_state.get('steps', []):
            if step['status'] == 'success' and step.get('attempts', 0) > 2:
                issues.append(f"{step['step_id']}: {step['attempts']} attempts")
        
        if issues:
            self._add_warning("High attempt count", ", ".join(issues))
        else:
            success_steps = [s for s in task_state.get('steps', []) if s['status'] == 'success']
            self._add_check("No excessive reexecution", True, f"{len(success_steps)} successful steps")
    
    def _add_check(self, name: str, passed: bool, details: str = "") -> None:
        """添加检查结果"""
        self.results['checks'].append({
            'name': name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        })
    
    def _add_error(self, name: str, message: str) -> None:
        """添加错误"""
        self.results['errors'].append({'name': name, 'message': message})
        self.results['passed'] = False
        self._add_check(name, False, message)
    
    def _add_warning(self, name: str, message: str) -> None:
        """添加警告"""
        self.results['warnings'].append({'name': name, 'message': message})
        self._add_check(name, True, f"WARNING: {message}")


def main():
    parser = argparse.ArgumentParser(description="Check v2 baseline integrity")
    parser.add_argument("--task", default="pilot_docs_index_v2", help="Task ID to check")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    repo_root = Path(args.repo).resolve()
    guard = BaselineGuard(repo_root)
    
    results = guard.check_all(args.task)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 60)
        print("V2 Baseline Guard Check")
        print("=" * 60)
        print(f"\nTask: {args.task}")
        print(f"Repo: {repo_root}")
        print()
        
        print("Checks:")
        for check in results['checks']:
            status = "✅" if check['passed'] else "❌"
            print(f"  {status} {check['name']}: {check.get('details', '')}")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for err in results['errors']:
                print(f"  - {err['name']}: {err['message']}")
        
        if results['warnings']:
            print(f"\n⚠️ Warnings ({len(results['warnings'])}):")
            for warn in results['warnings']:
                print(f"  - {warn['name']}: {warn['message']}")
        
        print()
        print("=" * 60)
        if results['passed']:
            print("✅ ALL CHECKS PASSED - Baseline intact")
        else:
            print("❌ CHECKS FAILED - Baseline violation detected")
        print("=" * 60)
    
    sys.exit(0 if results['passed'] else 1)


if __name__ == "__main__":
    main()
