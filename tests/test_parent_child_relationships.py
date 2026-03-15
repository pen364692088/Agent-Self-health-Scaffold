"""
Tests for Task Relationships in v3-B
"""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

from core.task_relationships import TaskRelationships


class TestTaskRelationships:
    """Test parent-child relationship management."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def relationships(self, temp_base):
        """Create relationships manager."""
        return TaskRelationships(base_path=temp_base)
    
    def test_create_relationship(self, relationships, temp_base):
        """Test creating a parent-child relationship."""
        # Create parent directory
        parent_dir = Path(temp_base) / "task_parent_001"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationship = relationships.create_relationship(
            parent_task_id="task_parent_001",
            child_task_id="task_child_001",
            relation_type="required",
            failure_policy="block_parent"
        )
        
        assert relationship["parent_task_id"] == "task_parent_001"
        assert relationship["child_task_id"] == "task_child_001"
        assert relationship["relation_type"] == "required"
        assert relationship["failure_policy"] == "block_parent"
        assert relationship["status"] == "created"
        assert relationship["relationship_id"].startswith("rel_")
    
    def test_relationship_persistence(self, relationships, temp_base):
        """Test that relationships are persisted to disk."""
        parent_dir = Path(temp_base) / "task_parent_002"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_002",
            child_task_id="task_child_002"
        )
        
        # Check file exists
        rel_path = Path(temp_base) / "task_parent_002" / "relationships.json"
        assert rel_path.exists()
        
        # Verify content
        with open(rel_path, 'r') as f:
            data = json.load(f)
        
        assert data["parent_task_id"] == "task_parent_002"
        assert len(data["children"]) == 1
        assert data["children"][0]["child_task_id"] == "task_child_002"
    
    def test_multiple_children(self, relationships, temp_base):
        """Test parent with multiple children."""
        parent_dir = Path(temp_base) / "task_parent_003"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_003",
            child_task_id="task_child_a",
            relation_type="required"
        )
        
        relationships.create_relationship(
            parent_task_id="task_parent_003",
            child_task_id="task_child_b",
            relation_type="optional"
        )
        
        children = relationships.get_all_children("task_parent_003")
        assert len(children) == 2
        
        required = relationships.get_required_children("task_parent_003")
        assert len(required) == 1
        assert required[0]["child_task_id"] == "task_child_a"
        
        optional = relationships.get_optional_children("task_parent_003")
        assert len(optional) == 1
        assert optional[0]["child_task_id"] == "task_child_b"
    
    def test_update_relationship_status(self, relationships, temp_base):
        """Test updating relationship status."""
        parent_dir = Path(temp_base) / "task_parent_004"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_004",
            child_task_id="task_child_004"
        )
        
        # Update status
        result = relationships.update_relationship_status(
            parent_task_id="task_parent_004",
            child_task_id="task_child_004",
            status="completed",
            result_ref="path/to/summary.md",
            gate_result=True
        )
        
        assert result is True
        
        # Verify update
        rel = relationships.get_relationship("task_parent_004", "task_child_004")
        assert rel["status"] == "completed"
        assert rel["result_ref"] == "path/to/summary.md"
        assert rel["child_gate_result"] is True
    
    def test_get_pending_children(self, relationships, temp_base):
        """Test getting pending children."""
        parent_dir = Path(temp_base) / "task_parent_005"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_005",
            child_task_id="task_child_running"
        )
        
        relationships.create_relationship(
            parent_task_id="task_parent_005",
            child_task_id="task_child_done"
        )
        
        # Update one to completed
        relationships.update_relationship_status(
            parent_task_id="task_parent_005",
            child_task_id="task_child_done",
            status="completed"
        )
        
        pending = relationships.get_pending_children("task_parent_005")
        assert len(pending) == 1
        assert pending[0]["child_task_id"] == "task_child_running"
    
    def test_has_blocking_failure(self, relationships, temp_base):
        """Test blocking failure detection."""
        parent_dir = Path(temp_base) / "task_parent_006"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Required child with block_parent
        relationships.create_relationship(
            parent_task_id="task_parent_006",
            child_task_id="task_child_required",
            relation_type="required",
            failure_policy="block_parent"
        )
        
        # Optional child
        relationships.create_relationship(
            parent_task_id="task_parent_006",
            child_task_id="task_child_optional",
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        # Initially no blocking failure
        assert relationships.has_blocking_failure("task_parent_006") is False
        
        # Mark required child as failed
        relationships.update_relationship_status(
            parent_task_id="task_parent_006",
            child_task_id="task_child_required",
            status="failed"
        )
        
        # Now should have blocking failure
        assert relationships.has_blocking_failure("task_parent_006") is True
        
        # Mark optional child as failed - should not add blocking
        relationships.update_relationship_status(
            parent_task_id="task_parent_006",
            child_task_id="task_child_optional",
            status="failed"
        )
        
        # Still only one blocking failure
        assert relationships.has_blocking_failure("task_parent_006") is True
    
    def test_all_required_children_completed(self, relationships, temp_base):
        """Test checking if all required children completed."""
        parent_dir = Path(temp_base) / "task_parent_007"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_007",
            child_task_id="task_child_1",
            relation_type="required"
        )
        
        relationships.create_relationship(
            parent_task_id="task_parent_007",
            child_task_id="task_child_2",
            relation_type="required"
        )
        
        # Not all completed initially
        assert relationships.all_required_children_completed("task_parent_007") is False
        
        # Complete one
        relationships.update_relationship_status(
            parent_task_id="task_parent_007",
            child_task_id="task_child_1",
            status="completed"
        )
        
        # Still not all
        assert relationships.all_required_children_completed("task_parent_007") is False
        
        # Complete the other
        relationships.update_relationship_status(
            parent_task_id="task_parent_007",
            child_task_id="task_child_2",
            status="failed"  # Failed also counts as "completed" for this check
        )
        
        # Now all completed
        assert relationships.all_required_children_completed("task_parent_007") is True
    
    def test_count_children_by_status(self, relationships, temp_base):
        """Test counting children by status."""
        parent_dir = Path(temp_base) / "task_parent_008"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        relationships.create_relationship(
            parent_task_id="task_parent_008",
            child_task_id="child_1"
        )
        relationships.create_relationship(
            parent_task_id="task_parent_008",
            child_task_id="child_2"
        )
        relationships.create_relationship(
            parent_task_id="task_parent_008",
            child_task_id="child_3"
        )
        
        relationships.update_relationship_status(
            parent_task_id="task_parent_008",
            child_task_id="child_1",
            status="completed"
        )
        relationships.update_relationship_status(
            parent_task_id="task_parent_008",
            child_task_id="child_2",
            status="running"
        )
        
        counts = relationships.count_children_by_status("task_parent_008")
        
        assert counts["total"] == 3
        assert counts["completed"] == 1
        assert counts["running"] == 1
        assert counts["created"] == 1


class TestRelationshipRecovery:
    """Test relationship recovery after restart."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_recovery_from_disk(self, temp_base):
        """Test that relationships can be recovered from disk."""
        # Create initial relationships
        rel1 = TaskRelationships(base_path=temp_base)
        parent_dir = Path(temp_base) / "task_parent_recovery"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        rel1.create_relationship(
            parent_task_id="task_parent_recovery",
            child_task_id="child_a"
        )
        rel1.create_relationship(
            parent_task_id="task_parent_recovery",
            child_task_id="child_b"
        )
        
        # Create new instance (simulating restart)
        rel2 = TaskRelationships(base_path=temp_base)
        
        # Should be able to load existing relationships
        children = rel2.get_all_children("task_parent_recovery")
        assert len(children) == 2
        assert children[0]["child_task_id"] == "child_a"
        assert children[1]["child_task_id"] == "child_b"
