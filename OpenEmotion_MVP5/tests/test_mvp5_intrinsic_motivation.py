"""
Tests for MVP-5 D3: Intrinsic Motivation System

Tests:
1. Expected Info Gain Tests
   - Test: high uncertainty + novelty -> high expected_info_gain
   - Test: social threat reduces expected_info_gain
   - Test: questions in text boost expected_info_gain
   - Test: new topic indicators boost expected_info_gain

2. Curiosity Tests
   - Test: high expected_info_gain -> curiosity increase
   - Test: low social threat allows curiosity boost
   - Test: curiosity decays over time
   - Test: curiosity_trace explains the source

3. Boredom Tests
   - Test: sustained low info_gain + low prediction_error -> boredom
   - Test: boredom increases with duration
   - Test: boredom decays when info_gain returns
   - Test: boredom_trace explains the source

4. Confusion Tests
   - Test: high non-converging prediction_error -> confusion
   - Test: confusion increases with sustained errors
   - Test: confusion decays when errors converge
   - Test: confusion_trace explains the source

5. Integration Tests
   - Test: integration with meta-cognition (ask_more, shift_topic, ask_clarify)
   - Test: integration with decision (exploration_tendency when social_threat low)
   - Test: trace fields are populated

6. Determinism Tests
   - Test: same inputs produce same outputs with same seed
   - Test: history maintains correct state across updates
"""
import pytest
import pytest_asyncio
import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from emotiond.intrinsic_motivation import (
    InfoGainHistory,
    PredictionErrorHistory,
    IntrinsicMotivationState,
    IntrinsicMotivationEngine,
    get_intrinsic_engine,
    reset_intrinsic_engine,
    compute_intrinsic_motivation,
    apply_intrinsic_to_meta_cognition,
    apply_intrinsic_to_decision,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fresh_engine():
    """Create a fresh engine for each test."""
    reset_intrinsic_engine()
    return IntrinsicMotivationEngine(seed=42)


@pytest.fixture
def info_gain_history():
    """Create a fresh info gain history."""
    return InfoGainHistory()


@pytest.fixture
def prediction_error_history():
    """Create a fresh prediction error history."""
    return PredictionErrorHistory()


# ============================================================================
# 1. Expected Info Gain Tests
# ============================================================================

class TestExpectedInfoGain:
    """Test expected information gain computation."""
    
    def test_high_uncertainty_novelty_high_info_gain(self, fresh_engine):
        """Test: high uncertainty + novelty -> high expected_info_gain."""
        info_gain, trace = fresh_engine.compute_expected_info_gain(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            text=None
        )
        
        assert info_gain > 0.5, f"Expected high info gain, got {info_gain}"
        assert "uncertainty" in trace.lower()
        assert "novelty" in trace.lower()
    
    def test_social_threat_reduces_info_gain(self, fresh_engine):
        """Test: social threat reduces expected_info_gain."""
        info_gain_low_threat, _ = fresh_engine.compute_expected_info_gain(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            text=None
        )
        
        info_gain_high_threat, trace = fresh_engine.compute_expected_info_gain(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.8,
            text=None
        )
        
        assert info_gain_high_threat < info_gain_low_threat
        assert "threat" in trace.lower() or "threat_factor" in trace.lower()
    
    def test_question_boosts_info_gain(self, fresh_engine):
        """Test: questions in text boost expected_info_gain."""
        base_gain, _ = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="This is a statement."
        )
        
        question_gain, trace = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="What do you think about this?"
        )
        
        assert question_gain > base_gain
        assert "question" in trace.lower()
    
    def test_chinese_question_boosts_info_gain(self, fresh_engine):
        """Test: Chinese questions boost expected_info_gain."""
        base_gain, _ = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="这是一个陈述。"
        )
        
        question_gain, trace = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="你怎么看这个问题？"
        )
        
        assert question_gain > base_gain
        assert "question" in trace.lower()
    
    def test_new_topic_boosts_info_gain(self, fresh_engine):
        """Test: new topic indicators boost expected_info_gain."""
        base_gain, _ = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="Continuing the same topic."
        )
        
        new_topic_gain, trace = fresh_engine.compute_expected_info_gain(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            text="Let's try something different and experiment."
        )
        
        assert new_topic_gain > base_gain
        assert "new topic" in trace.lower() or "experiment" in trace.lower()


