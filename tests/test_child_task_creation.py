"""
Tests for Child Task Creation in v3-B
"""

import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path

from core.task_relationships import TaskRelationships
from core.child_task_factory import ChildTaskFactory


class TestChildTaskCreation:
    """Test child task creation and initialization."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def factory(self, temp_base):
        """Create child task factory."""
        relationships = TaskRelationships(base_path=temp_base)
        return ChildTaskFactory(base_path=temp_base, relationships_manager=relationships)
    
    def test_create_child_task(self, factory, temp_base):
        """Test basic child task creation."""
        # Create parent directory
        parent_dir = Path(temp_base) / "task_parent_001"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        steps = [
            {"name": "Step 1", "type": "execute_shell", "command": "echo hello"}
        ]
        
        result = factory.create_child_task(
            parent_task_id="task_parent_001",
            child_task_name="Test Child",
            steps=steps,
            description="Test child task"
        )
        
        assert result["status"] == "created"
        assert result["parent_task_id"] == "task_parent_001"
        assert result["child_task_id"].startswith("task_")
        
        # Check task state file
        task_state_path = Path(result["task_state_path"])
        assert task_state_path.exists()
        
        with open(task_state_path, 'r') as f:
            task_state = json.load(f)
        
        assert task_state["task_name"] == "Test Child"
        assert task_state["parent_task_id"] == "task_parent_001"
        assert task_state["status"] == "pending"
    
    def test_child_task_has_step_packet(self, factory, temp_base):
        """Test that child task has step packet."""
        parent_dir = Path(temp_base) / "task_parent_002"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        steps = [
            {"name": "Step A", "type": "execute_shell", "command": "ls"},
            {"name": "Step B", "type": "execute_shell", "command": "pwd"}
        ]
        
        result = factory.create_child_task(
            parent_task_id="task_parent_002",
            child_task_name="Child with Steps",
            steps=steps
        )
        
        step_packet_path = Path(result["step_packet_path"])
        assert step_packet_path.exists()
        
        with open(step_packet_path, 'r') as f:
            step_packet = json.load(f)
        
        assert len(step_packet["steps"]) == 2
        assert step_packet["parent_task_id"] == "task_parent_002"
    
    def test_child_task_ledger(self, factory, temp_base):
        """Test that child task has initialized ledger."""
        parent_dir = Path(temp_base) / "task_parent_003"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result = factory.create_child_task(
            parent_task_id="task_parent_003",
            child_task_name="Child with Ledger",
            steps=[]
        )
        
        ledger_path = Path(temp_base) / result["child_task_id"] / "ledger.jsonl"
        assert ledger_path.exists()
        
        with open(ledger_path, 'r') as f:
            line = f.readline()
            event = json.loads(line)
        
        assert event["event"] == "task_created"
        assert event["parent_task_id"] == "task_parent_003"
    
    def test_relation_type_and_failure_policy(self, factory, temp_base):
        """Test that relation type and failure policy are set correctly."""
        parent_dir = Path(temp_base) / "task_parent_004"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result = factory.create_child_task(
            parent_task_id="task_parent_004",
            child_task_name="Optional Child",
            steps=[],
            relation_type="optional",
            failure_policy="continue_with_warning"
        )
        
        # Check relationship was created with correct settings
        relationship = result["relationship"]
        assert relationship["relation_type"] == "optional"
        assert relationship["failure_policy"] == "continue_with_warning"
    
    def test_input_context_passed(self, factory, temp_base):
        """Test that input context is passed to child task."""
        parent_dir = Path(temp_base) / "task_parent_005"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        input_context = {
            "target_file": "docs/index.md",
            "categories": ["api", "guide", "tutorial"]
        }
        
        result = factory.create_child_task(
            parent_task_id="task_parent_005",
            child_task_name="Child with Context",
            steps=[],
            input_context=input_context
        )
        
        step_packet_path = Path(result["step_packet_path"])
        with open(step_packet_path, 'r') as f:
            step_packet = json.load(f)
        
        assert step_packet["input_context"]["target_file"] == "docs/index.md"
        assert len(step_packet["input_context"]["categories"]) == 3
    
    def test_dispatch_child_task(self, factory, temp_base):
        """Test dispatching a child task."""
        parent_dir = Path(temp_base) / "task_parent_006"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result = factory.create_child_task(
            parent_task_id="task_parent_006",
            child_task_name="Dispatchable Child",
            steps=[]
        )
        
        child_task_id = result["child_task_id"]
        
        # Dispatch
        dispatch_result = factory.dispatch_child_task(child_task_id)
        assert dispatch_result is True
        
        # Check state updated
        task_state = factory.get_child_task_state(child_task_id)
        assert task_state["status"] == "dispatched"
    
    def test_create_simple_child_task(self, factory, temp_base):
        """Test convenience method for simple child task."""
        parent_dir = Path(temp_base) / "task_parent_007"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result = factory.create_simple_child_task(
            parent_task_id="task_parent_007",
            child_task_name="Simple Child",
            description="A simple child task",
            execution_steps=["ls -la", "pwd"],
            relation_type="required"
        )
        
        assert result["status"] == "created"
        
        # Check steps were created
        step_packet_path = Path(result["step_packet_path"])
        with open(step_packet_path, 'r') as f:
            step_packet = json.load(f)
        
        assert len(step_packet["steps"]) == 2
        assert step_packet["steps"][0]["command"] == "ls -la"
    
    def test_child_task_independent_directory(self, factory, temp_base):
        """Test that each child task has its own directory."""
        parent_dir = Path(temp_base) / "task_parent_008"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result1 = factory.create_child_task(
            parent_task_id="task_parent_008",
            child_task_name="Child 1",
            steps=[]
        )
        
        result2 = factory.create_child_task(
            parent_task_id="task_parent_008",
            child_task_name="Child 2",
            steps=[]
        )
        
        # Different task IDs
        assert result1["child_task_id"] != result2["child_task_id"]
        
        # Different directories
        dir1 = Path(temp_base) / result1["child_task_id"]
        dir2 = Path(temp_base) / result2["child_task_id"]
        
        assert dir1 != dir2
        assert dir1.exists()
        assert dir2.exists()


class TestChildTaskRelationships:
    """Test that child tasks are properly registered in relationships."""
    
    @pytest.fixture
    def temp_base(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def factory(self, temp_base):
        """Create child task factory."""
        relationships = TaskRelationships(base_path=temp_base)
        return ChildTaskFactory(base_path=temp_base, relationships_manager=relationships)
    
    def test_relationship_registered(self, factory, temp_base):
        """Test that relationship is registered when child is created."""
        parent_dir = Path(temp_base) / "task_parent_rel"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        result = factory.create_child_task(
            parent_task_id="task_parent_rel",
            child_task_name="Registered Child",
            steps=[]
        )
        
        # Check relationship file
        rel_path = Path(temp_base) / "task_parent_rel" / "relationships.json"
        assert rel_path.exists()
        
        with open(rel_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["children"]) == 1
        assert data["children"][0]["child_task_id"] == result["child_task_id"]
    
    def test_multiple_children_registered(self, factory, temp_base):
        """Test that multiple children are all registered."""
        parent_dir = Path(temp_base) / "task_parent_multi"
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        factory.create_child_task(
            parent_task_id="task_parent_multi",
            child_task_name="Child A",
            steps=[],
            relation_type="required"
        )
        
        factory.create_child_task(
            parent_task_id="task_parent_multi",
            child_task_name="Child B",
            steps=[],
            relation_type="optional"
        )
        
        rel_path = Path(temp_base) / "task_parent_multi" / "relationships.json"
        with open(rel_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["children"]) == 2
        relation_types = {c["relation_type"] for c in data["children"]}
        assert "required" in relation_types
        assert "optional" in relation_types
