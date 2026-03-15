"""
Tests for Cascade Failure Policy in v3-B
"""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

from core.task_relationships import TaskRelationships
from runtime.cascade_policy import CascadePolicy, FailurePolicy


class TestCascadePolicy:
    """Test cascade failure policy evaluation."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cascade_policy(self, temp_base):
        """Create cascade policy manager."""
        relationships = TaskRelationships(base_path=temp_base)
        return CascadePolicy(base_path=temp_base, relationships_manager=relationships)
    
    def test_evaluate_block_parent_policy(self, cascade_policy, temp_base):
        """Test block_parent failure policy evaluation."""
        parent_task_id = "task_parent_block"
        child_task_id = "task_child_block"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required",
            failure_policy="block_parent"
        )
        
        # Mark child as failed
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="failed"
        )
        
        result = cascade_policy.evaluate_child_failure(parent_task_id, child_task_id)
        
        assert result["action"] == "block_parent"
        assert child_task_id in result["reason"]
    
    def test_evaluate_continue_with_warning_policy(self, cascade_policy, temp_base):
        """Test continue_with_warning failure policy evaluation."""
        parent_task_id = "task_parent_warning"
        child_task_id = "task_child_warning"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="failed"
        )
        
        result = cascade_policy.evaluate_child_failure(parent_task_id, child_task_id)
        
        assert result["action"] == "continue_with_warning"
        assert "warning" in result
    
    def test_optional_child_with_block_parent(self, cascade_policy, temp_base):
        """Test optional child with block_parent policy (edge case)."""
        parent_task_id = "task_parent_opt_block"
        child_task_id = "task_child_opt_block"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="optional",
            failure_policy="block_parent"
        )
        
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="failed"
        )
        
        result = cascade_policy.evaluate_child_failure(parent_task_id, child_task_id)
        
        # Should still block because policy is block_parent
        assert result["action"] == "block_parent"
    
    def test_evaluate_parent_cancellation(self, cascade_policy, temp_base):
        """Test evaluation when parent is cancelled."""
        parent_task_id = "task_parent_cancel"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create multiple pending children
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_running_1",
            relation_type="required"
        )
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_running_2",
            relation_type="optional"
        )
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_done",
            relation_type="required"
        )
        
        # Mark one as completed
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_done",
            status="completed"
        )
        
        result = cascade_policy.evaluate_parent_cancellation(parent_task_id)
        
        assert result["cancel_children"] is True
        assert len(result["children_to_cancel"]) == 2  # Only pending children
        assert "child_done" not in result["children_to_cancel"]
    
    def test_record_warning(self, cascade_policy, temp_base):
        """Test recording warning in parent task state."""
        parent_task_id = "task_parent_record"
        child_task_id = "task_child_record"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create parent task state
        task_state = {
            "task_id": parent_task_id,
            "status": "running"
        }
        with open(parent_dir / "task_state.json", 'w') as f:
            json.dump(task_state, f)
        
        cascade_policy.record_warning(
            parent_task_id=parent_task_id,
            warning="Child task failed but continuing",
            child_task_id=child_task_id
        )
        
        # Verify warning recorded
        with open(parent_dir / "task_state.json", 'r') as f:
            updated_state = json.load(f)
        
        assert "warnings" in updated_state
        assert len(updated_state["warnings"]) == 1
        assert updated_state["warnings"][0]["child_task_id"] == child_task_id
    
    def test_get_all_failure_actions(self, cascade_policy, temp_base):
        """Test getting failure actions for all failed children."""
        parent_task_id = "task_parent_all_failures"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create multiple failed children with different policies
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_block",
            relation_type="required",
            failure_policy="block_parent"
        )
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_warn",
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_block",
            status="failed"
        )
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_warn",
            status="failed"
        )
        
        actions = cascade_policy.get_all_failure_actions(parent_task_id)
        
        assert len(actions) == 2
        action_types = {a["action"] for a in actions}
        assert "block_parent" in action_types
        assert "continue_with_warning" in action_types
    
    def test_should_block_parent(self, cascade_policy, temp_base):
        """Test determining if parent should be blocked."""
        parent_task_id = "task_parent_should_block"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # No failures initially
        should_block, reason = cascade_policy.should_block_parent(parent_task_id)
        assert should_block is False
        
        # Add blocking failure
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_blocking",
            relation_type="required",
            failure_policy="block_parent"
        )
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_blocking",
            status="failed"
        )
        
        should_block, reason = cascade_policy.should_block_parent(parent_task_id)
        assert should_block is True
        assert reason is not None
    
    def test_get_warnings_to_record(self, cascade_policy, temp_base):
        """Test getting warnings to record for non-blocking failures."""
        parent_task_id = "task_parent_warnings"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create children with continue_with_warning policy
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_warn_1",
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="child_warn_2",
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_warn_1",
            status="failed"
        )
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="child_warn_2",
            status="failed"
        )
        
        warnings = cascade_policy.get_warnings_to_record(parent_task_id)
        
        assert len(warnings) == 2
        assert all("child_task_id" in w for w in warnings)


class TestMixedFailureScenarios:
    """Test complex scenarios with mixed failure policies."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cascade_policy(self, temp_base):
        """Create cascade policy manager."""
        relationships = TaskRelationships(base_path=temp_base)
        return CascadePolicy(base_path=temp_base, relationships_manager=relationships)
    
    def test_required_blocks_optional_continues(self, cascade_policy, temp_base):
        """Test scenario where required child blocks but optional continues."""
        parent_task_id = "task_parent_mixed"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Required child with block_parent
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="required_child",
            relation_type="required",
            failure_policy="block_parent"
        )
        
        # Optional child with continue_with_warning
        cascade_policy.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id="optional_child",
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        # Both fail
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="required_child",
            status="failed"
        )
        cascade_policy.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id="optional_child",
            status="failed"
        )
        
        # Should block due to required child
        should_block, reason = cascade_policy.should_block_parent(parent_task_id)
        assert should_block is True
        
        # But warnings should still be collected
        warnings = cascade_policy.get_warnings_to_record(parent_task_id)
        assert len(warnings) == 1  # Only optional child produces warning
