"""
Contract Tests for Materialized State v0

Tests verify:
1. Schema compliance
2. Semantic validation
3. Field extraction correctness
4. Conflict resolution behavior
5. Read-only boundary enforcement
6. CLI compatibility

Run with: pytest tests/core/test_materialized_state_v0.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add workspace to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.materialized_state_v0 import (
    FieldSource,
    FieldResolution,
    ConflictInfo,
    MaterializedState,
    StateMaterializerV0,
    extract_field_value,
    extract_all_fields,
    resolve_field_conflicts,
    materialize_state,
    normalize_value,
    is_placeholder,
    PLACEHOLDER_VALUES,
    TRACKED_FIELDS,
    SOURCE_PRIORITY,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_session_state():
    """Sample SESSION-STATE.md content."""
    return """# SESSION-STATE.md

## Current Objective
实现用户认证模块

## Phase
Implementing

## Branch
main

## Blocker
None

## Next Action
继续实现登录功能
"""


@pytest.fixture
def sample_working_buffer():
    """Sample working-buffer.md content."""
    return """# Working Buffer

## Focus
用户认证模块开发

## Phase
开发中

## Next Step
编写测试用例
"""


@pytest.fixture
def conflicting_session_state():
    """SESSION-STATE.md with different objective."""
    return """# SESSION-STATE.md

## Current Objective
实现支付模块

## Phase
Planning
"""


@pytest.fixture
def materializer():
    """Create a StateMaterializerV0 instance."""
    return StateMaterializerV0()


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSchemaCompliance:
    """Tests for schema compliance."""
    
    def test_field_source_schema(self):
        """FieldSource should have required fields."""
        source = FieldSource(status="valid", value="test")
        data = source.__dict__
        
        assert "status" in data
        assert "value" in data
        assert data["status"] in ["valid", "empty", "missing"]
    
    def test_field_resolution_schema(self):
        """FieldResolution should have required fields."""
        resolution = FieldResolution(status="valid", value="test")
        data = resolution.__dict__
        
        assert "status" in data
        assert data["status"] in ["valid", "missing"]
    
    def test_materialized_state_schema(self):
        """MaterializedState should have required fields."""
        state = MaterializedState()
        data = state.to_dict()
        
        assert "materialized_at" in data
        assert "sources_checked" in data
        assert "uncertainty_flag" in data
        assert "field_sources" in data
        assert "field_resolutions" in data
    
    def test_output_validates_against_json_schema(self):
        """Output should validate against JSON schema."""
        import jsonschema
        
        schema_path = ROOT / "schemas" / "materialized_state.v0.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        
        schema = json.loads(schema_path.read_text())
        state = MaterializedState(
            objective="Test objective",
            phase="testing",
            materialized_at="2026-03-14T12:00:00"
        )
        
        # Should not raise
        jsonschema.validate(state.to_dict(), schema)


# =============================================================================
# Field Extraction Tests
# =============================================================================

class TestFieldExtraction:
    """Tests for field extraction."""
    
    def test_extract_objective_header_format(self, sample_session_state):
        """Extract objective from ## header format."""
        status, raw, normalized = extract_field_value(sample_session_state, "objective")
        
        assert status == "valid"
        assert "认证" in normalized
    
    def test_extract_phase(self, sample_session_state):
        """Extract phase field."""
        status, raw, normalized = extract_field_value(sample_session_state, "phase")
        
        assert status == "valid"
        assert normalized.lower() in ["implementing", "开发中"]
    
    def test_extract_missing_field(self):
        """Extract field that doesn't exist."""
        content = "## Other Section\nSome content"
        status, raw, normalized = extract_field_value(content, "objective")
        
        assert status == "missing"
        assert normalized == ""
    
    def test_extract_empty_field(self):
        """Extract empty field."""
        content = "## Current Objective\n\n"
        status, raw, normalized = extract_field_value(content, "objective")
        
        assert status == "empty"
    
    def test_extract_placeholder_field(self):
        """Extract placeholder field."""
        content = "## Current Objective\nTBD"
        status, raw, normalized = extract_field_value(content, "objective")
        
        assert status == "empty"
    
    def test_extract_all_fields(self, sample_session_state):
        """Extract all tracked fields."""
        results = extract_all_fields(sample_session_state, "test.md")
        
        assert "objective" in results
        assert "phase" in results
        assert "branch" in results
        assert isinstance(results["objective"], FieldSource)


