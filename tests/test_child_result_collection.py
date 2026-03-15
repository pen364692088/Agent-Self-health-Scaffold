"""
Tests for Child Result Collection in v3-B
"""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

from core.task_relationships import TaskRelationships
from core.child_result_collector import ChildResultCollector


class TestChildResultCollection:
    """Test child result collection."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def collector(self, temp_base):
        """Create result collector."""
        relationships = TaskRelationships(base_path=temp_base)
        return ChildResultCollector(base_path=temp_base, relationships_manager=relationships)
    
    def _setup_completed_child(self, temp_base, child_task_id, parent_task_id, status="completed"):
        """Setup a completed child task with artifacts."""
        # Create child directory structure
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # Create task state
        task_state = {
            "task_id": child_task_id,
            "status": status,
            "parent_task_id": parent_task_id
        }
        with open(child_dir / "task_state.json", 'w') as f:
            json.dump(task_state, f)
        
        # Create SUMMARY.md
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Summary\n\nTask completed.")
        
        # Create gate_report.json
        gate_report = {
            "all_passed": status == "completed",
            "checks": []
        }
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump(gate_report, f)
        
        # Create receipt.json
        receipt = {
            "task_id": child_task_id,
            "status": status
        }
        with open(final_dir / "receipt.json", 'w') as f:
            json.dump(receipt, f)
    
    def test_collect_child_result(self, collector, temp_base):
        """Test collecting result from a completed child."""
        parent_task_id = "task_parent_collect"
        child_task_id = "task_child_collect"
        
        # Setup parent and child
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_completed_child(temp_base, child_task_id, parent_task_id)
        
        # Create relationship
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id
        )
        
        # Collect result
        result = collector.collect_child_result(parent_task_id, child_task_id)
        
        assert result is not None
        assert result["child_task_id"] == child_task_id
        assert result["parent_task_id"] == parent_task_id
        assert result["status"] == "completed"
        assert result["gate_passed"] is True
        assert result["artifacts"]["summary_path"] is not None
    
    def test_collect_failed_child_result(self, collector, temp_base):
        """Test collecting result from a failed child."""
        parent_task_id = "task_parent_failed"
        child_task_id = "task_child_failed"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup failed child
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        task_state = {
            "task_id": child_task_id,
            "status": "failed",
            "parent_task_id": parent_task_id,
            "failure_class": "execution_error",
            "failure_message": "Command failed"
        }
        with open(child_dir / "task_state.json", 'w') as f:
            json.dump(task_state, f)
        
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Failed\n")
        
        gate_report = {"all_passed": False}
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump(gate_report, f)
        
        receipt = {"task_id": child_task_id, "status": "failed"}
        with open(final_dir / "receipt.json", 'w') as f:
            json.dump(receipt, f)
        
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id
        )
        
        result = collector.collect_child_result(parent_task_id, child_task_id)
        
        assert result["status"] == "failed"
        assert result["failure_class"] == "execution_error"
        assert result["gate_passed"] is False
    
    def test_collect_all_child_results(self, collector, temp_base):
        """Test collecting results from all children."""
        parent_task_id = "task_parent_all"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create two children
        child_a = "task_child_all_a"
        child_b = "task_child_all_b"
        
        self._setup_completed_child(temp_base, child_a, parent_task_id, "completed")
        self._setup_completed_child(temp_base, child_b, parent_task_id, "completed")
        
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_a
        )
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_b
        )
        
        # Collect all
        result = collector.collect_all_child_results(parent_task_id)
        
        assert result["success"] is True
        assert result["total_children"] == 2
        assert len(result["results"]) == 2
        assert result["summary"]["completed"] == 2
    
    def test_child_results_saved_to_parent(self, collector, temp_base):
        """Test that results are saved to parent's child_results.json."""
        parent_task_id = "task_parent_save"
        child_task_id = "task_child_save"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_completed_child(temp_base, child_task_id, parent_task_id)
        
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id
        )
        
        collector.collect_child_result(parent_task_id, child_task_id)
        
        # Check child_results.json
        results_path = parent_dir / "child_results.json"
        assert results_path.exists()
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["collected_results"]) == 1
        assert data["collected_results"][0]["child_task_id"] == child_task_id
    
    def test_validate_child_artifacts(self, collector, temp_base):
        """Test artifact validation."""
        child_task_id = "task_child_validate"
        
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # Create all required artifacts
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Summary")
        with open(final_dir / "gate_report.json", 'w') as f:
            json.dump({"all_passed": True}, f)
        with open(final_dir / "receipt.json", 'w') as f:
            json.dump({"status": "completed"}, f)
        
        result = collector.validate_child_artifacts(child_task_id)
        
        assert result["all_passed"] is True
        assert all(c["passed"] for c in result["checks"])
    
    def test_validate_child_artifacts_missing(self, collector, temp_base):
        """Test artifact validation with missing files."""
        child_task_id = "task_child_missing"
        
        child_dir = Path(temp_base) / child_task_id
        child_dir.mkdir(parents=True, exist_ok=True)
        final_dir = child_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # Only create one artifact
        with open(final_dir / "SUMMARY.md", 'w') as f:
            f.write("# Summary")
        
        result = collector.validate_child_artifacts(child_task_id)
        
        assert result["all_passed"] is False
        failed_checks = [c for c in result["checks"] if not c["passed"]]
        assert len(failed_checks) == 2  # gate_report and receipt missing
    
    def test_all_required_results_collected(self, collector, temp_base):
        """Test checking if all required results are collected."""
        parent_task_id = "task_parent_required"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create required and optional children
        child_req = "task_child_required"
        child_opt = "task_child_optional"
        
        self._setup_completed_child(temp_base, child_req, parent_task_id)
        self._setup_completed_child(temp_base, child_opt, parent_task_id)
        
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_req,
            relation_type="required"
        )
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_opt,
            relation_type="optional"
        )
        
        # Initially not all collected
        assert collector.all_required_results_collected(parent_task_id) is False
        
        # Collect required child result
        collector.collect_child_result(parent_task_id, child_req)
        
        # Now all required collected
        assert collector.all_required_results_collected(parent_task_id) is True
    
    def test_relationship_updated_on_collection(self, collector, temp_base):
        """Test that relationship is updated when result is collected."""
        parent_task_id = "task_parent_update"
        child_task_id = "task_child_update"
        
        parent_dir = Path(temp_base) / parent_task_id
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_completed_child(temp_base, child_task_id, parent_task_id)
        
        collector.relationships.create_relationship(
            parent_task_id=parent_task_id,
            child_task_id=child_task_id
        )
        
        # Collect result
        collector.collect_child_result(parent_task_id, child_task_id)
        
        # Check relationship updated
        rel = collector.relationships.get_relationship(parent_task_id, child_task_id)
        assert rel["status"] == "completed"
        assert rel["child_gate_result"] is True
        assert rel["result_ref"] is not None
