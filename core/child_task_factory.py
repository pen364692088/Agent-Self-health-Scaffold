"""
Child Task Factory for Checkpointed Step Loop v3-B

Creates and registers child tasks with proper boundaries and validation.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


class ChildTaskFactory:
    """
    Factory for creating child tasks within the v3-B orchestration.
    
    Child tasks use the same execution path as standalone tasks (v2 + v3-A).
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
    
    def create_child_task(
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
        Create a child task.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_name: Human-readable name for the child task
            steps: List of step definitions
            relation_type: "required" or "optional"
            failure_policy: "block_parent", "continue_with_warning", or "cancel_children"
            input_context: Context/data to pass to child task
            description: Description of what the child task does
            
        Returns:
            Dict containing child task ID and creation status
        """
        # Generate child task ID
        child_task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # Create child task directory
        child_task_dir = self.base_path / child_task_id
        child_task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create task state
        task_state = {
            "task_id": child_task_id,
            "task_name": child_task_name,
            "description": description,
            "parent_task_id": parent_task_id,
            "status": "pending",
            "created_at": self._now(),
            "updated_at": self._now(),
            "steps": {},
            "current_step": None,
            "attempts": {},
            "metadata": {
                "relation_type": relation_type,
                "failure_policy": failure_policy
            }
        }
        
        # Initialize step states
        for i, step in enumerate(steps):
            step_id = f"S{i+1:02d}"
            task_state["steps"][step_id] = {
                "step_id": step_id,
                "step_name": step.get("name", f"Step {i+1}"),
                "status": "pending",
                "attempts": 0
            }
        
        # Create step packet
        step_packet = {
            "task_id": child_task_id,
            "parent_task_id": parent_task_id,
            "steps": steps,
            "input_context": input_context or {},
            "created_at": self._now()
        }
        
        # Write files
        with open(child_task_dir / "task_state.json", 'w') as f:
            json.dump(task_state, f, indent=2)
        
        with open(child_task_dir / "step_packet.json", 'w') as f:
            json.dump(step_packet, f, indent=2)
        
        # Initialize ledger
        ledger_path = child_task_dir / "ledger.jsonl"
        with open(ledger_path, 'w') as f:
            event = {
                "event": "task_created",
                "task_id": child_task_id,
                "parent_task_id": parent_task_id,
                "timestamp": self._now(),
                "metadata": {
                    "relation_type": relation_type,
                    "failure_policy": failure_policy
                }
            }
            f.write(json.dumps(event) + "\n")
        
        # Register relationship
        if self.relationships:
            relationship = self.relationships.create_relationship(
                parent_task_id=parent_task_id,
                child_task_id=child_task_id,
                relation_type=relation_type,
                failure_policy=failure_policy
            )
        else:
            relationship = None
        
        return {
            "child_task_id": child_task_id,
            "parent_task_id": parent_task_id,
            "status": "created",
            "task_state_path": str(child_task_dir / "task_state.json"),
            "step_packet_path": str(child_task_dir / "step_packet.json"),
            "relationship": relationship
        }
    
    def dispatch_child_task(self, child_task_id: str) -> bool:
        """
        Mark a child task as dispatched (ready for execution).
        
        Args:
            child_task_id: ID of the child task
            
        Returns:
            True if dispatch successful
        """
        task_dir = self.base_path / child_task_id
        task_state_path = task_dir / "task_state.json"
        
        if not task_state_path.exists():
            return False
        
        with open(task_state_path, 'r') as f:
            task_state = json.load(f)
        
        task_state["status"] = "dispatched"
        task_state["updated_at"] = self._now()
        
        with open(task_state_path, 'w') as f:
            json.dump(task_state, f, indent=2)
        
        # Update relationship if parent exists
        parent_task_id = task_state.get("parent_task_id")
        if parent_task_id and self.relationships:
            self.relationships.update_relationship_status(
                parent_task_id=parent_task_id,
                child_task_id=child_task_id,
                status="dispatched"
            )
        
        # Record in ledger
        ledger_path = task_dir / "ledger.jsonl"
        with open(ledger_path, 'a') as f:
            event = {
                "event": "task_dispatched",
                "task_id": child_task_id,
                "timestamp": self._now()
            }
            f.write(json.dumps(event) + "\n")
        
        return True
    
    def get_child_task_state(self, child_task_id: str) -> Optional[Dict[str, Any]]:
        """Load the state of a child task."""
        task_state_path = self.base_path / child_task_id / "task_state.json"
        
        if not task_state_path.exists():
            return None
        
        with open(task_state_path, 'r') as f:
            return json.load(f)
    
    def create_simple_child_task(
        self,
        parent_task_id: str,
        child_task_name: str,
        description: str,
        execution_steps: List[str],
        relation_type: str = "required",
        failure_policy: str = "block_parent"
    ) -> Dict[str, Any]:
        """
        Convenience method to create a simple child task with shell commands.
        
        Args:
            parent_task_id: ID of the parent task
            child_task_name: Name for the child task
            description: What the child task does
            execution_steps: List of shell commands to execute
            relation_type: "required" or "optional"
            failure_policy: Failure policy
            
        Returns:
            Creation result
        """
        steps = []
        for i, cmd in enumerate(execution_steps):
            steps.append({
                "step_id": f"S{i+1:02d}",
                "name": f"Step {i+1}",
                "type": "execute_shell",
                "command": cmd
            })
        
        return self.create_child_task(
            parent_task_id=parent_task_id,
            child_task_name=child_task_name,
            steps=steps,
            relation_type=relation_type,
            failure_policy=failure_policy,
            description=description
        )