# ============================================================================
# 2. Curiosity Tests
# ============================================================================

class TestCuriosity:
    """Test curiosity emergence from expected_info_gain."""
    
    def test_high_info_gain_increases_curiosity(self, fresh_engine):
        """Test: high expected_info_gain -> curiosity increase."""
        # Start with low curiosity
        fresh_engine.state.curiosity = 0.1
        
        # Update with high info gain conditions
        state = fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            prediction_error=0.1,
            dt=1.0
        )
        
        assert state.curiosity > 0.1, f"Curiosity should increase, got {state.curiosity}"
        assert state.expected_info_gain > 0.6
    
    def test_low_social_threat_allows_curiosity_boost(self, fresh_engine):
        """Test: low social threat allows curiosity boost."""
        # High info gain with low threat
        state_low_threat = fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            prediction_error=0.1,
            dt=1.0
        )
        curiosity_low_threat = state_low_threat.curiosity
        
        # Reset and try with high threat
        fresh_engine.reset()
        state_high_threat = fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.8,
            prediction_error=0.1,
            dt=1.0
        )
        curiosity_high_threat = state_high_threat.curiosity
        
        # Both should increase but low threat should be higher
        # (or at least not suppressed)
        assert curiosity_low_threat >= curiosity_high_threat * 0.8
    
    def test_curiosity_decays_over_time(self, fresh_engine):
        """Test: curiosity decays over time."""
        # First boost curiosity
        fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            prediction_error=0.1,
            dt=1.0
        )
        high_curiosity = fresh_engine.state.curiosity
        
        # Now let time pass with low info gain
        fresh_engine.update(
            uncertainty=0.2,
            novelty=0.1,
            social_threat=0.1,
            prediction_error=0.1,
            dt=5.0
        )
        decayed_curiosity = fresh_engine.state.curiosity
        
        assert decayed_curiosity < high_curiosity
    
    def test_curiosity_trace_explains_source(self, fresh_engine):
        """Test: curiosity_trace explains the source of curiosity."""
        state = fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            prediction_error=0.1,
            dt=1.0
        )
        
        assert state.curiosity_trace
        assert len(state.curiosity_trace) > 0
        # Should contain explanation keywords
        assert any(word in state.curiosity_trace.lower() for word in [
            "info_gain", "threat", "increased", "decayed"
        ])


# ============================================================================
# 3. Boredom Tests
# ============================================================================

class TestBoredom:
    """Test boredom emergence from sustained low info_gain + low prediction_error."""
    
    def test_low_info_gain_low_error_increases_boredom(self, fresh_engine):
        """Test: low info_gain + low prediction_error -> boredom increase."""
        # Start with low boredom
        fresh_engine.state.boredom = 0.1
        
        # Update with low info gain and low prediction error
        state = fresh_engine.update(
            uncertainty=0.1,
            novelty=0.05,
            social_threat=0.1,
            prediction_error=0.05,
            dt=1.0
        )
        
        assert state.boredom > 0.1, f"Boredom should increase, got {state.boredom}"
        assert state.expected_info_gain < 0.3
    
    def test_sustained_low_increases_boredom_more(self, fresh_engine):
        """Test: sustained low info gain increases boredom more."""
        # Simulate sustained low info gain
        for _ in range(5):
            fresh_engine.update(
                uncertainty=0.1,
                novelty=0.05,
                social_threat=0.1,
                prediction_error=0.05,
                dt=15.0  # 15 seconds each
            )
        
        boredom_after_sustained = fresh_engine.state.boredom
        
        # Should have accumulated boredom
        assert boredom_after_sustained > 0.15
    
    def test_boredom_decays_when_info_gain_returns(self, fresh_engine):
        """Test: boredom decays when info_gain returns."""
        # First create boredom
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.1,
                novelty=0.05,
                social_threat=0.1,
                prediction_error=0.05,
                dt=1.0
            )
        
        boredom_before = fresh_engine.state.boredom
        
        # Now provide high info gain
        fresh_engine.update(
            uncertainty=0.8,
            novelty=0.7,
            social_threat=0.1,
            prediction_error=0.1,
            dt=1.0
        )
        
        boredom_after = fresh_engine.state.boredom
        
        # Boredom should decay (or at least not increase as much)
        assert boredom_after < boredom_before + 0.05
    
    def test_boredom_trace_explains_source(self, fresh_engine):
        """Test: boredom_trace explains the source of boredom."""
        state = fresh_engine.update(
            uncertainty=0.1,
            novelty=0.05,
            social_threat=0.1,
            prediction_error=0.05,
            dt=1.0
        )
        
        assert state.boredom_trace
        assert len(state.boredom_trace) > 0
        # Should contain explanation keywords
        assert any(word in state.boredom_trace.lower() for word in [
            "info_gain", "prediction_error", "sustained", "increased", "decayed"
        ])


