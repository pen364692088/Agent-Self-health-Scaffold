"""
Contract Tests for Prompt Preview (Shadow Mode)

Tests verify:
1. Shadow mode boundary enforcement
2. Conflict handling (not silently included)
3. Missing blocker warning
4. Uncertainty flag propagation
5. Dual-run comparison correctness
6. Quality metrics assessment

Run with: pytest tests/core/test_prompt_preview.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add workspace to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.prompt_preview import (
    PromptLayer,
    PromptPreview,
    DualRunCompare,
    MaterializedStatePromptAssembler,
    DualRunComparator,
    create_shadow_prompt_preview,
    create_dual_run_compare,
    estimate_tokens,
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
        "field_sources": {
            "objective": {
                "session_state_md": {"status": "valid", "value": "Implement user authentication"}
            }
        },
        "field_resolutions": {
            "objective": {
                "status": "valid",
                "value": "Implement user authentication",
                "chosen_source": "session_state_md"
            },
            "phase": {
                "status": "valid",
                "value": "Implementing",
                "conflicts": [
                    {"source": "working_buffer_md", "value": "Development", "priority": 60}
                ]
            }
        }
    }


@pytest.fixture
def main_chain_output():
    """Sample prompt-assemble output."""
    return {
        "session_id": "test_session",
        "prompt_tokens": 5000,
        "max_tokens": 100000,
        "layers": {
            "resident": {
                "tokens": 2000,
                "components": ["task_goal", "open_loops", "hard_constraints"]
            },
            "active": {
                "tokens": 2500,
                "turns": [1, 2, 3, 4, 5, 6]
            },
            "recall": {
                "tokens": 500,
                "snippets": ["cap_001"]
            }
        },
        "compression_applied": False
    }


@pytest.fixture
def assembler():
    """Create a MaterializedStatePromptAssembler instance."""
    return MaterializedStatePromptAssembler()


@pytest.fixture
def comparator():
    """Create a DualRunComparator instance."""
    return DualRunComparator()


# =============================================================================
# Token Estimation Tests
# =============================================================================

class TestTokenEstimation:
    """Tests for token estimation."""
    
    def test_estimate_empty_string(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens("") == 0
    
    def test_estimate_short_string(self):
        """Short string should return at least 1 token."""
        assert estimate_tokens("ab") == 1
    
    def test_estimate_long_string(self):
        """Long string should return expected tokens."""
        text = "x" * 400  # 400 chars = 100 tokens
        assert estimate_tokens(text) == 100
    
    def test_estimate_unicode(self):
        """Unicode text should be handled."""
        text = "你好世界"  # 4 Chinese characters
        tokens = estimate_tokens(text)
        assert tokens > 0


# =============================================================================
# Prompt Assembly Tests
# =============================================================================

class TestPromptAssembly:
    """Tests for prompt assembly."""
    
    def test_assemble_basic(self, assembler, materialized_state):
        """Basic assembly should work."""
        preview = assembler.assemble(materialized_state)
        
        assert preview.prompt_tokens > 0
        assert "resident" in preview.layers
        assert "action" in preview.layers
    
    def test_objective_included(self, assembler, materialized_state):
        """Objective should be included in resident layer."""
        preview = assembler.assemble(materialized_state)
        
        assert "objective" in preview.layers["resident"].components
        assert preview.layers["resident"].data["objective"] == "Implement user authentication"
    
    def test_phase_included(self, assembler, materialized_state):
        """Phase should be included in resident layer."""
        preview = assembler.assemble(materialized_state)
        
        assert "phase" in preview.layers["resident"].components
    
    def test_next_step_in_action_layer(self, assembler, materialized_state):
        """Next step should be in action layer."""
        preview = assembler.assemble(materialized_state)
        
        assert "next_step" in preview.layers["action"].components
    
    def test_missing_blocker_warning(self, assembler, materialized_state):
        """Missing blocker should trigger warning."""
        preview = assembler.assemble(materialized_state)
        
        assert len(preview.warnings) > 0
        assert any("BLOCKER_MISSING" in w for w in preview.warnings)
    
    def test_no_missing_blocker_warning_when_disabled(self, materialized_state):
        """No warning when warn_on_missing_blocker is False."""
        assembler = MaterializedStatePromptAssembler(warn_on_missing_blocker=False)
        preview = assembler.assemble(materialized_state)
        
        assert not any("BLOCKER_MISSING" in w for w in preview.warnings)
    
    def test_uncertainty_flag_propagated(self, assembler):
        """Uncertainty flag should be propagated."""
        state = {
            "objective": "Test",
            "uncertainty_flag": True
        }
        preview = assembler.assemble(state)
        
        assert preview.uncertainty_flag is True
        assert any("UNCERTAINTY" in w for w in preview.warnings)


# =============================================================================
# Conflict Handling Tests
# =============================================================================

class TestConflictHandling:
    """Tests for conflict handling."""
    
    def test_conflicts_detected(self, assembler, materialized_state):
        """Conflicts should be detected."""
        preview = assembler.assemble(materialized_state)
        
        assert len(preview.conflicts) > 0
    
    def test_conflicts_not_included_by_default(self, assembler, materialized_state):
        """Conflicts should NOT be included in prompt by default."""
        preview = assembler.assemble(materialized_state)
        
        for conflict in preview.conflicts:
            assert conflict["included_in_prompt"] is False
    
    def test_conflicts_included_when_requested(self, materialized_state):
        """Conflicts CAN be included if explicitly requested."""
        assembler = MaterializedStatePromptAssembler(include_conflicts=True)
        preview = assembler.assemble(materialized_state)
        
        # Conflict info is tracked, but still separate from prompt content
        assert len(preview.conflicts) > 0
    
    def test_conflict_has_provenance(self, assembler, materialized_state):
        """Conflicts should have provenance info."""
        preview = assembler.assemble(materialized_state)
        
        for conflict in preview.conflicts:
            assert "field" in conflict
            assert "conflict_source" in conflict


# =============================================================================
# Shadow Mode Boundary Tests
# =============================================================================

class TestShadowModeBoundary:
    """Tests for shadow mode boundary enforcement."""
    
    def test_preview_is_read_only(self, assembler, materialized_state):
        """Preview should not modify input state."""
        original = dict(materialized_state)
        assembler.assemble(materialized_state)
        
        assert materialized_state == original
    
    def test_preview_has_no_authority(self, assembler, materialized_state):
        """Preview should not have authority flag."""
        preview = assembler.assemble(materialized_state)
        
        # No authority flag in output
        assert "authority" not in preview.to_dict()
    
    def test_preview_indicates_shadow_mode(self, assembler, materialized_state):
        """Preview should indicate it's shadow mode."""
        preview = assembler.assemble(materialized_state)
        preview_dict = preview.to_dict()
        
        # Has warnings and conflicts tracked separately
        assert "warnings" in preview_dict
        assert "conflicts" in preview_dict


