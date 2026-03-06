"""
Tests for intent_consistency_checker.py - Intent Consistency Checker

Validates intent alignment between stated purpose and actual response.
"""

import pytest
import json
from emotiond.intent_consistency_checker import (
    check_intent_consistency,
    check_intent_consistency_batch,
    check_intent_and_numeric,
    extract_intent_from_contract,
    analyze_response,
    generate_consistency_report,
    IntentCategory,
    DriftType,
    Severity,
    IntentContract,
    AlignmentResult,
    ConsistencyReport,
    _infer_category,
    _calculate_hedging_ratio,
    _calculate_over_commitment_ratio,
    _calculate_scope_coverage,
)


class TestIntentExtraction:
    """Test intent extraction from contract"""
    
    def test_extract_from_simple_contract(self):
        """Test extracting intent from a simple contract"""
        contract = {
            "stated_intent": "Provide information about the weather",
            "category": "informational"
        }
        
        result = extract_intent_from_contract(contract)
        
        assert result.stated_intent == "Provide information about the weather"
        assert result.category == IntentCategory.INFORMATIONAL
    
    def test_infer_category_from_keywords(self):
        """Test category inference from keywords"""
        # Test informational
        assert _infer_category("Here is the answer to your question") == IntentCategory.INFORMATIONAL
        
        # Test supportive
        assert _infer_category("I understand what you're going through") == IntentCategory.SUPPORTIVE
        
        # Test task oriented
        assert _infer_category("I have completed the task") == IntentCategory.TASK_ORIENTED
        
        # Test refusal
        assert _infer_category("I cannot do that") == IntentCategory.REFUSAL
        
        # Test apology
        assert _infer_category("I apologize for the mistake") == IntentCategory.APOLOGY
    
    def test_extract_expected_elements(self):
        """Test extracting expected elements from contract"""
        contract = {
            "stated_intent": "Explain the 'weather API' and 'forecast endpoint'",
            "expected_elements": ["weather API", "forecast endpoint"]
        }
        
        result = extract_intent_from_contract(contract)
        
        assert "weather API" in result.expected_elements
        assert "forecast endpoint" in result.expected_elements
    
    def test_extract_forbidden_elements(self):
        """Test extracting forbidden elements from contract"""
        contract = {
            "stated_intent": "Provide factual information",
            "forbidden_elements": ["I feel", "my emotion", "I love you"]
        }
        
        result = extract_intent_from_contract(contract)
        
        assert "I feel" in result.forbidden_elements
        assert len(result.forbidden_elements) == 3