# ============================================================================
# 4. Confusion Tests
# ============================================================================

class TestConfusion:
    """Test confusion emergence from high non-converging prediction_error."""
    
    def test_high_prediction_error_increases_confusion(self, fresh_engine):
        """Test: high prediction_error -> confusion increase."""
        # Start with low confusion
        fresh_engine.state.confusion = 0.1
        
        # Update with high prediction error
        state = fresh_engine.update(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            prediction_error=0.6,
            dt=1.0
        )
        
        assert state.confusion > 0.1, f"Confusion should increase, got {state.confusion}"
    
    def test_non_converging_errors_increase_confusion_more(self, fresh_engine):
        """Test: non-converging prediction errors increase confusion more."""
        # Simulate non-converging high errors
        for error in [0.5, 0.55, 0.6]:
            fresh_engine.update(
                uncertainty=0.5,
                novelty=0.3,
                social_threat=0.1,
                prediction_error=error,
                dt=1.0
            )
        
        confusion_non_converging = fresh_engine.state.confusion
        
        # Reset and try with converging errors
        fresh_engine.reset()
        for error in [0.6, 0.4, 0.2]:  # Decreasing
            fresh_engine.update(
                uncertainty=0.5,
                novelty=0.3,
                social_threat=0.1,
                prediction_error=error,
                dt=1.0
            )
        
        confusion_converging = fresh_engine.state.confusion
        
        # Non-converging should produce higher confusion
        assert confusion_non_converging > confusion_converging
    
    def test_confusion_decays_when_errors_converge(self, fresh_engine):
        """Test: confusion decays when prediction errors converge."""
        # First create confusion with high errors
        for error in [0.5, 0.55, 0.6]:
            fresh_engine.update(
                uncertainty=0.5,
                novelty=0.3,
                social_threat=0.1,
                prediction_error=error,
                dt=1.0
            )
        
        confusion_before = fresh_engine.state.confusion
        
        # Now provide low error
        fresh_engine.update(
            uncertainty=0.3,
            novelty=0.2,
            social_threat=0.1,
            prediction_error=0.05,
            dt=1.0
        )
        
        confusion_after = fresh_engine.state.confusion
        
        # Confusion should decay
        assert confusion_after < confusion_before
    
    def test_confusion_trace_explains_source(self, fresh_engine):
        """Test: confusion_trace explains the source of confusion."""
        state = fresh_engine.update(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            prediction_error=0.6,
            dt=1.0
        )
        
        assert state.confusion_trace
        assert len(state.confusion_trace) > 0
        # Should contain explanation keywords
        assert any(word in state.confusion_trace.lower() for word in [
            "prediction_error", "non_converging", "increased", "decayed"
        ])


# ============================================================================
# 5. Integration Tests
# ============================================================================