# =============================================================================
# Dual-Run Comparison Tests
# =============================================================================

class TestDualRunComparison:
    """Tests for dual-run comparison."""
    
    def test_compare_basic(self, comparator, main_chain_output, materialized_state):
        """Basic comparison should work."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        assert compare.generated_at is not None
        assert compare.comparison is not None
    
    def test_token_comparison(self, comparator, main_chain_output, materialized_state):
        """Token comparison should be correct."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        assert "token_usage" in compare.comparison
        assert compare.comparison["token_usage"]["main_chain_tokens"] == 5000
        assert compare.comparison["token_usage"]["shadow_preview_tokens"] > 0
    
    def test_layer_coverage_comparison(self, comparator, main_chain_output, materialized_state):
        """Layer coverage should be compared."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        assert "layer_coverage" in compare.comparison
        assert "common_layers" in compare.comparison["layer_coverage"]
    
    def test_quality_metrics_present(self, comparator, main_chain_output, materialized_state):
        """Quality metrics should be present."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        assert "completeness" in compare.quality_metrics
        assert "consistency" in compare.quality_metrics
        assert "observability" in compare.quality_metrics
    
    def test_recommendations_generated(self, comparator, main_chain_output, materialized_state):
        """Recommendations should be generated."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        assert isinstance(compare.recommendations, list)
    
    def test_warning_in_recommendations(self, comparator, main_chain_output, materialized_state):
        """Warnings should appear in recommendations."""
        preview = create_shadow_prompt_preview(materialized_state)
        compare = comparator.compare(main_chain_output, preview)
        
        # Missing blocker should trigger recommendation
        assert len(compare.recommendations) > 0


# =============================================================================
# Quality Metrics Tests
# =============================================================================

class TestQualityMetrics:
    """Tests for quality metrics assessment."""
    
    def test_completeness_score(self, comparator, materialized_state):
        """Completeness score should be calculated."""
        preview = create_shadow_prompt_preview(materialized_state)
        metrics = comparator._assess_completeness(preview)
        
        assert "score" in metrics
        assert 0 <= metrics["score"] <= 1
    
    def test_completeness_missing_fields(self, comparator):
        """Missing fields should reduce completeness."""
        state = {"objective": "Test"}  # Missing phase, next_step
        preview = create_shadow_prompt_preview(state)
        metrics = comparator._assess_completeness(preview)
        
        assert metrics["score"] < 1
        assert len(metrics["missing"]) > 0
    
    def test_consistency_assessment(self, comparator, main_chain_output, materialized_state):
        """Consistency should be assessed."""
        preview = create_shadow_prompt_preview(materialized_state)
        metrics = comparator._assess_consistency(main_chain_output, preview.to_dict())
        
        assert "consistent" in metrics
        assert "token_ratio" in metrics
    
    def test_observability_assessment(self, comparator, materialized_state):
        """Observability should be assessed."""
        preview = create_shadow_prompt_preview(materialized_state)
        metrics = comparator._assess_observability(preview)
        
        assert "has_warnings" in metrics
        assert "has_conflicts" in metrics


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_shadow_prompt_preview(self, materialized_state):
        """Convenience function should create preview."""
        preview = create_shadow_prompt_preview(materialized_state)
        
        assert isinstance(preview, PromptPreview)
    
    def test_create_dual_run_compare(self, main_chain_output, materialized_state):
        """Convenience function should create comparison."""
        compare = create_dual_run_compare(main_chain_output, materialized_state)
        
        assert isinstance(compare, DualRunCompare)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests with real MaterializedState."""
    
    def test_with_real_workspace(self):
        """Test with real workspace."""
        workspace = ROOT
        
        # Load real SESSION-STATE.md
        session_state_path = workspace / "SESSION-STATE.md"
        if not session_state_path.exists():
            pytest.skip("SESSION-STATE.md not found")
        
        # Import materialize function
        from core.materialized_state_v0 import materialize_state
        
        # Materialize state
        state = materialize_state(workspace_path=workspace)
        state_dict = state.to_dict()
        
        # Create preview
        preview = create_shadow_prompt_preview(state_dict)
        
        assert preview.prompt_tokens > 0
        assert len(preview.layers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