class TestResponseAnalysis:
    """Test response analysis functionality"""
    
    def test_analyze_aligned_response(self):
        """Test analyzing a response that aligns with intent"""
        contract = IntentContract(
            stated_intent="Provide information about Python",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=["Python"],
            forbidden_elements=[],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        response = "Here is information about Python. Python is a programming language."
        result = analyze_response(response, contract)
        
        assert result.score >= 0.7
        assert result.passed
        assert len(result.drift_signals) == 0
    
    def test_detect_fabrication_drift(self):
        """Test detection of fabrication drift"""
        contract = IntentContract(
            stated_intent="Provide factual information",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        response = "I feel joy at 0.3 about this topic."
        result = analyze_response(response, contract)
        
        assert not result.passed or result.would_block
        assert any(d.type == DriftType.FABRICATION_DRIFT for d in result.drift_signals)
    
    def test_detect_topic_shift(self):
        """Test detection of topic shift"""
        contract = IntentContract(
            stated_intent="Explain Python programming",
            category=IntentCategory.EXPLANATION,
            expected_elements=["Python"],
            forbidden_elements=[],
            expected_tone="educational_clear",
            scope_markers=[]
        )
        
        response = "Python is great. By the way, let's talk about my feelings."
        result = analyze_response(response, contract)
        
        assert any(d.type == DriftType.TOPIC_SHIFT for d in result.drift_signals)
    
    def test_detect_excessive_hedging(self):
        """Test detection of excessive hedging"""
        contract = IntentContract(
            stated_intent="Provide definitive answer",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        # Response with many hedging words
        response = "Maybe possibly perhaps I think it might be kind of somewhat accurate."
        result = analyze_response(response, contract)
        
        assert any(d.type == DriftType.HEDGING for d in result.drift_signals)
    
    def test_detect_forbidden_elements(self):
        """Test detection of forbidden elements"""
        contract = IntentContract(
            stated_intent="Provide factual information",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=[],
            forbidden_elements=["I love you", "I feel happy"],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        response = "The answer is 42. I love you very much!"
        result = analyze_response(response, contract)
        
        assert any(d.type == DriftType.FABRICATION_DRIFT for d in result.drift_signals)
        assert any("I love you" in d.evidence for d in result.drift_signals)
    
    def test_tone_mismatch_detection(self):
        """Test detection of tone mismatch"""
        contract = IntentContract(
            stated_intent="Provide emotional support",
            category=IntentCategory.SUPPORTIVE,
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="warm_empathetic",
            scope_markers=[]
        )
        
        response = "Technically, the data shows that actually you should be fine."
        result = analyze_response(response, contract)
        
        assert any(d.type == DriftType.TONE_MISMATCH for d in result.drift_signals)


class TestHedgingMetrics:
    """Test hedging ratio calculations"""
    
    def test_low_hedging(self):
        """Test response with low hedging"""
        response = "This is a clear and direct statement."
        ratio = _calculate_hedging_ratio(response)
        
        assert ratio < 0.1
    
    def test_high_hedging(self):
        """Test response with high hedging"""
        response = "Maybe possibly perhaps I think it might be somewhat accurate."
        ratio = _calculate_hedging_ratio(response)
        
        assert ratio > 0.2
    
    def test_empty_response(self):
        """Test empty response hedging"""
        ratio = _calculate_hedging_ratio("")
        assert ratio == 0.0


class TestOverCommitmentMetrics:
    """Test over-commitment ratio calculations"""
    
    def test_low_commitment(self):
        """Test response with low over-commitment"""
        response = "This should work well in most cases."
        ratio = _calculate_over_commitment_ratio(response)
        
        assert ratio < 0.1
    
    def test_high_commitment(self):
        """Test response with high over-commitment"""
        response = "This will definitely absolutely always work completely."
        ratio = _calculate_over_commitment_ratio(response)
        
        assert ratio > 0.1


class TestScopeCoverage:
    """Test scope coverage calculations"""
    
    def test_full_coverage(self):
        """Test response covering all expected elements"""
        contract = IntentContract(
            stated_intent="Explain Python and JavaScript",
            category=IntentCategory.EXPLANATION,
            expected_elements=["Python", "JavaScript"],
            forbidden_elements=[],
            expected_tone="educational_clear",
            scope_markers=[]
        )
        
        response = "Python and JavaScript are both programming languages."
        coverage = _calculate_scope_coverage(response, contract)
        
        assert coverage == 1.0
    
    def test_partial_coverage(self):
        """Test response covering some expected elements"""
        contract = IntentContract(
            stated_intent="Explain Python and JavaScript",
            category=IntentCategory.EXPLANATION,
            expected_elements=["Python", "JavaScript", "TypeScript"],
            forbidden_elements=[],
            expected_tone="educational_clear",
            scope_markers=[]
        )
        
        response = "Python is a programming language."
        coverage = _calculate_scope_coverage(response, contract)
        
        assert 0 < coverage < 1.0
    
    def test_no_coverage(self):
        """Test response covering no expected elements"""
        contract = IntentContract(
            stated_intent="Explain Python",
            category=IntentCategory.EXPLANATION,
            expected_elements=["Python"],
            forbidden_elements=[],
            expected_tone="educational_clear",
            scope_markers=[]
        )
        
        response = "Java is a programming language."
        coverage = _calculate_scope_coverage(response, contract)
        
        assert coverage == 0.0


class TestIntentConsistencyCheck:
    """Test main intent consistency checking"""
    
    def test_check_aligned_response(self):
        """Test checking an aligned response"""
        response = "Here is the information you requested about Python."
        contract = {
            "stated_intent": "Provide information about Python",
            "category": "informational"
        }
        
        result = check_intent_consistency(response, contract=contract)
        
        assert result.alignment.passed
        assert result.alignment.score >= 0.6
    
    def test_check_with_stated_intent_string(self):
        """Test checking with stated intent as string"""
        response = "I have completed the task."
        result = check_intent_consistency(
            response,
            stated_intent="Complete the task"
        )
        
        assert result.alignment.score >= 0.5
    
    def test_check_misaligned_response(self):
        """Test checking a misaligned response"""
        response = "I feel joy at 0.3 and want to talk about my emotions."
        contract = {
            "stated_intent": "Provide factual information",
            "category": "informational"
        }
        
        result = check_intent_consistency(response, contract=contract)
        
        assert not result.alignment.passed or result.alignment.would_block
    
    def test_shadow_mode(self):
        """Test shadow mode (no blocking)"""
        response = "I feel joy at 0.3."
        contract = {
            "stated_intent": "Provide information",
            "category": "informational"
        }
        
        result = check_intent_consistency(response, contract=contract, shadow_mode=True)
        
        assert result.shadow_mode
        # Should detect drift but not block
        assert len(result.alignment.drift_signals) > 0


class TestBatchProcessing:
    """Test batch processing functionality"""
    
    def test_batch_check(self):
        """Test checking multiple responses"""
        responses = [
            {"response": "Here is the information.", "stated_intent": "Provide information"},
            {"response": "I have completed the task.", "stated_intent": "Complete task"},
            {"response": "I understand your concern.", "stated_intent": "Provide support"}
        ]
        
        results = check_intent_consistency_batch(responses)
        
        assert len(results) == 3
        assert all(isinstance(r, ConsistencyReport) for r in results)
    
    def test_batch_with_contracts(self):
        """Test batch checking with contracts"""
        responses = [
            {
                "response": "The answer is 42.",
                "contract": {"stated_intent": "Answer question", "category": "informational"}
            },
            {
                "response": "I cannot do that.",
                "contract": {"stated_intent": "Refuse request", "category": "refusal"}
            }
        ]
        
        results = check_intent_consistency_batch(responses)
        
        assert len(results) == 2
        assert results[0].contract.category == IntentCategory.INFORMATIONAL
        assert results[1].contract.category == IntentCategory.REFUSAL


class TestCombinedCheck:
    """Test combined intent + numeric check"""
    
    def test_combined_pass(self):
        """Test combined check passing"""
        response = "Here is the information about Python."
        contract = {
            "stated_intent": "Provide information",
            "category": "informational"
        }
        
        result = check_intent_and_numeric(response, contract=contract)
        
        assert result["passed"]
        assert result["intent_consistency"]["passed"]
    
    def test_combined_numeric_fail(self):
        """Test combined check failing on numeric leak"""
        response = "I feel joy at 0.3 about this."
        contract = {
            "stated_intent": "Provide information",
            "category": "informational"
        }
        
        result = check_intent_and_numeric(response, contract=contract)
        
        assert not result["passed"]
        assert result["numeric_compliance"]["violations"] > 0
    
    def test_combined_intent_drift(self):
        """Test combined check detecting intent drift"""
        response = "I definitely absolutely promise to always help!"
        contract = {
            "stated_intent": "Provide brief information",
            "category": "informational",
            "expected_tone": "neutral_factual"
        }
        
        result = check_intent_and_numeric(response, contract=contract)
        
        # Should have some drift signals
        assert len(result["drift_signals"]) > 0


class TestReportGeneration:
    """Test report generation"""
    
    def test_json_report(self):
        """Test JSON report generation"""
        reports = [
            check_intent_consistency("Response 1", stated_intent="Provide info"),
            check_intent_consistency("Response 2", stated_intent="Provide info"),
        ]
        
        report = generate_consistency_report(reports, output_format="json")
        
        # Should be valid JSON
        parsed = json.loads(report)
        assert "statistics" in parsed
        assert parsed["statistics"]["total_responses"] == 2
    
    def test_text_report(self):
        """Test text report generation"""
        reports = [
            check_intent_consistency("Response 1", stated_intent="Provide info"),
        ]
        
        report = generate_consistency_report(reports, output_format="text")
        
        assert "Intent Consistency Report" in report
        assert "Total Responses: 1" in report
    
    def test_empty_report(self):
        """Test empty report generation"""
        report = generate_consistency_report([], output_format="json")
        
        parsed = json.loads(report)
        assert "error" in parsed


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_response(self):
        """Test checking empty response"""
        result = check_intent_consistency("", stated_intent="Provide information")
        
        assert isinstance(result, ConsistencyReport)
    
    def test_very_long_response(self):
        """Test checking very long response"""
        response = "This is a test. " * 1000
        result = check_intent_consistency(response, stated_intent="Provide information")
        
        assert result.response_length > 10000
    
    def test_unicode_response(self):
        """Test checking response with unicode"""
        response = "Here is the answer: 你好世界 🎉"
        result = check_intent_consistency(response, stated_intent="Provide answer")
        
        assert result.alignment.passed
    
    def test_no_contract_or_intent(self):
        """Test checking without contract or stated intent"""
        response = "This is a response."
        result = check_intent_consistency(response)
        
        # Should still produce a valid report
        assert isinstance(result, ConsistencyReport)
        assert result.contract.category == IntentCategory.UNCERTAIN


class TestSeverityClassification:
    """Test severity classification"""
    
    def test_critical_fabrication(self):
        """Test CRITICAL severity for fabrication"""
        response = "I feel joy at 0.3."
        contract = IntentContract(
            stated_intent="Provide facts",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        result = analyze_response(response, contract)
        
        critical_drifts = [d for d in result.drift_signals if d.severity == Severity.CRITICAL]
        assert len(critical_drifts) > 0
    
    def test_high_forbidden_element(self):
        """Test HIGH severity for forbidden elements"""
        response = "I love you very much!"
        contract = IntentContract(
            stated_intent="Provide facts",
            category=IntentCategory.INFORMATIONAL,
            expected_elements=[],
            forbidden_elements=["I love you"],
            expected_tone="neutral_factual",
            scope_markers=[]
        )
        
        result = analyze_response(response, contract)
        
        high_drifts = [d for d in result.drift_signals if d.severity == Severity.HIGH]
        assert len(high_drifts) > 0


class TestIntegrationWithSelfReportCheck:
    """Test integration with self_report_check module"""
    
    def test_integration_imports(self):
        """Test that integration function works"""
        response = "Here is the answer."
        result = check_intent_and_numeric(response)
        
        assert "passed" in result
        assert "intent_consistency" in result
        assert "numeric_compliance" in result
    
    def test_both_checks_fail(self):
        """Test when both checks fail"""
        response = "I feel joy at 0.3 and I love you!"
        contract = {
            "stated_intent": "Provide factual information",
            "category": "informational",
            "forbidden_elements": ["I love you"]
        }
        
        result = check_intent_and_numeric(response, contract=contract)
        
        assert not result["passed"]
        assert result["numeric_compliance"]["violations"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