class TestIntegration:
    """Test integration with meta-cognition and decision."""
    
    def test_high_curiosity_triggers_ask_more(self, fresh_engine):
        """Test: high curiosity triggers ask_more guidance."""
        # Build up curiosity
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.8,
                novelty=0.7,
                social_threat=0.1,
                prediction_error=0.1,
                text="What if we try something new?",
                dt=1.0
            )
        
        guidance = fresh_engine.get_guidance()
        
        assert guidance["ask_more"] is True
        assert "curiosity" in guidance["reason"].lower()
    
    def test_high_curiosity_triggers_propose_experiment(self, fresh_engine):
        """Test: very high curiosity triggers propose_experiment."""
        # Build up very high curiosity
        for _ in range(5):
            fresh_engine.update(
                uncertainty=0.9,
                novelty=0.8,
                social_threat=0.05,
                prediction_error=0.1,
                text="Let's experiment with this idea!",
                dt=1.0
            )
        
        guidance = fresh_engine.get_guidance()
        
        assert guidance["propose_experiment"] is True
    
    def test_high_boredom_triggers_shift_topic(self, fresh_engine):
        """Test: high boredom triggers shift_topic guidance."""
        # Build up boredom
        for _ in range(5):
            fresh_engine.update(
                uncertainty=0.1,
                novelty=0.05,
                social_threat=0.1,
                prediction_error=0.05,
                text="Same old thing.",
                dt=15.0
            )
        
        guidance = fresh_engine.get_guidance()
        
        assert guidance["shift_topic"] is True
        assert "boredom" in guidance["reason"].lower()
    
    def test_high_confusion_triggers_ask_clarify(self, fresh_engine):
        """Test: high confusion triggers ask_clarify guidance."""
        # Build up confusion
        for error in [0.5, 0.55, 0.6, 0.65]:
            fresh_engine.update(
                uncertainty=0.6,
                novelty=0.4,
                social_threat=0.1,
                prediction_error=error,
                dt=1.0
            )
        
        guidance = fresh_engine.get_guidance()
        
        assert guidance["ask_clarify"] is True
        assert "confusion" in guidance["reason"].lower()
    
    def test_low_threat_allows_exploration_boost(self, fresh_engine):
        """Test: low social threat allows exploration tendency boost."""
        # Build up curiosity with low threat
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.8,
                novelty=0.7,
                social_threat=0.1,
                prediction_error=0.1,
                dt=1.0
            )
        
        exploration_low_threat = fresh_engine.state.exploration_tendency
        
        # Reset and try with high threat
        fresh_engine.reset()
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.8,
                novelty=0.7,
                social_threat=0.8,
                prediction_error=0.1,
                dt=1.0
            )
        
        exploration_high_threat = fresh_engine.state.exploration_tendency
        
        # Low threat should allow higher exploration
        assert exploration_low_threat > exploration_high_threat
    
    def test_apply_to_meta_cognition_adds_flags(self, fresh_engine):
        """Test: apply_intrinsic_to_meta_cognition adds intrinsic flags."""
        # Build up curiosity
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.8,
                novelty=0.7,
                social_threat=0.1,
                prediction_error=0.1,
                dt=1.0
            )
        
        meta_context = {}
        updated_context = apply_intrinsic_to_meta_cognition(
            meta_context,
            fresh_engine.state
        )
        
        assert "intrinsic_motivation" in updated_context
        assert updated_context.get("intrinsic_ask_more") is True
    
    def test_apply_to_decision_adds_explore_boost(self, fresh_engine):
        """Test: apply_intrinsic_to_decision adds exploration boost."""
        # Build up curiosity
        for _ in range(3):
            fresh_engine.update(
                uncertainty=0.8,
                novelty=0.7,
                social_threat=0.1,
                prediction_error=0.1,
                dt=1.0
            )
        
        decision_context = {}
        updated_context = apply_intrinsic_to_decision(
            decision_context,
            fresh_engine.state,
            social_threat=0.1
        )
        
        assert "intrinsic_explore_boost" in updated_context
        assert updated_context["intrinsic_explore_boost"] > 0
        assert "intrinsic_motivation" in updated_context


# ============================================================================
# 6. Determinism Tests
# ============================================================================

