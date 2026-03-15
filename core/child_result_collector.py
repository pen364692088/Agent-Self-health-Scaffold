"""
Child Result Collector for Checkpointed Step Loop v3-B

Collects and validates results from completed child tasks.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


class ChildResultCollector:
    """
    Collects results from child tasks for parent task processing.
    
    Ensures all required artifacts exist and are valid before
    returning results to the parent.
    """
    
    def __init__(
        self,
        base_path: str = "artifacts/tasks",
        relationships_manager=None
    ):
        self.base_path = Path(base_path)
        self.relationships = relationships_manager
    
    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def collect_child_result(
        self,
        parent_task_id: str,
        child_task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Collect the result from a completed child task.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_id: ID of the child task
            
        Returns:
            Dict with child result data, or None if collection fails
        """
        child_task_dir = self.base_path / child_task_id
        
        if not child_task_dir.exists():
            return None
        
        # Check for required artifacts
        summary_path = child_task_dir / "final" / "SUMMARY.md"
        gate_report_path = child_task_dir / "final" / "gate_report.json"
        receipt_path = child_task_dir / "final" / "receipt.json"
        task_state_path = child_task_dir / "task_state.json"
        
        # Load task state
        if not task_state_path.exists():
            return None
        
        with open(task_state_path, 'r') as f:
            task_state = json.load(f)
        
        child_status = task_state.get("status", "unknown")
        
        # Build result
        result = {
            "child_task_id": child_task_id,
            "parent_task_id": parent_task_id,
            "status": child_status,
            "artifacts": {
                "summary_path": str(summary_path) if summary_path.exists() else None,
                "gate_report_path": str(gate_report_path) if gate_report_path.exists() else None,
                "receipt_path": str(receipt_path) if receipt_path.exists() else None
            },
            "gate_passed": None,
            "failure_class": None,
            "failure_message": None,
            "collected_at": self._now()
        }
        
        # Check gate result
        if gate_report_path.exists():
            with open(gate_report_path, 'r') as f:
                gate_report = json.load(f)
            result["gate_passed"] = gate_report.get("all_passed", False)
        
        # Get failure info if failed
        if child_status == "failed":
            result["failure_class"] = task_state.get("failure_class", "execution_error")
            result["failure_message"] = task_state.get("failure_message", "Task failed")
        
        # Update relationship
        if self.relationships:
            self.relationships.update_relationship_status(
                parent_task_id=parent_task_id,
                child_task_id=child_task_id,
                status=child_status,
                result_ref=str(summary_path) if summary_path.exists() else None,
                gate_result=result["gate_passed"]
            )
        
        # Save to parent's child_results.json
        self._save_child_result(parent_task_id, result)
        
        return result
    
    def _save_child_result(self, parent_task_id: str, result: Dict[str, Any]) -> None:
        """Save child result to parent's child_results.json."""
        results_path = self.base_path / parent_task_id / "child_results.json"
        
        if results_path.exists():
            with open(results_path, 'r') as f:
                results_data = json.load(f)
        else:
            results_data = {
                "parent_task_id": parent_task_id,
                "collected_results": []
            }
        
        # Check if result already exists
        existing_idx = None
        for i, r in enumerate(results_data["collected_results"]):
            if r["child_task_id"] == result["child_task_id"]:
                existing_idx = i
                break
        
        if existing_idx is not None:
            results_data["collected_results"][existing_idx] = result
        else:
            results_data["collected_results"].append(result)
        
        with open(results_path, 'w') as f:
            json.dump(results_data, f, indent=2)
    
    def collect_all_child_results(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Collect results from all children of a parent task.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Dict with collection summary
        """
        if not self.relationships:
            return {
                "success": False,
                "error": "No relationships manager configured"
            }
        
        children = self.relationships.get_all_children(parent_task_id)
        results = []
        errors = []
        
        for child in children:
            child_task_id = child["child_task_id"]
            result = self.collect_child_result(parent_task_id, child_task_id)
            
            if result:
                results.append(result)
            else:
                errors.append({
                    "child_task_id": child_task_id,
                    "error": "Failed to collect result"
                })
        
        # Summary stats
        completed = sum(1 for r in results if r["status"] == "completed")
        failed = sum(1 for r in results if r["status"] == "failed")
        cancelled = sum(1 for r in results if r["status"] == "cancelled")
        gates_passed = sum(1 for r in results if r.get("gate_passed") == True)
        
        return {
            "success": len(errors) == 0,
            "parent_task_id": parent_task_id,
            "total_children": len(children),
            "results": results,
            "errors": errors,
            "summary": {
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
                "gates_passed": gates_passed
            }
        }
    
    def get_collected_results(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get all previously collected results for a parent task."""
        results_path = self.base_path / parent_task_id / "child_results.json"
        
        if not results_path.exists():
            return []
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        return data.get("collected_results", [])
    
    def validate_child_artifacts(
        self,
        child_task_id: str
    ) -> Dict[str, Any]:
        """
        Validate that all required child artifacts exist.
        
        Args:
            child_task_id: ID of the child task
            
        Returns:
            Validation result
        """
        child_task_dir = self.base_path / child_task_id / "final"
        
        checks = []
        all_passed = True
        
        # Check SUMMARY.md
        summary_path = child_task_dir / "SUMMARY.md"
        summary_exists = summary_path.exists()
        checks.append({
            "check": "summary_exists",
            "passed": summary_exists,
            "path": str(summary_path)
        })
        if not summary_exists:
            all_passed = False
        
        # Check gate_report.json
        gate_path = child_task_dir / "gate_report.json"
        gate_exists = gate_path.exists()
        checks.append({
            "check": "gate_report_exists",
            "passed": gate_exists,
            "path": str(gate_path)
        })
        if not gate_exists:
            all_passed = False
        
        # Check receipt.json
        receipt_path = child_task_dir / "receipt.json"
        receipt_exists = receipt_path.exists()
        checks.append({
            "check": "receipt_exists",
            "passed": receipt_exists,
            "path": str(receipt_path)
        })
        if not receipt_exists:
            all_passed = False
        
        return {
            "child_task_id": child_task_id,
            "all_passed": all_passed,
            "checks": checks
        }
    
    def get_required_child_results(
        self,
        parent_task_id: str
    ) -> List[Dict[str, Any]]:
        """Get results for all required children."""
        if not self.relationships:
            return []
        
        required_children = self.relationships.get_required_children(parent_task_id)
        results = self.get_collected_results(parent_task_id)
        
        required_ids = {c["child_task_id"] for c in required_children}
        return [r for r in results if r["child_task_id"] in required_ids]
    
    def all_required_results_collected(
        self,
        parent_task_id: str
    ) -> bool:
        """Check if all required children have collected results."""
        if not self.relationships:
            return True
        
        required_children = self.relationships.get_required_children(parent_task_id)
        collected_results = self.get_collected_results(parent_task_id)
        
        collected_ids = {r["child_task_id"] for r in collected_results}
        required_ids = {c["child_task_id"] for c in required_children}
        
        return required_ids.issubset(collected_ids)