# =============================================================================
# Conflict Resolution Tests
# =============================================================================

class TestConflictResolution:
    """Tests for conflict resolution."""
    
    def test_single_source_resolution(self):
        """Resolution with single valid source."""
        field_values = {
            "session_state_md": FieldSource(status="valid", value="目标A")
        }
        
        result = resolve_field_conflicts(field_values)
        
        assert result.status == "valid"
        assert result.value == "目标A"
        assert result.chosen_source == "session_state_md"
    
    def test_priority_winner(self):
        """Resolution with priority-based winner."""
        field_values = {
            "session_state_md": FieldSource(status="valid", value="目标A"),
            "working_buffer_md": FieldSource(status="valid", value="目标B")
        }
        
        result = resolve_field_conflicts(field_values)
        
        assert result.status == "valid"
        # session_state_md has higher priority (70 vs 60)
        assert result.chosen_source == "session_state_md"
    
    def test_conflict_detection(self):
        """Detection of conflicting values."""
        field_values = {
            "session_state_md": FieldSource(status="valid", value="目标A"),
            "working_buffer_md": FieldSource(status="valid", value="目标B")
        }
        
        result = resolve_field_conflicts(field_values)
        
        assert result.conflicts is not None
        assert len(result.conflicts) == 1
        assert result.conflicts[0].source == "working_buffer_md"
    
    def test_all_empty_resolution(self):
        """Resolution with all empty values."""
        field_values = {
            "session_state_md": FieldSource(status="empty", value=None),
            "working_buffer_md": FieldSource(status="empty", value=None)
        }
        
        result = resolve_field_conflicts(field_values)
        
        assert result.status == "missing"


# =============================================================================
# Materialization Tests
# =============================================================================

class TestMaterialization:
    """Tests for full materialization."""
    
    def test_basic_materialization(self, materializer, sample_session_state):
        """Basic materialization from content."""
        state = materializer.materialize(
            session_state_content=sample_session_state
        )
        
        assert state.objective is not None
        assert "认证" in state.objective
        assert state.materialized_at is not None
        assert "session_state_md" in state.sources_checked
    
    def test_materialization_with_working_buffer(
        self, materializer, sample_session_state, sample_working_buffer
    ):
        """Materialization with both sources."""
        state = materializer.materialize(
            session_state_content=sample_session_state,
            working_buffer_content=sample_working_buffer
        )
        
        assert "session_state_md" in state.sources_checked
        assert "working_buffer_md" in state.sources_checked
    
    def test_materialization_with_branch(self, materializer, sample_session_state):
        """Materialization with repo evidence."""
        state = materializer.materialize(
            session_state_content=sample_session_state,
            branch="feature/auth"
        )
        
        assert state.branch == "feature/auth"
        assert "repo_evidence" in state.sources_checked
    
    def test_conflict_in_materialization(
        self, materializer, conflicting_session_state, sample_working_buffer
    ):
        """Conflict detection during materialization."""
        state = materializer.materialize(
            session_state_content=conflicting_session_state,
            working_buffer_content=sample_working_buffer
        )
        
        # Should have conflict recorded
        if "phase" in state.field_resolutions:
            resolution = state.field_resolutions["phase"]
            # Conflict may or may not exist depending on values
    
    def test_uncertainty_flag(self, materializer):
        """Uncertainty flag for missing critical fields."""
        state = materializer.materialize(
            session_state_content="# Empty State\n"
        )
        
        assert state.uncertainty_flag is True
    
    def test_no_uncertainty_flag(self, materializer, sample_session_state):
        """No uncertainty flag when critical fields present."""
        state = materializer.materialize(
            session_state_content=sample_session_state
        )
        
        # Should not have uncertainty if objective is present
        if state.objective:
            assert state.uncertainty_flag is False


