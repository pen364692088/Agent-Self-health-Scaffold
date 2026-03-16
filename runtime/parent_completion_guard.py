"""
Parent Completion Guard for Checkpointed Step Loop v3-B

Enforces parent completion gate rules.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class ParentCompletionGuard:
    """
    Guards parent task completion.
    
    Ensures:
    1. All required children completed
    2. Required child artifacts exist
    3. Required child gates passed
    4. No blocking child failures
    5. All children accounted for
    """
    
    def __init__(
        self,
        base_path: str = "artifacts/tasks",
        relationships_manager=None,
        result_collector=None
    ):
        self.base_path = Path(base_path)
        self.relationships = relationships_manager
        self.collector = result_collector
    
    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def check_all_required_children_completed(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Check that all required children have completed.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Check result
        """
        if not self.relationships:
            return {
                "check": "all_required_children_completed",
                "passed": False,
                "reason": "No relationships manager"
            }
        
        required_children = self.relationships.get_required_children(parent_task_id)
        
        if not required_children:
            return {
                "check": "all_required_children_completed",
                "passed": True,
                "details": "No required children"
            }
        
        completed_count = 0
        pending = []
        
        for child in required_children:
            if child["status"] in ["completed", "failed", "cancelled"]:
                completed_count += 1
            else:
                pending.append(child["child_task_id"])
        
        all_completed = len(pending) == 0
        
        return {
            "check": "all_required_children_completed",
            "passed": all_completed,
            "total_required": len(required_children),
            "completed": completed_count,
            "pending": pending,
            "details": f"{completed_count}/{len(required_children)} required children completed"
        }
    
    def check_required_child_artifacts(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Check that all required child artifacts exist.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Check result
        """
        if not self.relationships:
            return {
                "check": "required_child_artifacts_exist",
                "passed": False,
                "reason": "No relationships manager"
            }
        
        required_children = self.relationships.get_required_children(parent_task_id)
        missing_artifacts = []
        
        for child in required_children:
            if child["status"] != "completed":
                continue  # Skip non-completed children
            
            child_task_id = child["child_task_id"]
            child_dir = self.base_path / child_task_id / "final"
            
            summary_path = child_dir / "SUMMARY.md"
            gate_path = child_dir / "gate_report.json"
            receipt_path = child_dir / "receipt.json"
            
            if not summary_path.exists():
                missing_artifacts.append({
                    "child_task_id": child_task_id,
                    "missing": "SUMMARY.md"
                })
            
            if not gate_path.exists():
                missing_artifacts.append({
                    "child_task_id": child_task_id,
                    "missing": "gate_report.json"
                })
            
            if not receipt_path.exists():
                missing_artifacts.append({
                    "child_task_id": child_task_id,
                    "missing": "receipt.json"
                })
        
        all_passed = len(missing_artifacts) == 0
        
        return {
            "check": "required_child_artifacts_exist",
            "passed": all_passed,
            "missing": missing_artifacts,
            "details": "All artifact paths verified" if all_passed else f"Missing {len(missing_artifacts)} artifacts"
        }
    
    def check_required_child_gates(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Check that all required child gates passed.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Check result
        """
        if not self.relationships:
            return {
                "check": "required_child_gates_passed",
                "passed": False,
                "reason": "No relationships manager"
            }
        
        required_children = self.relationships.get_required_children(parent_task_id)
        failed_gates = []
        
        for child in required_children:
            if child["status"] != "completed":
                continue  # Only check completed children
            
            child_task_id = child["child_task_id"]
            gate_path = self.base_path / child_task_id / "final" / "gate_report.json"
            
            if gate_path.exists():
                with open(gate_path, 'r') as f:
                    gate_report = json.load(f)
                
                if not gate_report.get("all_passed", False):
                    failed_gates.append({
                        "child_task_id": child_task_id,
                        "gate_passed": False
                    })
            else:
                failed_gates.append({
                    "child_task_id": child_task_id,
                    "gate_passed": False,
                    "reason": "gate_report.json not found"
                })
        
        all_passed = len(failed_gates) == 0
        
        return {
            "check": "required_child_gates_passed",
            "passed": all_passed,
            "failed_gates": failed_gates,
            "details": "All required child gates passed" if all_passed else f"{len(failed_gates)} child gates failed"
        }
    
    def check_no_blocking_failures(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Check that there are no blocking child failures.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Check result
        """
        if not self.relationships:
            return {
                "check": "no_blocking_child_failures",
                "passed": False,
                "reason": "No relationships manager"
            }
        
        has_blocking = self.relationships.has_blocking_failure(parent_task_id)
        
        if has_blocking:
            failed = self.relationships.get_failed_children(parent_task_id)
            blocking_failures = [
                c for c in failed
                if c["relation_type"] == "required" and c["failure_policy"] == "block_parent"
            ]
            
            return {
                "check": "no_blocking_child_failures",
                "passed": False,
                "blocking_failures": blocking_failures,
                "details": f"{len(blocking_failures)} blocking child failures"
            }
        
        return {
            "check": "no_blocking_child_failures",
            "passed": True,
            "details": "No required child failures with block_parent policy"
        }
    
    def check_no_orphaned_children(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Check that all children are tracked.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Check result
        """
        if not self.relationships:
            return {
                "check": "no_orphaned_children",
                "passed": False,
                "reason": "No relationships manager"
            }
        
        children = self.relationships.get_all_children(parent_task_id)
        
        # Check that all children have relationship_id and are tracked
        orphaned = []
        for child in children:
            if not child.get("relationship_id"):
                orphaned.append(child["child_task_id"])
        
        return {
            "check": "no_orphaned_children",
            "passed": len(orphaned) == 0,
            "orphaned": orphaned,
            "total_children": len(children),
            "details": "All children tracked" if not orphaned else f"{len(orphaned)} orphaned children"
        }
    
    def run_completion_gate(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Run all completion gate checks.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Complete gate report
        """
        checks = [
            self.check_all_required_children_completed(parent_task_id),
            self.check_required_child_artifacts(parent_task_id),
            self.check_required_child_gates(parent_task_id),
            self.check_no_blocking_failures(parent_task_id),
            self.check_no_orphaned_children(parent_task_id)
        ]
        
        all_passed = all(c["passed"] for c in checks)
        
        return {
            "gate": "parent_completion",
            "parent_task_id": parent_task_id,
            "checks": checks,
            "all_passed": all_passed,
            "timestamp": self._now()
        }
    
    def can_parent_complete(
        self,
        parent_task_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if parent can complete.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Tuple of (can_complete, reason)
        """
        gate_result = self.run_completion_gate(parent_task_id)
        
        if gate_result["all_passed"]:
            return True, None
        
        # Find first failed check
        for check in gate_result["checks"]:
            if not check["passed"]:
                return False, check.get("details", check["check"])
        
        return False, "Unknown gate failure"
    
    def generate_gate_report_file(
        self,
        parent_task_id: str
    ) -> str:
        """
        Generate and save gate report file.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Path to generated report
        """
        gate_result = self.run_completion_gate(parent_task_id)
        
        report_path = self.base_path / parent_task_id / "final" / "parent_gate_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(gate_result, f, indent=2)
        
        return str(report_path)


from typing import Tuple
