"""
Cascade Policy for Checkpointed Step Loop v3-B

Handles cascade failure and cancellation policies.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum


class FailurePolicy(Enum):
    """Failure policy types."""
    BLOCK_PARENT = "block_parent"
    CONTINUE_WITH_WARNING = "continue_with_warning"
    CANCEL_CHILDREN = "cancel_children"


class CascadePolicy:
    """
    Evaluates and applies cascade policies.
    
    Determines:
    - Whether parent should be blocked
    - Whether warnings should be recorded
    - Whether children should be cancelled
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
    
    def evaluate_child_failure(
        self,
        parent_task_id: str,
        child_task_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate the impact of a child failure on the parent.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_id: ID of the failed child
            
        Returns:
            Evaluation result with recommended action
        """
        if not self.relationships:
            return {
                "action": "unknown",
                "reason": "No relationships manager"
            }
        
        # Get relationship
        relationship = self.relationships.get_relationship(parent_task_id, child_task_id)
        
        if not relationship:
            return {
                "action": "unknown",
                "reason": "Relationship not found"
            }
        
        relation_type = relationship.get("relation_type")
        failure_policy = relationship.get("failure_policy")
        
        # Evaluate based on policy
        if failure_policy == FailurePolicy.BLOCK_PARENT.value:
            if relation_type == "required":
                return {
                    "action": "block_parent",
                    "reason": f"Required child {child_task_id} failed with block_parent policy",
                    "child_task_id": child_task_id,
                    "policy": failure_policy
                }
            else:
                # Optional child with block_parent - still block but warn
                return {
                    "action": "block_parent",
                    "reason": f"Optional child {child_task_id} failed with block_parent policy",
                    "child_task_id": child_task_id,
                    "policy": failure_policy,
                    "note": "Policy was block_parent even though relation is optional"
                }
        
        elif failure_policy == FailurePolicy.CONTINUE_WITH_WARNING.value:
            return {
                "action": "continue_with_warning",
                "reason": f"Child {child_task_id} failed but parent can continue",
                "child_task_id": child_task_id,
                "policy": failure_policy,
                "warning": f"Child task {child_task_id} failed (relation_type: {relation_type})"
            }
        
        elif failure_policy == FailurePolicy.CANCEL_CHILDREN.value:
            # This policy is usually for parent->children cascade
            # but if set on child, it means parent should note and continue
            return {
                "action": "continue_with_warning",
                "reason": f"Child {child_task_id} failed with cancel_children policy",
                "child_task_id": child_task_id,
                "policy": failure_policy
            }
        
        return {
            "action": "unknown",
            "reason": f"Unknown failure policy: {failure_policy}"
        }
    
    def evaluate_parent_cancellation(
        self,
        parent_task_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate what should happen to children when parent is cancelled.
        
        Args:
            parent_task_id: ID of the cancelled parent
            
        Returns:
            Cancellation plan
        """
        if not self.relationships:
            return {
                "cancel_children": False,
                "reason": "No relationships manager"
            }
        
        pending_children = self.relationships.get_pending_children(parent_task_id)
        
        if not pending_children:
            return {
                "cancel_children": False,
                "reason": "No pending children to cancel"
            }
        
        return {
            "cancel_children": True,
            "children_to_cancel": [c["child_task_id"] for c in pending_children],
            "count": len(pending_children),
            "reason": "Parent cancelled, cascade to pending children"
        }
    
    def record_warning(
        self,
        parent_task_id: str,
        warning: str,
        child_task_id: Optional[str] = None
    ) -> None:
        """
        Record a warning in the parent's task state.
        
        Args:
            parent_task_id: ID of the parent task
            warning: Warning message
            child_task_id: Related child task ID (optional)
        """
        task_state_path = self.base_path / parent_task_id / "task_state.json"
        
        if not task_state_path.exists():
            return
        
        with open(task_state_path, 'r') as f:
            task_state = json.load(f)
        
        # Initialize warnings list if not exists
        if "warnings" not in task_state:
            task_state["warnings"] = []
        
        warning_record = {
            "message": warning,
            "timestamp": self._now()
        }
        
        if child_task_id:
            warning_record["child_task_id"] = child_task_id
        
        task_state["warnings"].append(warning_record)
        task_state["updated_at"] = self._now()
        
        with open(task_state_path, 'w') as f:
            json.dump(task_state, f, indent=2)
    
    def get_all_failure_actions(
        self,
        parent_task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get failure actions for all failed children.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            List of failure actions
        """
        if not self.relationships:
            return []
        
        failed_children = self.relationships.get_failed_children(parent_task_id)
        actions = []
        
        for child in failed_children:
            action = self.evaluate_child_failure(
                parent_task_id=parent_task_id,
                child_task_id=child["child_task_id"]
            )
            actions.append(action)
        
        return actions
    
    def should_block_parent(
        self,
        parent_task_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if parent should be blocked due to child failures.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            Tuple of (should_block, reason)
        """
        actions = self.get_all_failure_actions(parent_task_id)
        
        for action in actions:
            if action.get("action") == "block_parent":
                return True, action.get("reason")
        
        return False, None
    
    def get_warnings_to_record(
        self,
        parent_task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all warnings that should be recorded.
        
        Args:
            parent_task_id: ID of the parent task
            
        Returns:
            List of warnings to record
        """
        actions = self.get_all_failure_actions(parent_task_id)
        
        warnings = []
        for action in actions:
            if action.get("action") == "continue_with_warning":
                warnings.append({
                    "child_task_id": action.get("child_task_id"),
                    "warning": action.get("warning", action.get("reason"))
                })
        
        return warnings
