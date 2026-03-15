"""
Task Relationships Manager for Checkpointed Step Loop v3-B

Manages parent-child task relationships with persistence.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid


class TaskRelationships:
    """
    Manages parent-child task relationships.
    
    All relationships are persisted to disk for recovery.
    """
    
    def __init__(self, base_path: str = "artifacts/tasks"):
        self.base_path = Path(base_path)
        
    def _get_relationships_path(self, parent_task_id: str) -> Path:
        """Get path to relationships file for a parent task."""
        return self.base_path / parent_task_id / "relationships.json"
    
    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def create_relationship(
        self,
        parent_task_id: str,
        child_task_id: str,
        relation_type: str = "required",
        failure_policy: str = "block_parent"
    ) -> Dict[str, Any]:
        """
        Create a new parent-child relationship.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_id: ID of the child task
            relation_type: "required" or "optional"
            failure_policy: "block_parent", "continue_with_warning", or "cancel_children"
            
        Returns:
            The created relationship record
        """
        relationship_id = f"rel_{uuid.uuid4().hex[:12]}"
        
        relationship = {
            "relationship_id": relationship_id,
            "parent_task_id": parent_task_id,
            "child_task_id": child_task_id,
            "relation_type": relation_type,
            "failure_policy": failure_policy,
            "status": "created",
            "created_at": self._now(),
            "updated_at": self._now(),
            "result_ref": None,
            "child_gate_result": None
        }
        
        # Load existing relationships
        relationships_path = self._get_relationships_path(parent_task_id)
        relationships_data = self._load_relationships(parent_task_id)
        
        # Add new relationship
        relationships_data["children"].append(relationship)
        relationships_data["updated_at"] = self._now()
        
        # Persist
        self._save_relationships(parent_task_id, relationships_data)
        
        return relationship
    
    def _load_relationships(self, parent_task_id: str) -> Dict[str, Any]:
        """Load relationships for a parent task."""
        relationships_path = self._get_relationships_path(parent_task_id)
        
        if relationships_path.exists():
            with open(relationships_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "parent_task_id": parent_task_id,
                "children": [],
                "created_at": self._now(),
                "updated_at": self._now()
            }
    
    def _save_relationships(self, parent_task_id: str, data: Dict[str, Any]) -> None:
        """Save relationships for a parent task."""
        relationships_path = self._get_relationships_path(parent_task_id)
        relationships_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(relationships_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_relationship(self, parent_task_id: str, child_task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific relationship."""
        relationships_data = self._load_relationships(parent_task_id)
        
        for child in relationships_data.get("children", []):
            if child["child_task_id"] == child_task_id:
                return child
        
        return None
    
    def get_all_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get all children for a parent task."""
        relationships_data = self._load_relationships(parent_task_id)
        return relationships_data.get("children", [])
    
    def get_required_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get all required children for a parent task."""
        children = self.get_all_children(parent_task_id)
        return [c for c in children if c["relation_type"] == "required"]
    
    def get_optional_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get all optional children for a parent task."""
        children = self.get_all_children(parent_task_id)
        return [c for c in children if c["relation_type"] == "optional"]
    
    def update_relationship_status(
        self,
        parent_task_id: str,
        child_task_id: str,
        status: str,
        result_ref: Optional[str] = None,
        gate_result: Optional[bool] = None
    ) -> bool:
        """
        Update the status of a relationship.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_id: ID of the child task
            status: New status (created, dispatched, running, completed, failed, cancelled)
            result_ref: Path to child's result summary (optional)
            gate_result: Result of child's gate check (optional)
            
        Returns:
            True if update successful, False otherwise
        """
        relationships_data = self._load_relationships(parent_task_id)
        
        for child in relationships_data.get("children", []):
            if child["child_task_id"] == child_task_id:
                child["status"] = status
                child["updated_at"] = self._now()
                
                if result_ref is not None:
                    child["result_ref"] = result_ref
                    
                if gate_result is not None:
                    child["child_gate_result"] = gate_result
                
                relationships_data["updated_at"] = self._now()
                self._save_relationships(parent_task_id, relationships_data)
                return True
        
        return False
    
    def get_pending_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get children that are not yet completed."""
        children = self.get_all_children(parent_task_id)
        return [c for c in children if c["status"] in ["created", "dispatched", "running"]]
    
    def get_completed_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get children that have completed (success, failed, or cancelled)."""
        children = self.get_all_children(parent_task_id)
        return [c for c in children if c["status"] in ["completed", "failed", "cancelled"]]
    
    def get_failed_children(self, parent_task_id: str) -> List[Dict[str, Any]]:
        """Get children that have failed."""
        children = self.get_all_children(parent_task_id)
        return [c for c in children if c["status"] == "failed"]
    
    def has_blocking_failure(self, parent_task_id: str) -> bool:
        """
        Check if any required child has failed with block_parent policy.
        
        Returns:
            True if there's a blocking failure, False otherwise
        """
        children = self.get_all_children(parent_task_id)
        
        for child in children:
            if (child["status"] == "failed" and 
                child["relation_type"] == "required" and 
                child["failure_policy"] == "block_parent"):
                return True
        
        return False
    
    def all_required_children_completed(self, parent_task_id: str) -> bool:
        """
        Check if all required children have completed.
        
        Returns:
            True if all required children are completed/failed/cancelled
        """
        required = self.get_required_children(parent_task_id)
        
        if not required:
            return True
            
        for child in required:
            if child["status"] not in ["completed", "failed", "cancelled"]:
                return False
        
        return True
    
    def count_children_by_status(self, parent_task_id: str) -> Dict[str, int]:
        """Count children by status."""
        children = self.get_all_children(parent_task_id)
        counts = {
            "total": len(children),
            "created": 0,
            "dispatched": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for child in children:
            status = child["status"]
            if status in counts:
                counts[status] += 1
        
        return counts
