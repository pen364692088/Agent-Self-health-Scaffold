"""
Parent-Child Orchestrator for Checkpointed Step Loop v3-B

Orchestrates parent-child task execution with state transitions
and result collection.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.task_relationships import TaskRelationships
from core.child_task_factory import ChildTaskFactory
from core.child_result_collector import ChildResultCollector


class ParentChildOrchestrator:
    """
    Orchestrates parent-child task workflows.
    
    Handles:
    - Child task creation and dispatch
    - Parent state transitions
    - Result collection
    - Failure handling
    """
    
    # Parent states
    STATE_PENDING = "pending"
    STATE_RUNNING = "running"
    STATE_WAITING_CHILDREN = "waiting_for_children"
    STATE_COLLECTING_CHILDREN = "collecting_children"
    STATE_BLOCKED_BY_CHILD = "blocked_by_child_failure"
    STATE_CHILDREN_FAILED = "children_failed"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"
    STATE_CANCELLED = "cancelled"
    
    def __init__(
        self,
        base_path: str = "artifacts/tasks"
    ):
        self.base_path = Path(base_path)
        self.relationships = TaskRelationships(base_path)
        self.factory = ChildTaskFactory(base_path, self.relationships)
        self.collector = ChildResultCollector(base_path, self.relationships)
    
    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def create_child(
        self,
        parent_task_id: str,
        child_task_name: str,
        steps: List[Dict[str, Any]],
        relation_type: str = "required",
        failure_policy: str = "block_parent",
        input_context: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a child task for a parent.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_name: Name for the child task
            steps: Step definitions
            relation_type: "required" or "optional"
            failure_policy: Failure policy
            input_context: Input data for child
            description: Child task description
            
        Returns:
            Creation result
        """
        return self.factory.create_child_task(
            parent_task_id=parent_task_id,
            child_task_name=child_task_name,
            steps=steps,
            relation_type=relation_type,
            failure_policy=failure_policy,
            input_context=input_context,
            description=description
        )
    
    def dispatch_child(self, child_task_id: str) -> bool:
        """Dispatch a child task for execution."""
        return self.factory.dispatch_child_task(child_task_id)
    
    def set_parent_waiting(self, parent_task_id: str) -> None:
        """Set parent task to waiting_for_children state."""
        self._update_parent_state(parent_task_id, self.STATE_WAITING_CHILDREN)
    
    def set_parent_collecting(self, parent_task_id: str) -> None:
        """Set parent task to collecting_children state."""
        self._update_parent_state(parent_task_id, self.STATE_COLLECTING_CHILDREN)
    
    def _update_parent_state(self, parent_task_id: str, new_state: str) -> None:
        """Update parent task state."""
        task_state_path = self.base_path / parent_task_id / "task_state.json"
        
        if not task_state_path.exists():
            return
        
        with open(task_state_path, 'r') as f:
            task_state = json.load(f)
        
        task_state["status"] = new_state
        task_state["updated_at"] = self._now()
        
        with open(task_state_path, 'w') as f:
            json.dump(task_state, f, indent=2)
    
    def check_children_progress(self, parent_task_id: str) -> Dict[str, Any]:
        """
        Check progress of all children.
        
        Returns:
            Progress summary
        """
        counts = self.relationships.count_children_by_status(parent_task_id)
        
        pending = counts["created"] + counts["dispatched"] + counts["running"]
        completed = counts["completed"] + counts["failed"] + counts["cancelled"]
        
        return {
            "parent_task_id": parent_task_id,
            "total_children": counts["total"],
            "pending": pending,
            "completed": completed,
            "counts": counts,
            "all_done": pending == 0,
            "has_failures": counts["failed"] > 0,
            "has_blocking_failure": self.relationships.has_blocking_failure(parent_task_id)
        }
    
    def process_child_completion(
        self,
        parent_task_id: str,
        child_task_id: str
    ) -> Dict[str, Any]:
        """
        Process completion of a child task.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_id: ID of the completed child
            
        Returns:
            Processing result with parent state recommendation
        """
        # Collect child result
        result = self.collector.collect_child_result(parent_task_id, child_task_id)
        
        if not result:
            return {
                "success": False,
                "error": "Failed to collect child result",
                "parent_state_recommendation": self.STATE_FAILED
            }
        
        # Check for blocking failures
        if self.relationships.has_blocking_failure(parent_task_id):
            return {
                "success": True,
                "child_result": result,
                "parent_state_recommendation": self.STATE_BLOCKED_BY_CHILD,
                "reason": "Required child failed with block_parent policy"
            }
        
        # Check if all children done
        progress = self.check_children_progress(parent_task_id)
        
        if progress["all_done"]:
            # All children completed, can proceed to collect
            return {
                "success": True,
                "child_result": result,
                "parent_state_recommendation": self.STATE_COLLECTING_CHILDREN,
                "all_children_done": True
            }
        else:
            # Still have pending children
            return {
                "success": True,
                "child_result": result,
                "parent_state_recommendation": self.STATE_WAITING_CHILDREN,
                "pending_children": progress["pending"]
            }
    
    def finalize_parent_children(self, parent_task_id: str) -> Dict[str, Any]:
        """
        Finalize child processing for parent.
        
        Collects all results and determines if parent can complete.
        
        Returns:
            Finalization result
        """
        # Collect all results
        collection_result = self.collector.collect_all_child_results(parent_task_id)
        
        # Check for blocking failures
        if self.relationships.has_blocking_failure(parent_task_id):
            self._update_parent_state(parent_task_id, self.STATE_BLOCKED_BY_CHILD)
            return {
                "success": False,
                "can_complete": False,
                "reason": "Blocking child failure detected",
                "collection_result": collection_result
            }
        
        # Check all required children completed
        if not self.relationships.all_required_children_completed(parent_task_id):
            return {
                "success": False,
                "can_complete": False,
                "reason": "Not all required children completed",
                "collection_result": collection_result
            }
        
        # All good, parent can proceed
        return {
            "success": True,
            "can_complete": True,
            "collection_result": collection_result
        }
    
    def cancel_all_children(self, parent_task_id: str) -> Dict[str, Any]:
        """
        Cancel all pending/running children of a parent.
        
        Used when parent is cancelled.
        
        Returns:
            Cancellation result
        """
        pending_children = self.relationships.get_pending_children(parent_task_id)
        cancelled = []
        errors = []
        
        for child in pending_children:
            child_task_id = child["child_task_id"]
            
            try:
                # Update child status
                self.relationships.update_relationship_status(
                    parent_task_id=parent_task_id,
                    child_task_id=child_task_id,
                    status="cancelled"
                )
                
                # Update child task state
                task_state_path = self.base_path / child_task_id / "task_state.json"
                if task_state_path.exists():
                    with open(task_state_path, 'r') as f:
                        task_state = json.load(f)
                    
                    task_state["status"] = "cancelled"
                    task_state["updated_at"] = self._now()
                    
                    with open(task_state_path, 'w') as f:
                        json.dump(task_state, f, indent=2)
                
                cancelled.append(child_task_id)
                
            except Exception as e:
                errors.append({
                    "child_task_id": child_task_id,
                    "error": str(e)
                })
        
        return {
            "parent_task_id": parent_task_id,
            "cancelled_count": len(cancelled),
            "cancelled": cancelled,
            "errors": errors
        }
    
    def get_parent_state_summary(self, parent_task_id: str) -> Dict[str, Any]:
        """Get comprehensive state summary for a parent task."""
        # Load parent state
        task_state_path = self.base_path / parent_task_id / "task_state.json"
        
        if task_state_path.exists():
            with open(task_state_path, 'r') as f:
                parent_state = json.load(f)
        else:
            parent_state = {"status": "unknown"}
        
        # Get children info
        children = self.relationships.get_all_children(parent_task_id)
        progress = self.check_children_progress(parent_task_id)
        
        # Get collected results
        collected_results = self.collector.get_collected_results(parent_task_id)
        
        return {
            "parent_task_id": parent_task_id,
            "parent_status": parent_state.get("status"),
            "children": {
                "total": len(children),
                "progress": progress,
                "list": children
            },
            "collected_results": collected_results,
            "has_blocking_failure": self.relationships.has_blocking_failure(parent_task_id),
            "all_required_completed": self.relationships.all_required_children_completed(parent_task_id)
        }
