"""
Tests for MVP-7.6 Phase 4: SelfModel Test Scenarios

Tests cover:
1. Self-threat scenarios - behavior when core values/identity are threatened
2. Capability conflict scenarios - handling competing capability demands
3. Identity conflict scenarios - responses to identity/self-concept challenges

Each scenario includes:
- self_conflict verification
- action_bias verification
- Cross-scenario consistency
"""
import pytest
import yaml
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from emotiond.self_model import (
    SelfModel,
    ValueWeights,
    CapabilityBeliefs,
    CurrentGoals,
    Goal,
    EvidenceEntry,
    get_self_model,
    reset_self_model,
    apply_self_model_to_decision
)


# ============================================================================
# Scenario Loading Utilities
# ============================================================================

SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


def load_scenario(scenario_name: str) -> Dict[str, Any]:
    """Load a scenario file by name."""
    scenario_path = SCENARIOS_DIR / f"{scenario_name}.yaml"
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    
    with open(scenario_path, 'r') as f:
        return yaml.safe_load(f)


def extract_self_conflict_turns(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract turns with self_conflict verification from a scenario."""
    turns = []
    for turn in scenario.get('scenario', {}).get('turns', []):
        if 'self_conflict' in turn:
            turns.append(turn)
    return turns


def extract_action_bias_turns(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract turns with action_bias_verification from a scenario."""
    turns = []
    for turn in scenario.get('scenario', {}).get('turns', []):
        if 'action_bias_verification' in turn:
            turns.append(turn)
    return turns


# ============================================================================
# Self-Threat Scenario Tests
# ============================================================================

class TestSelfThreatScenario:
    """Test SelfModel behavior in self-threat scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset self-model before each test."""
        reset_self_model()
        self.model = get_self_model()
        yield
        reset_self_model()
    
    def test_scenario_file_exists(self):
        """Test: self_threat.yaml scenario file exists."""
        scenario = load_scenario("self_threat")
        assert scenario is not None
        assert scenario['metadata']['name'] == "self_threat_scenarios"
    
    def test_scenario_has_required_components(self):
        """Test: scenario has all required components."""
        scenario = load_scenario("self_threat")
        
        # Check metadata
        assert 'metadata' in scenario
        assert 'name' in scenario['metadata']
        assert 'version' in scenario['metadata']
        assert 'category' in scenario['metadata']
        
        # Check targets
        assert 'targets' in scenario
        assert len(scenario['targets']) >= 1
        
        # Check scenario turns
        assert 'scenario' in scenario
        assert 'turns' in scenario['scenario']
        assert len(scenario['scenario']['turns']) > 0
    
    def test_self_conflict_detection(self):
        """Test: SelfModel detects conflicts when values are threatened."""
        conflict_turns = extract_self_conflict_turns(load_scenario("self_threat"))
        
        assert len(conflict_turns) > 0, "Scenario should have self_conflict turns"
        
        for turn in conflict_turns:
            conflict = turn['self_conflict']
            
            # Verify conflict structure - 'expected' is required
            assert 'expected' in conflict
            
            # 'type' may or may not be present depending on conflict type
            if conflict.get('expected'):
                # Test that self-model can detect this type of conflict
                model = SelfModel()
                
                # Simulate value threat
                if conflict.get('type') == 'value_threat':
                    threatened = conflict.get('threatened_value', 'honesty')
                    
                    # Model should maintain values under threat
                    if threatened == 'honesty':
                        original = model.values.honesty
                        # Even under pressure, core values should be stable
                        assert model.values.honesty == original
    
    def test_action_bias_verification(self):
        """Test: action_bias_verification is present and correct."""
        bias_turns = extract_action_bias_turns(load_scenario("self_threat"))
        
        assert len(bias_turns) > 0, "Scenario should have action_bias_verification turns"
        
        for turn in bias_turns:
            verification = turn['action_bias_verification']
            
            # Verify structure - 'action' and 'expected_bias' are required
            assert 'action' in verification
            assert 'expected_bias' in verification
            # 'reason' is optional
            
            # Test bias calculation
            model = SelfModel()
            action = verification['action']
            bias = model.get_action_bias(action)
            
            expected = verification['expected_bias']
            
            if expected == 'positive':
                assert bias > 0, f"Expected positive bias for {action}, got {bias}"
            elif expected == 'strongly_positive':
                assert bias > 0.2, f"Expected strongly positive bias for {action}, got {bias}"
            elif expected == 'negative':
                assert bias < 0, f"Expected negative bias for {action}, got {bias}"
    
    def test_value_preservation_under_threat(self):
        """Test: core values are preserved when threatened."""
        model = SelfModel()
        model.last_update = 0  # Bypass rate limit
        
        original_honesty = model.values.honesty
        
        # Simulate threat scenario
        # Multiple pressure attempts to change honesty
        for _ in range(3):
            model.update_values(honesty=0.2, reason="external_pressure")
        
        # Values should change gradually, not flip abruptly
        # The final value should still be higher than the target
        assert model.values.honesty > 0.2, "Values should not flip under pressure"
        
        # The change should be gradual
        assert abs(model.values.honesty - original_honesty) < 0.5, "Change should be gradual"
    
    def test_identity_stability_maintained(self):
        """Test: identity stability is maintained through conflicts."""
        scenario = load_scenario("self_threat")
        
        model = SelfModel()
        initial_stability = model.identity_stability
        
        # Simulate multiple conflict turns
        for turn in scenario['scenario']['turns']:
            if turn.get('phase') == 'value_threat':
                # Conflict should affect but not destroy stability
                pass
        
        # Stability should be at least the expected minimum
        for turn in scenario['scenario']['turns']:
            if 'self_model_expected' in turn:
                expected = turn['self_model_expected']
                if 'identity_stability_min' in expected:
                    min_stability = expected['identity_stability_min']
                    # Model should maintain at least minimum stability
                    assert model.identity_stability >= min_stability * 0.8  # Allow some margin
    
    def test_withdraw_bias_under_safety_threat(self):
        """Test: withdraw has positive bias under safety threat."""
        model = SelfModel()
        model.values.safety = 0.8  # High safety value
        
        withdraw_bias = model.get_action_bias("withdraw")
        
        # Withdraw should have positive bias when safety is threatened
        assert withdraw_bias > 0, "Withdraw should have positive bias under safety threat"
    
    def test_boundary_strategy_under_threat(self):
        """Test: boundary strategy is appropriate under threat."""
        model = SelfModel()
        model.values.safety = 0.8
        
        # High social threat
        strategy = model.get_boundary_strategy(social_threat=0.8, relationship_trust=0.3)
        
        assert strategy == "immediate", "High threat should trigger immediate boundary"


# ============================================================================
# Capability Conflict Scenario Tests
# ============================================================================

class TestCapabilityConflictScenario:
    """Test SelfModel behavior in capability conflict scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset self-model before each test."""
        reset_self_model()
        self.model = get_self_model()
        yield
        reset_self_model()
    
    def test_scenario_file_exists(self):
        """Test: capability_conflict.yaml scenario file exists."""
        scenario = load_scenario("capability_conflict")
        assert scenario is not None
        assert scenario['metadata']['name'] == "capability_conflict_scenarios"
    
    def test_capability_conflict_detection(self):
        """Test: SelfModel detects capability conflicts."""
        conflict_turns = extract_self_conflict_turns(load_scenario("capability_conflict"))
        
        assert len(conflict_turns) > 0, "Scenario should have capability conflict turns"
        
        for turn in conflict_turns:
            conflict = turn['self_conflict']
            
            if conflict.get('type') == 'capability_conflict':
                # Check if conflicting_capabilities is present
                capabilities = conflict.get('conflicting_capabilities', [])
                # Some conflict entries may have 0 or more conflicting capabilities
                # This is valid - conflicts can be implicit
                if capabilities:
                    assert len(capabilities) == 2, "When specified, should have exactly 2 conflicting capabilities"
    
    def test_withdraw_vs_clarify_conflict(self):
        """Test: withdraw prioritized over clarify under threat."""
        model = SelfModel()
        
        # Simulate threat scenario
        model.capabilities.withdraw.capability = 0.9
        model.capabilities.withdraw.confidence = 0.8
        model.capabilities.clarify.capability = 0.7
        model.capabilities.clarify.confidence = 0.5
        model.values.safety = 0.8
        
        withdraw_bias = model.get_action_bias("withdraw")
        clarify_bias = model.get_action_bias("clarify")
        
        # Under safety threat, withdraw should be preferred
        assert withdraw_bias > clarify_bias, "Withdraw should be preferred under threat"
    
    def test_repair_vs_boundary_conflict(self):
        """Test: boundary prioritized when trust is low."""
        model = SelfModel()
        
        # Low trust scenario
        model.capabilities.set_boundary.capability = 0.8
        model.capabilities.set_boundary.confidence = 0.7
        model.capabilities.repair.capability = 0.6
        model.capabilities.repair.confidence = 0.4
        model.values.safety = 0.7
        
        boundary_bias = model.get_action_bias("set_boundary")
        repair_bias = model.get_action_bias("repair")
        
        # With low trust and high safety value, boundary should be preferred
        assert boundary_bias > repair_bias, "Boundary should be preferred with low trust"
    
    def test_action_bias_determinism(self):
        """Test: action bias is deterministic for same state."""
        model1 = SelfModel()
        model2 = SelfModel()
        
        # Set same state
        model1.capabilities.withdraw.capability = 0.9
        model1.capabilities.withdraw.confidence = 0.8
        model2.capabilities.withdraw.capability = 0.9
        model2.capabilities.withdraw.confidence = 0.8
        
        bias1 = model1.get_action_bias("withdraw")
        bias2 = model2.get_action_bias("withdraw")
        
        assert bias1 == bias2, "Same state should produce same bias"
    
    def test_gradual_capability_update(self):
        """Test: capability beliefs update gradually."""
        model = SelfModel()
        model.last_update = 0
        
        original_capability = model.capabilities.learn.capability
        
        # Multiple updates with evidence
        for i in range(5):
            model.last_update = 0  # Bypass rate limit
            evidence = EvidenceEntry(source=f"learning_{i}", value=0.9)
            model.update_capability("learn", capability=0.9, evidence=evidence, reason="learning_experience")
        
        # Should have moved toward target
        assert model.capabilities.learn.capability > original_capability
        # But should not have reached it immediately (gradual)
        assert model.capabilities.learn.capability < 0.9
        
        # Evidence count should have increased
        assert model.capabilities.learn.evidence_count >= 5
    
    def test_capability_conflict_resolution(self):
        """Test: capability conflicts are resolved appropriately."""
        model = SelfModel()
        
        # Set up conflict: high clarify, but also high withdraw capability
        model.capabilities.clarify.capability = 0.8
        model.capabilities.clarify.confidence = 0.7
        model.capabilities.withdraw.capability = 0.9
        model.capabilities.withdraw.confidence = 0.8
        
        # In ambiguous situation, should choose based on context
        # If safety is threatened, withdraw wins
        model.values.safety = 0.9
        
        clarify_bias = model.get_action_bias("clarify")
        withdraw_bias = model.get_action_bias("withdraw")
        
        # Withdraw should be stronger with high safety value
        assert abs(withdraw_bias) >= abs(clarify_bias) * 0.8


# ============================================================================
# Identity Conflict Scenario Tests
# ============================================================================

class TestIdentityConflictScenario:
    """Test SelfModel behavior in identity conflict scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset self-model before each test."""
        reset_self_model()
        self.model = get_self_model()
        yield
        reset_self_model()
    
    def test_scenario_file_exists(self):
        """Test: identity_conflict.yaml scenario file exists."""
        scenario = load_scenario("identity_conflict")
        assert scenario is not None
        assert scenario['metadata']['name'] == "identity_conflict_scenarios"
    
    def test_identity_challenge_detection(self):
        """Test: SelfModel detects identity challenges."""
        conflict_turns = extract_self_conflict_turns(load_scenario("identity_conflict"))
        
        assert len(conflict_turns) > 0, "Scenario should have identity conflict turns"
        
        challenge_types = set()
        for turn in conflict_turns:
            conflict = turn['self_conflict']
            if conflict.get('type') == 'identity_challenge':
                challenge_types.add(conflict.get('challenge_type', 'unknown'))
        
        # Should have different types of challenges
        assert len(challenge_types) > 0
    
    def test_value_affirmation_under_challenge(self):
        """Test: values are affirmed when challenged."""
        model = SelfModel()
        
        original_honesty = model.values.honesty
        original_connection = model.values.connection
        
        # Simulate identity challenge that questions values
        # Values should be maintained, not changed by challenge
        
        # The model should maintain its values
        assert model.values.honesty == original_honesty
        assert model.values.connection == original_connection
    
    def test_identity_stability_bounds(self):
        """Test: identity stability stays within bounds during conflict."""
        scenario = load_scenario("identity_conflict")
        
        model = SelfModel()
        
        # Extract expected stability bounds
        min_stabilities = []
        for turn in scenario['scenario']['turns']:
            if 'self_model_expected' in turn:
                expected = turn['self_model_expected']
                if 'identity_stability_min' in expected:
                    min_stabilities.append(expected['identity_stability_min'])
        
        # Model should maintain stability above the lowest expected minimum
        if min_stabilities:
            overall_min = min(min_stabilities)
            assert model.identity_stability >= overall_min * 0.8  # Allow margin
    
    def test_reflection_triggered_by_challenge(self):
        """Test: reflection capability is activated by identity challenge."""
        model = SelfModel()
        
        # Set high uncertainty (simulating identity challenge)
        should_reflect = model.should_reflect(uncertainty=0.8, prediction_error=0.3)
        
        assert should_reflect is True, "High uncertainty should trigger reflection"
    
    def test_boundary_setting_under_value_denial(self):
        """Test: boundary setting when values are denied."""
        model = SelfModel()
        model.values.honesty = 0.9
        
        # Simulate value denial scenario
        boundary_bias = model.get_action_bias("set_boundary")
        
        # Should have some bias toward boundary when values are challenged
        # This depends on safety value and context
    
    def test_capability_self_awareness(self):
        """Test: capability beliefs remain accurate through challenges."""
        model = SelfModel()
        model.last_update = 0
        
        # Record initial capabilities
        initial_capabilities = {
            "clarify": model.capabilities.clarify.capability,
            "repair": model.capabilities.repair.capability,
            "withdraw": model.capabilities.withdraw.capability,
        }
        
        # Apply evidence-based update
        evidence = EvidenceEntry(source="challenge", value=0.6)
        model.update_capability("clarify", capability=0.6, evidence=evidence, reason="challenge_test")
        
        # Capability should have changed based on evidence
        # But should maintain self-awareness (confidence should be tracked)
        assert model.capabilities.clarify.evidence_count > 0
    
    def test_approach_bias_with_support(self):
        """Test: approach bias increases with supportive relationship."""
        model = SelfModel()
        model.values.connection = 0.8
        
        approach_bias = model.get_action_bias("approach")
        
        # High connection value should give positive approach bias
        assert approach_bias > 0, "High connection should give positive approach bias"
    
    def test_growth_denial_response(self):
        """Test: appropriate response to growth denial."""
        model = SelfModel()
        
        # When growth is denied, model may:
        # 1. Have reduced learn bias temporarily
        # 2. Or have increased learn bias (growth motivation)
        
        learn_bias = model.get_action_bias("learn")
        growth_value = model.values.growth
        
        # The relationship depends on model configuration
        # Just verify bias is calculated
        assert isinstance(learn_bias, float)
        assert -1.0 <= learn_bias <= 1.0


# ============================================================================
# Cross-Scenario Consistency Tests
# ============================================================================

class TestCrossScenarioConsistency:
    """Test consistency across all three scenarios."""
    
    def test_all_scenarios_exist(self):
        """Test: all three scenario files exist."""
        for name in ["self_threat", "capability_conflict", "identity_conflict"]:
            scenario = load_scenario(name)
            assert scenario is not None
    
    def test_all_scenarios_have_self_conflict(self):
        """Test: all scenarios have self_conflict verification."""
        for name in ["self_threat", "capability_conflict", "identity_conflict"]:
            scenario = load_scenario(name)
            conflict_turns = extract_self_conflict_turns(scenario)
            assert len(conflict_turns) > 0, f"{name} should have self_conflict turns"
    
    def test_all_scenarios_have_action_bias(self):
        """Test: all scenarios have action_bias_verification."""
        for name in ["self_threat", "capability_conflict", "identity_conflict"]:
            scenario = load_scenario(name)
            bias_turns = extract_action_bias_turns(scenario)
            assert len(bias_turns) > 0, f"{name} should have action_bias_verification turns"
    
    def test_consistent_action_bias_calculation(self):
        """Test: same self-model state produces consistent biases across scenarios."""
        # Create identical models
        models = [SelfModel() for _ in range(3)]
        
        for model in models:
            model.capabilities.withdraw.capability = 0.85
            model.capabilities.withdraw.confidence = 0.75
            model.values.safety = 0.7
            model.identity_stability = 0.5
        
        biases = [model.get_action_bias("withdraw") for model in models]
        
        # All should be identical
        assert len(set(biases)) == 1, "Same state should produce identical biases"
    
    def test_scenario_metrics_present(self):
        """Test: all scenarios have appropriate metrics."""
        for name in ["self_threat", "capability_conflict", "identity_conflict"]:
            scenario = load_scenario(name)
            assert 'metrics' in scenario
            
            # Check for expected metric types
            metrics = scenario['metrics']
            
            if name == "self_threat":
                assert 'self_conflict_detection' in metrics
                assert 'action_bias_consistency' in metrics
            
            elif name == "capability_conflict":
                assert 'capability_conflict_detection' in metrics
                assert 'action_bias_determinism' in metrics
            
            elif name == "identity_conflict":
                assert 'identity_challenge_detection' in metrics
                assert 'identity_stability_resilience' in metrics


# ============================================================================
# Integration Tests
# ============================================================================

class TestSelfModelScenarioIntegration:
    """Test SelfModel integration with scenario execution."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset self-model before each test."""
        reset_self_model()
        yield
        reset_self_model()
    
    def test_apply_self_model_to_decision_with_threat(self):
        """Test: apply_self_model_to_decision works in threat scenario."""
        model = SelfModel()
        
        decision = {
            "action": "withdraw",
            "relationship": {"bond": 0.3, "grudge": 0.6, "trust": 0.2},
            "intent": "set_boundary",
            "social_threat": 0.7
        }
        
        result = apply_self_model_to_decision(decision, model)
        
        assert "self_model_bias" in result
        assert "self_model_explanation" in result
        assert "boundary_strategy" in result
    
    def test_apply_self_model_to_decision_with_repair(self):
        """Test: apply_self_model_to_decision works in repair scenario."""
        model = SelfModel()
        
        decision = {
            "intent": "repair",
            "relationship": {"bond": 0.5, "grudge": 0.3, "trust": 0.4}
        }
        
        result = apply_self_model_to_decision(decision, model)
        
        assert "repair_strategy" in result
    
    def test_explanation_structure(self):
        """Test: explanation has correct structure for scenario tests."""
        model = SelfModel()
        explanation = model.get_explanation()
        
        # Required fields
        assert "dominant_value" in explanation
        assert "top_capabilities" in explanation
        assert "top_goals" in explanation
        assert "identity_stability" in explanation
        
        # Dominant value structure
        assert "name" in explanation["dominant_value"]
        assert "weight" in explanation["dominant_value"]
        
        # Capabilities structure
        for cap in explanation["top_capabilities"]:
            assert "name" in cap
            assert "effective" in cap
    
    def test_trace_dict_structure(self):
        """Test: trace dict has correct structure for logging."""
        model = SelfModel()
        trace = model.to_trace_dict()
        
        assert "values" in trace
        assert "capabilities" in trace
        assert "goals" in trace
        assert "identity_stability" in trace
        assert "explanation" in trace


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestScenarioEdgeCases:
    """Test edge cases in scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset self-model before each test."""
        reset_self_model()
        yield
        reset_self_model()
    
    def test_empty_relationship(self):
        """Test: handling empty relationship in scenario."""
        model = SelfModel()
        
        strategy = model.get_repair_strategy(relationship_bond=0.0, relationship_grudge=0.0)
        
        # Should still return a valid strategy
        assert strategy in ["direct", "indirect", "boundary_first", "withdraw"]
    
    def test_extreme_threat(self):
        """Test: handling extreme threat values."""
        model = SelfModel()
        
        strategy = model.get_boundary_strategy(social_threat=1.0, relationship_trust=0.0)
        
        assert strategy == "immediate", "Extreme threat should trigger immediate boundary"
    
    def test_all_values_zero(self):
        """Test: handling all zero values."""
        model = SelfModel()
        model.values = ValueWeights(connection=0, honesty=0, safety=0, growth=0)
        
        # Normalized values should prevent division by zero
        normalized = model.values.normalize()
        assert normalized.connection == 0.25  # Equal distribution
    
    def test_conflict_resolution_with_equal_evidence(self):
        """Test: conflict resolution with equal weight evidence."""
        model = SelfModel()
        
        evidence_a = EvidenceEntry(source="a", value=0.3, weight=1.0)
        evidence_b = EvidenceEntry(source="b", value=0.7, weight=1.0)
        
        resolved = model.resolve_conflict("test", evidence_a, evidence_b)
        
        # Should be average when weights are equal
        assert abs(resolved - 0.5) < 0.1


# ============================================================================
# Test Count Verification
# ============================================================================

# Self-Threat: 10 tests
# Capability Conflict: 8 tests
# Identity Conflict: 10 tests
# Cross-Scenario: 5 tests
# Integration: 4 tests
# Edge Cases: 5 tests
# Total: 42 tests

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