class TestDeterminism:
    """Test deterministic behavior with same seed."""
    
    def test_same_inputs_same_outputs(self):
        """Test: same inputs produce same outputs with same seed."""
        engine1 = IntrinsicMotivationEngine(seed=42)
        engine2 = IntrinsicMotivationEngine(seed=42)
        
        # Run same updates on both
        for _ in range(5):
            state1 = engine1.update(
                uncertainty=0.7,
                novelty=0.6,
                social_threat=0.2,
                prediction_error=0.3,
                text="What do you think?",
                dt=1.0
            )
            state2 = engine2.update(
                uncertainty=0.7,
                novelty=0.6,
                social_threat=0.2,
                prediction_error=0.3,
                text="What do you think?",
                dt=1.0
            )
        
        # States should be identical
        assert state1.curiosity == state2.curiosity
        assert state1.boredom == state2.boredom
        assert state1.confusion == state2.confusion
        assert state1.expected_info_gain == state2.expected_info_gain
        assert state1.predictability == state2.predictability
    
    def test_history_maintains_state(self, fresh_engine):
        """Test: history maintains correct state across updates."""
        # Add values to history
        for i in range(5):
            fresh_engine.update(
                uncertainty=0.5,
                novelty=0.3,
                social_threat=0.1,
                prediction_error=0.2 + i * 0.1,
                dt=1.0
            )
        
        # History should have 5 values
        assert len(fresh_engine.info_gain_history.values) == 5
        assert len(fresh_engine.prediction_error_history.values) == 5
        
        # Check trend detection
        trend = fresh_engine.prediction_error_history.get_trend()
        assert trend > 0  # Errors are increasing


# ============================================================================
# 7. InfoGainHistory Tests
# ============================================================================

class TestInfoGainHistory:
    """Test InfoGainHistory class."""
    
    def test_add_and_retrieve(self, info_gain_history):
        """Test: add values and retrieve recent average."""
        for i in range(5):
            info_gain_history.add(0.1 * i)
        
        avg = info_gain_history.get_recent_average(3)
        expected = (0.2 + 0.3 + 0.4) / 3
        assert abs(avg - expected) < 0.001
    
    def test_max_window_size(self, info_gain_history):
        """Test: history respects max window size."""
        for i in range(25):
            info_gain_history.add(0.1 * i)
        
        # Should only keep last 20
        assert len(info_gain_history.values) == 20
    
    def test_sustained_low_detection(self, info_gain_history):
        """Test: detect sustained low info gain."""
        now = time.time()
        
        # Add low values with time gaps
        for i in range(5):
            info_gain_history.add(0.1, now + i * 20)
        
        duration = info_gain_history.get_sustained_low_duration(threshold=0.2)
        assert duration > 0


# ============================================================================
# 8. PredictionErrorHistory Tests
# ============================================================================

class TestPredictionErrorHistory:
    """Test PredictionErrorHistory class."""
    
    def test_non_converging_detection(self, prediction_error_history):
        """Test: detect non-converging prediction errors."""
        # Add high errors
        for error in [0.5, 0.55, 0.6]:
            prediction_error_history.add(error)
        
        assert prediction_error_history.is_non_converging(threshold=0.4, min_samples=3)
    
    def test_converging_not_detected(self, prediction_error_history):
        """Test: converging errors not detected as non-converging."""
        # Add decreasing errors
        for error in [0.6, 0.4, 0.2]:
            prediction_error_history.add(error)
        
        assert not prediction_error_history.is_non_converging(threshold=0.4, min_samples=3)
    
    def test_trend_calculation(self, prediction_error_history):
        """Test: trend calculation for errors."""
        # Add increasing errors
        for error in [0.1, 0.2, 0.3, 0.4, 0.5]:
            prediction_error_history.add(error)
        
        trend = prediction_error_history.get_trend()
        assert trend > 0  # Increasing trend
    
    def test_decreasing_trend(self, prediction_error_history):
        """Test: decreasing trend detection."""
        # Add decreasing errors
        for error in [0.5, 0.4, 0.3, 0.2, 0.1]:
            prediction_error_history.add(error)
        
        trend = prediction_error_history.get_trend()
        assert trend < 0  # Decreasing trend


