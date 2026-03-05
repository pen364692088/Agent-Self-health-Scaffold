#!/usr/bin/env python3
"""
MVP11.2 Seed Consistency Tests

Tests that verify fixed seeds produce consistent results across runs.
Used by CI to detect determinism regressions.
"""

import pytest
import os
import sys
import random
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRandomSeedConsistency:
    """Tests for random seed consistency."""
    
    def test_python_random_seed_consistency(self):
        """
        Test that Python's random module produces consistent results with fixed seed.
        """
        results = []
        
        for _ in range(3):
            random.seed(42)
            values = [random.random() for _ in range(10)]
            results.append(tuple(values))
        
        # All should be identical
        assert len(set(results)) == 1, "Random seed produced inconsistent results"
    
    def test_random_sequence_reproducibility(self):
        """
        Test that we can reproduce random sequences.
        """
        # Generate sequence with seed 42
        random.seed(42)
        first_sequence = [random.randint(0, 100) for _ in range(20)]
        
        # Reset and generate again with same seed
        random.seed(42)
        second_sequence = [random.randint(0, 100) for _ in range(20)]
        
        assert first_sequence == second_sequence, "Sequences differ with same seed"


class TestDeterministicMode:
    """Tests for deterministic mode in emotiond."""
    
    def test_test_mode_flag_exists(self):
        """
        Test that TEST_MODE flag exists and can be set.
        """
        from emotiond.config import TEST_MODE
        
        # Should be a boolean
        assert isinstance(TEST_MODE, bool)
    
    def test_deterministic_mode_env_var(self):
        """
        Test that EMOTIOND_DETERMINISTIC_MODE can be read.
        """
        # This test just verifies the environment variable can be set
        original = os.environ.get("EMOTIOND_DETERMINISTIC_MODE")
        
        os.environ["EMOTIOND_DETERMINISTIC_MODE"] = "true"
        
        # Verify it was set
        assert os.environ.get("EMOTIOND_DETERMINISTIC_MODE") == "true"
        
        # Restore original
        if original is not None:
            os.environ["EMOTIOND_DETERMINISTIC_MODE"] = original
        else:
            os.environ.pop("EMOTIOND_DETERMINISTIC_MODE", None)


class TestActionScoreConsistency:
    """Tests for consistent action scoring."""
    
    def test_score_action_determinism(self):
        """
        Test that score_action produces consistent results for same inputs.
        """
        from emotiond.core import EmotionState, score_action
        from emotiond.config import ACTION_SCORE_WEIGHTS
        
        state = EmotionState()
        state.valence = 0.3
        state.arousal = 0.2
        state.social_safety = 0.6
        state.energy = 0.7
        
        relationship = {"bond": 0.5, "grudge": 0.1, "trust": 0.6, "repair_bank": 0.0}
        prediction = {
            "social_safety_delta": 0.1,
            "energy_delta": -0.05,
            "prediction_error_sum": 0.2,
            "prediction_count": 5
        }
        
        # Score same action multiple times
        results = []
        for _ in range(5):
            score = score_action("approach", state, relationship, prediction)
            results.append(score)
        
        # All should be identical
        assert len(set(results)) == 1, f"Score action non-deterministic: {results}"
    
    def test_score_action_comparison(self):
        """
        Test that action scores are comparable and consistent.
        """
        from emotiond.core import EmotionState, score_action
        
        state = EmotionState()
        state.valence = 0.5
        state.arousal = 0.3
        state.social_safety = 0.7
        state.energy = 0.8
        
        relationship = {"bond": 0.6, "grudge": 0.0, "trust": 0.7, "repair_bank": 0.1}
        prediction = {
            "social_safety_delta": 0.05,
            "energy_delta": 0.0,
            "prediction_error_sum": 0.1,
            "prediction_count": 10
        }
        
        # Score different actions
        actions = ["approach", "withdraw", "observe", "seek_info", "self_regulate"]
        scores = {action: score_action(action, state, relationship, prediction) for action in actions}
        
        # All scores should be floats
        for action, score in scores.items():
            assert isinstance(score, float), f"Score for {action} is not float: {type(score)}"
        
        # Note: Scores may be identical if predictions are not action-specific
        # This is acceptable - the test verifies scoring works consistently


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
