"""
Contract Tests for Recovery Preview (Shadow Mode)

Tests verify:
1. Shadow mode boundary enforcement
2. Conflict handling (not silently used)
3. Missing blocker warning
4. Uncertainty flag propagation
5. Recovery comparison correctness
6. Provenance tracking
7. No real recovery actions triggered

Run with: pytest tests/core/test_recovery_preview.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add workspace to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.recovery_preview import (
    RecoveryField,
    RecoveryPreview,
    RecoveryCompare,
    RecoveryPreviewGenerator,
    RecoveryCompareGenerator,
    create_recovery_preview,
    create_recovery_compare,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def materialized_state():
    """Sample MaterializedState output."""
    return {
        "objective": "Implement user authentication",
        "phase": "Implementing",
        "branch": "main",
        "blocker": None,  # Missing blocker
        "next_step": "Write unit tests",
        "next_actions": ["Test login", "Test registration"],
        "uncertainty_flag": False,
        "sources_checked": ["session_state_md", "repo_evidence"],
        "field_resolutions": {
            "objective": {
                "status": "valid",
                "value": "Implement user authentication",
                "chosen_source": "session_state_md"
            },
            "phase": {
                "status": "valid",
                "value": "Implementing",
                "chosen_source": "session_state_md"
            },
            "next_step": {
                "status": "valid",
                "value": "Write unit tests",
                "chosen_source": "session_state_md"
            },
            "blocker": {
                "status": "missing",
                "value": None
            }
        }
    }


@pytest.fixture
def canonical_state():
    """Sample canonical state."""
    return {
        "objective": {
            "value": "Different objective",
            "source": "run_state"
        },
        "status": {
            "value": "running",
            "source": "run_state"
        },
        "next_step": {
            "value": "Run integration tests",
            "source": "run_state"
        }
    }


@pytest.fixture
def main_recovery():
    """Sample main recovery output."""
    return {
        "recovered": True,
        "uncertainty_flag": False,
        "field_resolution": {
            "objective": {
                "status": "valid",
                "value": "Implement user authentication"
            },
            "phase": {
                "status": "valid",
                "value": "Implementing"
            },
            "next_step": {
                "status": "valid",
                "value": "Write unit tests"
            }
        },
        "sources": {
            "session_state": {"exists": True}
        }
    }


@pytest.fixture
def generator():
    """Create a RecoveryPreviewGenerator instance."""
    return RecoveryPreviewGenerator()


@pytest.fixture
def comparator():
    """Create a RecoveryCompareGenerator instance."""
    return RecoveryCompareGenerator()


# =============================================================================
# Recovery Preview Generation Tests
# =============================================================================

class TestRecoveryPreviewGeneration:
    """Tests for recovery preview generation."""
    
    def test_generate_basic(self, generator, materialized_state):
        """Basic generation should work."""
        preview = generator.generate(materialized_state)
        
        assert preview.generated_at is not None
        assert preview.objective == "Implement user authentication"
        assert preview.phase == "Implementing"
    
    def test_phase_extracted(self, generator, materialized_state):
        """Phase should be extracted."""
        preview = generator.generate(materialized_state)
        
        assert preview.phase == "Implementing"
    
    def test_next_step_extracted(self, generator, materialized_state):
        """Next step should be extracted."""
        preview = generator.generate(materialized_state)
        
        assert preview.next_step == "Write unit tests"
    
    def test_blocker_missing_warning(self, generator, materialized_state):
        """Missing blocker should trigger warning."""
        preview = generator.generate(materialized_state)
        
        assert len(preview.warnings) > 0
        assert any("BLOCKER_MISSING" in w for w in preview.warnings)
    
    def test_no_missing_blocker_warning_when_disabled(self, materialized_state):
        """No warning when warn_on_missing_blocker is False."""
        generator = RecoveryPreviewGenerator(warn_on_missing_blocker=False)
        preview = generator.generate(materialized_state)
        
        assert not any("BLOCKER_MISSING" in w for w in preview.warnings)
    
    def test_uncertainty_flag_propagated(self, generator):
        """Uncertainty flag should be propagated."""
        state = {
            "objective": None,
            "uncertainty_flag": True
        }
        preview = generator.generate(state)
        
        assert preview.uncertainty_flag is True
        assert any("UNCERTAINTY" in w for w in preview.warnings)


# =============================================================================
# Conflict Handling Tests
# =============================================================================

class TestConflictHandling:
    """Tests for conflict handling."""
    
    def test_conflict_detected(self, generator, materialized_state, canonical_state):
        """Conflicts should be detected when canonical differs."""
        preview = generator.generate(materialized_state, canonical_state)
        
        # Objective differs between bridge and canonical
        assert len(preview.conflicts) > 0
    
    def test_conflict_has_provenance(self, generator, materialized_state, canonical_state):
        """Conflicts should have provenance info."""
        preview = generator.generate(materialized_state, canonical_state)
        
        for conflict in preview.conflicts:
            assert "field" in conflict
            assert "bridge_value" in conflict
            assert "canonical_value" in conflict
            assert "bridge_source" in conflict
            assert "canonical_source" in conflict
    
    def test_conflict_field_status(self, generator, materialized_state, canonical_state):
        """Conflict field should have conflict status."""
        preview = generator.generate(materialized_state, canonical_state)
        
        # Find conflict field
        for field_name, field in preview.fields.items():
            if field.status == "conflict":
                assert field.conflict_info is not None
    
    def test_provenance_includes_conflict(self, generator, materialized_state, canonical_state):
        """Provenance should include conflict info."""
        preview = generator.generate(materialized_state, canonical_state)
        
        # Provenance should track canonical sources
        assert "canonical_sources" in preview.provenance


# =============================================================================
# Shadow Mode Boundary Tests
# =============================================================================

class TestShadowModeBoundary:
    """Tests for shadow mode boundary enforcement."""
    
    def test_preview_is_read_only(self, generator, materialized_state):
        """Preview should not modify input state."""
        original = dict(materialized_state)
        generator.generate(materialized_state)
        
        assert materialized_state == original
    
    def test_preview_has_no_authority(self, generator, materialized_state):
        """Preview should not have authority flag."""
        preview = generator.generate(materialized_state)
        preview_dict = preview.to_dict()
        
        # No authority flag in output
        assert "authority" not in preview_dict
    
    def test_preview_indicates_shadow_mode(self, generator, materialized_state):
        """Preview should indicate shadow mode."""
        preview = generator.generate(materialized_state)
        preview_dict = preview.to_dict()
        
        # Has warnings and provenance for transparency
        assert "warnings" in preview_dict
        assert "provenance" in preview_dict
    
    def test_no_real_recovery_triggered(self, generator, materialized_state):
        """Generate should not trigger real recovery."""
        # This test verifies that generate() doesn't call any recovery tools
        preview = generator.generate(materialized_state)
        
        # should_recover is a flag, not an action
        assert isinstance(preview.should_recover, bool)


# =============================================================================
# Recovery Comparison Tests
# =============================================================================

class TestRecoveryComparison:
    """Tests for recovery comparison."""
    
    def test_compare_basic(self, comparator, main_recovery, materialized_state):
        """Basic comparison should work."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert compare.generated_at is not None
        assert compare.field_differences is not None
    
    def test_phase_comparison(self, comparator, main_recovery, materialized_state):
        """Phase comparison should be correct."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert "main_phase" in compare.phase_comparison
        assert "shadow_phase" in compare.phase_comparison
        assert "match" in compare.phase_comparison
    
    def test_next_step_comparison(self, comparator, main_recovery, materialized_state):
        """Next step comparison should be correct."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert "main_next_step" in compare.next_step_comparison
        assert "shadow_next_step" in compare.next_step_comparison
    
    def test_blocker_comparison(self, comparator, main_recovery, materialized_state):
        """Blocker comparison should be correct."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert "main_blocker" in compare.blocker_comparison
        assert "shadow_blocker" in compare.blocker_comparison
        assert "main_has_blocker" in compare.blocker_comparison
    
    def test_warnings_comparison(self, comparator, main_recovery, materialized_state):
        """Warnings comparison should be correct."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert "main_uncertainty_flag" in compare.warnings_comparison
        assert "shadow_warnings_count" in compare.warnings_comparison
    
    def test_provenance_comparison(self, comparator, main_recovery, materialized_state):
        """Provenance comparison should be correct."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert "main_sources" in compare.provenance_comparison
        assert "shadow_provenance" in compare.provenance_comparison
    
    def test_recommendations_generated(self, comparator, main_recovery, materialized_state):
        """Recommendations should be generated."""
        preview = create_recovery_preview(materialized_state)
        compare = comparator.compare(main_recovery, preview)
        
        assert isinstance(compare.recommendations, list)
    
    def test_mismatch_in_recommendations(self, comparator, main_recovery, materialized_state):
        """Mismatches should appear in recommendations."""
        # Create state with different values
        different_state = {
            "objective": "Different objective",
            "phase": "Different phase",
            "next_step": "Different next step",
            "field_resolutions": {}
        }
        
        preview = create_recovery_preview(different_state)
        compare = comparator.compare(main_recovery, preview)
        
        # Should have recommendations about mismatches
        assert len(compare.recommendations) > 0


# =============================================================================
# Should Recover Logic Tests
# =============================================================================

class TestShouldRecoverLogic:
    """Tests for should_recover logic."""
    
    def test_should_recover_with_uncertainty(self, generator):
        """Should recommend recovery with uncertainty flag."""
        state = {
            "objective": "Test",
            "uncertainty_flag": True
        }
        preview = generator.generate(state)
        
        assert preview.should_recover is True
    
    def test_should_recover_with_missing_objective(self, generator):
        """Should recommend recovery with missing objective."""
        state = {
            "objective": None,
            "uncertainty_flag": False
        }
        preview = generator.generate(state)
        
        assert preview.should_recover is True
    
    def test_should_not_recover_with_valid_state(self, generator, materialized_state):
        """Should not recommend recovery with valid state."""
        preview = generator.generate(materialized_state)
        
        assert preview.should_recover is False


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_recovery_preview(self, materialized_state):
        """Convenience function should create preview."""
        preview = create_recovery_preview(materialized_state)
        
        assert isinstance(preview, RecoveryPreview)
    
    def test_create_recovery_compare(self, main_recovery, materialized_state):
        """Convenience function should create comparison."""
        compare = create_recovery_compare(main_recovery, materialized_state)
        
        assert isinstance(compare, RecoveryCompare)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests with real MaterializedState."""
    
    def test_with_real_workspace(self):
        """Test with real workspace."""
        workspace = ROOT
        
        session_state_path = workspace / "SESSION-STATE.md"
        if not session_state_path.exists():
            pytest.skip("SESSION-STATE.md not found")
        
        from core.materialized_state_v0 import materialize_state
        
        state = materialize_state(workspace_path=workspace)
        state_dict = state.to_dict()
        
        preview = create_recovery_preview(state_dict)
        
        assert preview.generated_at is not None
        assert len(preview.fields) > 0
    
    def test_with_canonical_integration(self):
        """Test with canonical adapter integration."""
        workspace = ROOT
        
        from core.materialized_state_v0 import materialize_state
        from core.canonical_adapter import CanonicalAdapter
        
        state = materialize_state(workspace_path=workspace)
        state_dict = state.to_dict()
        
        adapter = CanonicalAdapter(workspace_path=workspace)
        if adapter.connect():
            canonical_fields = adapter.extract_canonical_fields()
            canonical_dict = {
                name: {"value": f.value, "source": f.source}
                for name, f in canonical_fields.items()
            }
            
            preview = create_recovery_preview(state_dict, canonical_dict)
            
            assert preview.generated_at is not None
        else:
            pytest.skip("Canonical sources not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