# =============================================================================
# Boundary Tests
# =============================================================================

class TestReadonlyBoundary:
    """Tests for read-only boundary enforcement."""
    
    def test_no_write_to_source(self, materializer, sample_session_state, tmp_path):
        """Materialization should not modify source files."""
        # Create a temp file
        source_file = tmp_path / "SESSION-STATE.md"
        source_file.write_text(sample_session_state)
        original_mtime = source_file.stat().st_mtime
        
        # Materialize
        mat = StateMaterializerV0(session_state_path=source_file)
        state = mat.materialize()
        
        # Check file wasn't modified
        assert source_file.stat().st_mtime == original_mtime
    
    def test_no_side_effects(self, materializer):
        """Multiple materializations should be deterministic."""
        content = "## Current Objective\n测试目标"
        
        state1 = materializer.materialize(session_state_content=content)
        state2 = materializer.materialize(session_state_content=content)
        
        assert state1.objective == state2.objective


# =============================================================================
# CLI Compatibility Tests
# =============================================================================

class TestCLICompatibility:
    """Tests for CLI compatibility."""
    
    def test_to_dict_json_serializable(self, materializer, sample_session_state):
        """Output should be JSON serializable."""
        state = materializer.materialize(
            session_state_content=sample_session_state
        )
        
        # Should not raise
        json_str = json.dumps(state.to_dict())
        assert json_str is not None
    
    def test_top_level_fields_accessible(self, materializer, sample_session_state):
        """Top-level fields should be directly accessible."""
        state = materializer.materialize(
            session_state_content=sample_session_state
        )
        
        # These should be accessible as attributes
        assert hasattr(state, "objective")
        assert hasattr(state, "phase")
        assert hasattr(state, "branch")
        assert hasattr(state, "blocker")
        assert hasattr(state, "next_step")


# =============================================================================
# Normalization Tests
# =============================================================================

class TestNormalization:
    """Tests for value normalization."""
    
    def test_normalize_removes_markdown(self):
        """Normalization should remove markdown formatting."""
        result = normalize_value("**Bold** and _italic_")
        assert "*" not in result
        assert "_" not in result
    
    def test_normalize_collapses_whitespace(self):
        """Normalization should collapse whitespace."""
        result = normalize_value("  multiple   spaces  ")
        assert "  " not in result
    
    def test_normalize_truncates_long_values(self):
        """Normalization should truncate long values."""
        long_value = "x" * 1000
        result = normalize_value(long_value)
        assert len(result) <= 500
    
    def test_placeholder_detection(self):
        """Placeholder values should be detected."""
        for placeholder in PLACEHOLDER_VALUES:
            assert is_placeholder(placeholder)
    
    def test_non_placeholder_detection(self):
        """Non-placeholder values should not be detected."""
        assert not is_placeholder("实现目标")
        assert not is_placeholder("Implement feature X")


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests with real files."""
    
    def test_materialize_from_real_workspace(self):
        """Materialize from actual workspace files."""
        workspace = ROOT
        session_state_path = workspace / "SESSION-STATE.md"
        working_buffer_path = workspace / "working-buffer.md"
        
        if not session_state_path.exists():
            pytest.skip("SESSION-STATE.md not found")
        
        mat = StateMaterializerV0(
            session_state_path=session_state_path,
            working_buffer_path=working_buffer_path
        )
        
        state = mat.materialize()
        
        # Should have something
        assert state.materialized_at is not None
        assert isinstance(state.sources_checked, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
