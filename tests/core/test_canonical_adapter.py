"""
Contract Tests for Canonical Adapter (Shadow Mode)

Tests verify:
1. Read-only boundary enforcement
2. Shadow comparison correctness
3. Conflict detection
4. Coverage reporting
5. Provenance tracking
6. No modification of canonical sources

Run with: pytest tests/core/test_canonical_adapter.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add workspace to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.canonical_adapter import (
    CanonicalAdapter,
    CanonicalSource,
    CanonicalField,
    FieldComparison,
    ShadowCompareReport,
    create_shadow_report,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create run_state
        state_dir = workspace / "state" / "durable_execution"
        state_dir.mkdir(parents=True)
        run_state = {
            "version": 1,
            "updated_at": datetime.now().isoformat(),
            "objective": "Canonical Objective",
            "status": "running",
            "hard_block": False,
            "next_step": "Run tests",
            "resume_action": "continue"
        }
        (state_dir / "RUN_STATE.json").write_text(json.dumps(run_state))
        
        # Create task ledger
        ledger_path = workspace / "TASK_LEDGER.jsonl"
        entries = [
            {"task_id": "task_001", "state": "completed", "ts": datetime.now().isoformat()},
            {"task_id": "task_002", "state": "running", "ts": datetime.now().isoformat()},
        ]
        with ledger_path.open("w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        
        # Create run ledger dir
        run_ledger_dir = workspace / "artifacts" / "run_ledger"
        run_ledger_dir.mkdir(parents=True)
        
        yield workspace


@pytest.fixture
def bridge_state():
    """Sample bridge state (from MaterializedState)."""
    return {
        "objective": "Bridge Objective",
        "phase": "Implementing",
        "branch": "main",
        "blocker": None,
        "next_step": "Continue implementation",
        "uncertainty_flag": False,
        "field_resolutions": {
            "objective": {"chosen_source": "session_state_md", "value": "Bridge Objective"},
            "phase": {"chosen_source": "session_state_md", "value": "Implementing"},
            "next_step": {"chosen_source": "session_state_md", "value": "Continue implementation"}
        },
        "field_sources": {
            "objective": {"session_state_md": {"value": "Bridge Objective", "status": "valid"}}
        }
    }


@pytest.fixture
def adapter(temp_workspace):
    """Create a CanonicalAdapter instance."""
    return CanonicalAdapter(workspace_path=temp_workspace)


# =============================================================================
# Read-Only Boundary Tests
# =============================================================================

class TestReadonlyBoundary:
    """Tests for read-only boundary enforcement."""
    
    def test_connect_does_not_modify(self, adapter):
        """Connect should not modify any files."""
        # Get file mtimes before
        run_state_path = adapter.run_state_path
        mtime_before = run_state_path.stat().st_mtime if run_state_path.exists() else None
        
        adapter.connect()
        
        # Check file mtimes after
        if mtime_before:
            mtime_after = run_state_path.stat().st_mtime
            assert mtime_after == mtime_before
    
    def test_read_run_state_does_not_modify(self, adapter):
        """Reading run state should not modify the file."""
        adapter.connect()
        
        run_state_path = adapter.run_state_path
        content_before = run_state_path.read_text()
        
        adapter.read_run_state()
        
        content_after = run_state_path.read_text()
        assert content_before == content_after
    
    def test_read_task_ledger_does_not_modify(self, adapter):
        """Reading task ledger should not modify the file."""
        adapter.connect()
        
        ledger_path = adapter.task_ledger_path
        content_before = ledger_path.read_text()
        
        adapter.read_task_ledger()
        
        content_after = ledger_path.read_text()
        assert content_before == content_after
    
    def test_shadow_compare_does_not_modify(self, adapter, bridge_state):
        """Shadow compare should not modify any files."""
        adapter.connect()
        
        run_state_path = adapter.run_state_path
        mtime_before = run_state_path.stat().st_mtime
        
        adapter.shadow_compare(bridge_state)
        
        mtime_after = run_state_path.stat().st_mtime
        assert mtime_after == mtime_before


# =============================================================================
# Connection Tests
# =============================================================================

class TestConnection:
    """Tests for adapter connection."""
    
    def test_connect_returns_true_when_source_exists(self, adapter):
        """Connect should return True when at least one source exists."""
        result = adapter.connect()
        assert result is True
    
    def test_connect_returns_false_when_no_sources(self):
        """Connect should return False when no sources exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CanonicalAdapter(workspace_path=Path(tmpdir))
            result = adapter.connect()
            assert result is False
    
    def test_sources_populated_after_connect(self, adapter):
        """Sources should be populated after connect."""
        adapter.connect()
        sources = adapter.get_sources()
        
        assert "task_ledger" in sources
        assert "run_state" in sources
        assert "run_ledger_dir" in sources
    
    def test_is_connected_reflects_state(self, adapter):
        """is_connected should reflect connection state."""
        assert adapter.is_connected() is False
        adapter.connect()
        assert adapter.is_connected() is True


# =============================================================================
# Field Extraction Tests
# =============================================================================

class TestFieldExtraction:
    """Tests for canonical field extraction."""
    
    def test_extract_objective_from_run_state(self, adapter):
        """Should extract objective from run_state."""
        adapter.connect()
        fields = adapter.extract_canonical_fields()
        
        assert "objective" in fields
        assert fields["objective"].value == "Canonical Objective"
        assert fields["objective"].source == "run_state"
    
    def test_extract_status_from_run_state(self, adapter):
        """Should extract status from run_state."""
        adapter.connect()
        fields = adapter.extract_canonical_fields()
        
        assert "status" in fields
        assert fields["status"].value == "running"
    
    def test_extract_next_step_from_run_state(self, adapter):
        """Should extract next_step from run_state."""
        adapter.connect()
        fields = adapter.extract_canonical_fields()
        
        assert "next_step" in fields
        assert fields["next_step"].value == "Run tests"
    
    def test_extract_task_from_ledger(self, adapter):
        """Should extract latest task from ledger."""
        adapter.connect()
        fields = adapter.extract_canonical_fields()
        
        assert "latest_task_id" in fields
        assert fields["latest_task_id"].value == "task_002"