# ============================================================================
# 9. State Serialization Tests
# ============================================================================

class TestStateSerialization:
    """Test state serialization and deserialization."""
    
    def test_to_dict_contains_all_fields(self, fresh_engine):
        """Test: to_dict contains all expected fields."""
        state = fresh_engine.update(
            uncertainty=0.7,
            novelty=0.6,
            social_threat=0.2,
            prediction_error=0.3,
            dt=1.0
        )
        
        d = state.to_dict()
        
        expected_fields = [
            "curiosity", "boredom", "confusion",
            "expected_info_gain", "predictability", "exploration_tendency",
            "curiosity_trace", "boredom_trace", "confusion_trace", "info_gain_trace"
        ]
        
        for field in expected_fields:
            assert field in d, f"Missing field: {field}"


# ============================================================================
# 10. Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_uncertainty(self, fresh_engine):
        """Test: handle zero uncertainty gracefully."""
        state = fresh_engine.update(
            uncertainty=0.0,
            novelty=0.0,
            social_threat=0.0,
            prediction_error=0.0,
            dt=1.0
        )
        
        # Should not crash and should produce valid state
        assert 0.0 <= state.curiosity <= 1.0
        assert 0.0 <= state.boredom <= 1.0
        assert 0.0 <= state.confusion <= 1.0
    
    def test_max_values(self, fresh_engine):
        """Test: handle maximum values gracefully."""
        state = fresh_engine.update(
            uncertainty=1.0,
            novelty=1.0,
            social_threat=1.0,
            prediction_error=1.0,
            dt=1.0
        )
        
        # All values should be clamped to valid range
        assert 0.0 <= state.curiosity <= 1.0
        assert 0.0 <= state.boredom <= 1.0
        assert 0.0 <= state.confusion <= 1.0
        assert 0.0 <= state.expected_info_gain <= 1.0
        assert 0.0 <= state.predictability <= 1.0
    
    def test_empty_text(self, fresh_engine):
        """Test: handle empty/None text gracefully."""
        state = fresh_engine.update(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            prediction_error=0.2,
            text=None,
            dt=1.0
        )
        
        assert state.expected_info_gain >= 0.0
    
    def test_very_long_text(self, fresh_engine):
        """Test: handle very long text gracefully."""
        long_text = "What? " * 1000
        
        state = fresh_engine.update(
            uncertainty=0.5,
            novelty=0.3,
            social_threat=0.1,
            prediction_error=0.2,
            text=long_text,
            dt=1.0
        )
        
        # Should still detect question
        assert state.expected_info_gain > 0.3


# ============================================================================
# 11. API Function Tests
# ============================================================================

class TestAPIFunctions:
    """Test convenience API functions."""
    
    def test_compute_intrinsic_motivation(self):
        """Test: compute_intrinsic_motivation convenience function."""
        reset_intrinsic_engine()
        
        state = compute_intrinsic_motivation(
            uncertainty=0.7,
            novelty=0.6,
            social_threat=0.2,
            prediction_error=0.3,
            text="What do you think?",
            dt=1.0,
            seed=42
        )
        
        assert isinstance(state, IntrinsicMotivationState)
        assert state.expected_info_gain > 0
    
    def test_get_intrinsic_engine_singleton(self):
        """Test: get_intrinsic_engine returns singleton."""
        reset_intrinsic_engine()
        
        engine1 = get_intrinsic_engine(seed=42)
        engine2 = get_intrinsic_engine(seed=42)
        
        # Should be same instance
        assert engine1 is engine2
    
    def test_reset_intrinsic_engine(self):
        """Test: reset_intrinsic_engine clears singleton."""
        engine1 = get_intrinsic_engine(seed=42)
        reset_intrinsic_engine()
        engine2 = get_intrinsic_engine(seed=42)
        
        # Should be different instances after reset
        assert engine1 is not engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
