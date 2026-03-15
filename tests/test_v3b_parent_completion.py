"""
Tests for Parent Completion Gate in v3-B
"""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

from core.task_relationships import TaskRelationships
from core.child_result_collector import ChildResultCollector
from runtime.parent_completion_guard import ParentCompletionGuard


class TestParentCompletionGuard:
    """Test parent completion gate checks."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def guard(self, temp_base):
        """Create parent completion guard."""
        relationships = TaskRelationships(base_path=temp_base)
        collector = ChildResultCollector(base_path=temp_base, relationships_manager=relationships)
        return ParentCompletionGuard(
            base_path=temp_base,
            relationships_manager=relationships,
            result_collector=collector
        )
    
    def _setup_completed_child(self, temp_base, child_task_id, parent_task_id, gate_passed=True):
        """Setup a completed child task with artifacts."""
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        task_state = {
            "task_id": child_task_id,
            "status": "completed",
            "parent_task_id": parent_task_id
        }
        with open(child_dir / "task_state.json", 'w') as f:
            json.dump(task_state, f)
        
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Summary\n")
        
        gate_report = {"all_passed": gate_passed, "checks": []}
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump(gate_report, f)
        
        receipt = {"task_id": child_task_id, "status": "completed"}
        with open(final_dir / "receipt.json", 'w') as f:
            json.dump(receipt, f)
    
    def test_check_all_required_children_completed(self, guard, temp_base):
        """Test checking if all required children completed."""
        parent_task_id = "task_parent_required_check"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create required child
        child_task_id = "task_child_required_check"
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required"
        )
        
        # Not completed initially
        result = guard.check_all_required_children_completed(parent_task_id)
        assert result["passed"] is False
        
        # Mark as completed
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="completed"
        )
        
        result = guard.check_all_required_children_completed(parent_task_id)
        assert result["passed"] is True
    
    def test_check_required_child_artifacts(self, guard, temp_base):
        """Test checking required child artifacts exist."""
        parent_task_id = "task_parent_artifacts"
        child_task_id = "task_child_artifacts"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required"
        )
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="completed"
        )
        
        # No artifacts initially
        result = guard.check_required_child_artifacts(parent_task_id)
        assert result["passed"] is False
        
        # Create artifacts
        self._setup_completed_child(temp_base, child_task_id, parent_task_id)
        
        result = guard.check_required_child_artifacts(parent_task_id)
        assert result["passed"] is True
    
    def test_check_required_child_gates(self, guard, temp_base):
        """Test checking required child gates passed."""
        parent_task_id = "task_parent_gates"
        child_task_id = "task_child_gates"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required"
        )
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="completed"
        )
        
        # Create child with failed gate
        self._setup_completed_child(temp_base, child_task_id, parent_task_id, gate_passed=False)
        
        result = guard.check_required_child_gates(parent_task_id)
        assert result["passed"] is False
        
        # Create child with passed gate
        final_dir = Path(temp_base) / child_task_id / "final"
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump({"all_passed": True}, f)
        
        result = guard.check_required_child_gates(parent_task_id)
        assert result["passed"] is True
    
    def test_check_no_blocking_failures(self, guard, temp_base):
        """Test checking for blocking failures."""
        parent_task_id = "task_parent_blocking"
        child_task_id = "task_child_blocking"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required",
            failure_policy="block_parent"
        )
        
        # No failure initially
        result = guard.check_no_blocking_failures(parent_task_id)
        assert result["passed"] is True
        
        # Mark as failed
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="failed"
        )
        
        result = guard.check_no_blocking_failures(parent_task_id)
        assert result["passed"] is False
    
    def test_run_completion_gate_all_passed(self, guard, temp_base):
        """Test running full completion gate with all checks passed."""
        parent_task_id = "task_parent_all_pass"
        child_task_id = "task_child_all_pass"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required"
        )
        
        # Setup completed child with all artifacts
        self._setup_completed_child(temp_base, child_task_id, parent_task_id, gate_passed=True)
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="completed"
        )
        
        result = guard.run_completion_gate(parent_task_id)
        
        assert result["all_passed"] is True
        assert all(c["passed"] for c in result["checks"])
    
    def test_run_completion_gate_with_failure(self, guard, temp_base):
        """Test running completion gate with failed child."""
        parent_task_id = "task_parent_with_failure"
        child_task_id = "task_child_failed"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required",
            failure_policy="block_parent"
        )
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="failed"
        )
        
        result = guard.run_completion_gate(parent_task_id)
        
        assert result["all_passed"] is False
    
    def test_can_parent_complete(self, guard, temp_base):
        """Test can_parent_complete method."""
        parent_task_id = "task_parent_can_complete"
        child_task_id = "task_child_can_complete"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            relation_type="required"
        )
        
        # Cannot complete initially
        can_complete, reason = guard.can_parent_complete(parent_task_id)
        assert can_complete is False
        
        # Setup completed child
        self._setup_completed_child(temp_base, child_task_id, parent_task_id)
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id,
            status="completed"
        )
        
        can_complete, reason = guard.can_parent_complete(parent_task_id)
        assert can_complete is True
        assert reason is None
    
    def test_generate_gate_report_file(self, guard, temp_base):
        """Test generating gate report file."""
        parent_task_id = "task_parent_report"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # No children - should pass
        report_path = guard.generate_gate_report_file(parent_task_id)
        
        assert Path(report_path).exists()
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report["parent_task_id"] == parent_task_id
        assert report["all_passed"] is True


class TestParentCompletionWithOptionalChildren:
    """Test parent completion with mix of required and optional children."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def guard(self, temp_base):
        """Create parent completion guard."""
        relationships = TaskRelationships(base_path=temp_base)
        collector = ChildResultCollector(base_path=temp_base, relationships_manager=relationships)
        return ParentCompletionGuard(
            base_path=temp_base,
            relationships_manager=relationships,
            result_collector=collector
        )
    
    def _setup_completed_child(self, temp_base, child_task_id, parent_task_id):
        """Setup a completed child task."""
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        with open(child_dir / "task_state.json", 'w') as f:
            json.dump({"task_id": child_task_id, "status": "completed"}, f)
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Summary")
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump({"all_passed": True}, f)
        with open(final_dir / "receipt.json", 'w') as f:
            json.dump({"status": "completed"}, f)
    
    def test_optional_child_failure_does_not_block(self, guard, temp_base):
        """Test that optional child failure doesn't block parent."""
        parent_task_id = "task_parent_optional_fail"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Required child - completed
        required_child = "task_child_required_ok"
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=required_child,
            relation_type="required"
        )
        self._setup_completed_child(temp_base, required_child, parent_task_id)
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=required_child,
            status="completed"
        )
        
        # Optional child - failed with continue_with_warning
        optional_child = "task_child_optional_failed"
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=optional_child,
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=optional_child,
            status="failed"
        )
        
        # Parent should be able to complete
        can_complete, reason = guard.can_parent_complete(parent_task_id)
        assert can_complete is True
    
    def test_required_blocks_optional_ok(self, guard, temp_base):
        """Test that required child failure blocks even if optional succeeded."""
        parent_task_id = "task_parent_required_blocks"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Required child - failed with block_parent
        required_child = "task_child_required_failed"
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=required_child,
            relation_type="required",
            failure_policy="block_parent"
        )
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=required_child,
            status="failed"
        )
        
        # Optional child - completed
        optional_child = "task_child_optional_ok"
        guard.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=optional_child,
            relation_type="optional"
        )
        self._setup_completed_child(temp_base, optional_child, parent_task_id)
        guard.relationships.update_relationship_status(
            parent_task_id=parent_task_id,
            child_task_id=optional_child,
            status="completed"
        )
        
        # Parent should be blocked
        can_complete, reason = guard.can_parent_complete(parent_task_id)
        assert can_complete is False
        assert "blocking" in reason.lower() or "failed" in reason.lower()


class TestParentCompletionNoChildren:
    """Test parent completion when there are no children."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def guard(self, temp_base):
        """Create parent completion guard."""
        relationships = TaskRelationships(base_path=temp_base)
        collector = ChildResultCollector(base_path=temp_base, relationships_manager=relationships)
        return ParentCompletionGuard(
            base_path=temp_base,
            relationships_manager=relationships,
            result_collector=collector
        )
    
    def test_no_children_can_complete(self, guard, temp_base):
        """Test that parent with no children can complete."""
        parent_task_id = "task_parent_no_children"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        can_complete, reason = guard.can_parent_complete(parent_task_id)
        assert can_complete is True