# =============================================================================
# Shadow Comparison Tests
# =============================================================================

class TestShadowComparison:
    """Tests for shadow comparison."""
    
    def test_detects_value_mismatch(self, adapter, bridge_state):
        """Should detect value mismatches."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        # Objective should mismatch
        assert report.field_comparisons["objective"].match is False
        assert report.field_comparisons["objective"].conflict_type == "value_mismatch"
    
    def test_detects_match(self, temp_workspace):
        """Should detect matching values."""
        # Create adapter with matching state
        bridge_state = {
            "objective": "Canonical Objective",  # Matches canonical
            "phase": "running",
            "field_resolutions": {"objective": {"chosen_source": "bridge"}},
            "field_sources": {}
        }
        
        adapter = CanonicalAdapter(workspace_path=temp_workspace)
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        assert report.field_comparisons["objective"].match is True
    
    def test_detects_canonical_missing(self, bridge_state):
        """Should detect when canonical is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty workspace - no canonical sources
            adapter = CanonicalAdapter(workspace_path=Path(tmpdir))
            adapter.connect()
            
            report = adapter.shadow_compare(bridge_state)
            
            # All fields should have canonical_missing
            for comp in report.field_comparisons.values():
                if comp.bridge_value:
                    assert comp.conflict_type in ["canonical_missing", None]
    
    def test_detects_bridge_missing(self, temp_workspace):
        """Should detect when bridge is missing."""
        bridge_state = {
            "objective": None,
            "phase": None,
            "next_step": None,
            "field_resolutions": {},
            "field_sources": {}
        }
        
        adapter = CanonicalAdapter(workspace_path=temp_workspace)
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        # Should have fallbacks available
        assert len(report.fallbacks) > 0
    
    def test_provenance_preserved(self, adapter, bridge_state):
        """Should preserve provenance in comparisons."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        for comp in report.field_comparisons.values():
            assert "bridge_raw" in comp.provenance
            assert "canonical_raw" in comp.provenance


# =============================================================================
# Coverage Reporting Tests
# =============================================================================

class TestCoverageReporting:
    """Tests for coverage reporting."""
    
    def test_coverage_counts(self, adapter, bridge_state):
        """Should correctly count coverage."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        total = (
            len(report.coverage["bridge_only"]) +
            len(report.coverage["canonical_only"]) +
            len(report.coverage["both"]) +
            len(report.coverage["neither"])
        )
        
        # Should equal number of comparable fields
        assert total == 5  # objective, phase, status, blocker, next_step
    
    def test_summary_contains_key_metrics(self, adapter, bridge_state):
        """Summary should contain key metrics."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        assert "total_fields_compared" in report.summary
        assert "matches" in report.summary
        assert "conflicts" in report.summary
        assert "bridge_coverage" in report.summary
        assert "canonical_coverage" in report.summary


# =============================================================================
# Conflict Detection Tests
# =============================================================================

class TestConflictDetection:
    """Tests for conflict detection."""
    
    def test_conflicts_list_populated(self, adapter, bridge_state):
        """Should populate conflicts list."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        # Should have at least one conflict (objective)
        assert len(report.conflicts) > 0
    
    def test_conflict_contains_field_info(self, adapter, bridge_state):
        """Conflict should contain field info."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        if report.conflicts:
            conflict = report.conflicts[0]
            assert "field" in conflict
            assert "bridge_value" in conflict
            assert "canonical_value" in conflict
    
    def test_warnings_generated(self, adapter, bridge_state):
        """Should generate warnings."""
        adapter.connect()
        report = adapter.shadow_compare(bridge_state)
        
        # Should have warnings about conflicts
        assert len(report.warnings) > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests with real workspace."""
    
    def test_with_real_workspace(self):
        """Test with real workspace files."""
        workspace = ROOT
        adapter = CanonicalAdapter(workspace_path=workspace)
        
        if not adapter.connect():
            pytest.skip("No canonical sources in real workspace")
        
        # Should be able to extract fields
        fields = adapter.extract_canonical_fields()
        assert isinstance(fields, dict)
    
    def test_shadow_compare_with_real_workspace(self):
        """Shadow compare with real workspace."""
        workspace = ROOT
        adapter = CanonicalAdapter(workspace_path=workspace)
        
        if not adapter.connect():
            pytest.skip("No canonical sources in real workspace")
        
        bridge_state = {
            "objective": "Test objective",
            "phase": "Testing",
            "next_step": "Run tests",
            "field_resolutions": {},
            "field_sources": {}
        }
        
        report = adapter.shadow_compare(bridge_state)
        
        assert isinstance(report, ShadowCompareReport)
        assert report.generated_at is not None


# =============================================================================
# Merge Stub Tests
# =============================================================================

class TestMergeStub:
    """Tests for merge_with_canonical stub."""
    
    def test_merge_returns_unchanged(self, adapter, bridge_state):
        """Merge should return bridge_state unchanged in v0."""
        adapter.connect()
        result = adapter.merge_with_canonical(bridge_state)
        
        assert result == bridge_state


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunction:
    """Tests for create_shadow_report convenience function."""
    
    def test_creates_report(self, temp_workspace, bridge_state):
        """Should create a shadow report."""
        report = create_shadow_report(bridge_state, workspace_path=temp_workspace)
        
        assert isinstance(report, ShadowCompareReport)
        assert report.generated_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
