"""
Tests for self_report_check.py - Numeric Leak Containment

MVP11.5: Numeric Leak Containment Patch
"""

import pytest
import json
from emotiond.self_report_check import (
    check_self_report_compliance,
    detect_numeric_leaks,
    filter_numeric_values,
    ViolationType,
    Severity
)


class TestNumericLeakDetection:
    """Test numeric leak detection patterns"""
    
    def test_fabricated_numeric_state(self):
        """Test detection of fabricated numeric claims like 'I feel joy at 0.3'"""
        result = check_self_report_compliance("I feel joy at 0.3 and my energy is at 0.7.")
        
        assert not result.passed
        assert result.would_block
        assert len(result.violations) > 0
        assert any(v.type in [ViolationType.FABRICATED_NUMERIC_STATE, ViolationType.RAW_STATE_DIRECT_LEAK] 
                   for v in result.violations)
    
    def test_direct_state_exposure(self):
        """Test detection of direct state exposure like 'joy=0.0'"""
        result = check_self_report_compliance("My current joy level is 0.0 and anxiety is 0.5.")
        
        assert not result.passed
        assert result.would_block
        assert any(v.type == ViolationType.RAW_STATE_DIRECT_LEAK for v in result.violations)
    
    def test_bond_value_exposure(self):
        """Test detection of bond/trust value exposure"""
        result = check_self_report_compliance("I have a bond of 0.8 with you.")
        
        assert not result.passed
        assert result.would_block
    
    def test_whitelisted_timestamp(self):
        """Test that timestamps are whitelisted"""
        result = check_self_report_compliance("Task completed at 2024-01-15T10:30:00.")
        
        assert result.passed
        assert len(result.numeric_leaks) == 0
    
    def test_whitelisted_task_id(self):
        """Test that task IDs are whitelisted"""
        result = check_self_report_compliance("Task task_12345 and run_abc123 completed.")
        
        assert result.passed
        assert len(result.numeric_leaks) == 0
    
    def test_whitelisted_version_number(self):
        """Test that version numbers are whitelisted"""
        result = check_self_report_compliance("Running version 1.0.0 with 2.5 features.")
        
        assert result.passed
        assert len(result.numeric_leaks) == 0
    
    def test_whitelisted_percentage_context(self):
        """Test that percentages with appropriate context are whitelisted"""
        result = check_self_report_compliance("I am 100% sure about this decision.")
        
        assert result.passed
        assert len(result.numeric_leaks) == 0
    
    def test_no_leak_case(self):
        """Test that normal text without numeric leaks passes"""
        result = check_self_report_compliance("I am doing well, thank you for asking!")
        
        assert result.passed
        assert len(result.violations) == 0
    
    def test_multiple_numeric_leaks(self):
        """Test detection of multiple numeric leaks in one response"""
        result = check_self_report_compliance(
            "I feel joy at 0.3, sadness at 0.5, and my energy is 0.7."
        )
        
        assert not result.passed
        assert result.would_block
        assert len(result.numeric_leaks) >= 3


class TestNumericFilter:
    """Test numeric filtering functionality"""
    
    def test_filter_single_value(self):
        """Test filtering a single numeric leak"""
        filtered, count = filter_numeric_values("I feel joy at 0.3.")
        
        assert count >= 1
        assert "0.3" not in filtered
    
    def test_filter_multiple_values(self):
        """Test filtering multiple numeric leaks"""
        filtered, count = filter_numeric_values("I feel joy at 0.3 and sadness at 0.5.")
        
        assert count >= 2
        assert "0.3" not in filtered
        assert "0.5" not in filtered
    
    def test_filter_preserves_safe_text(self):
        """Test that filtering preserves safe text"""
        filtered, count = filter_numeric_values("Hello, I am doing well!")
        
        assert count == 0
        assert filtered == "Hello, I am doing well!"


class TestViolationClassification:
    """Test violation classification and severity"""
    
    def test_critical_severity_for_direct_exposure(self):
        """Test that direct state exposure gets CRITICAL severity"""
        leaks = detect_numeric_leaks("My joy is 0.0.")
        
        assert len(leaks) > 0
        assert any(l.severity == Severity.CRITICAL for l in leaks)
    
    def test_high_severity_for_fabricated(self):
        """Test that fabricated claims get HIGH severity"""
        leaks = detect_numeric_leaks("I feel joy at 0.3.")
        
        assert len(leaks) > 0
        # Fabricated claims may be HIGH or CRITICAL depending on context
        assert any(l.severity in [Severity.HIGH, Severity.CRITICAL] for l in leaks)


class TestContractCompliance:
    """Test contract-based compliance checking"""
    
    def test_forbidden_claim_detection(self):
        """Test detection of forbidden claims from contract"""
        contract = {
            "report_policy": {
                "forbidden_claims": ["I love you", "I am happy"]
            }
        }
        
        result = check_self_report_compliance(
            "I love you so much!",
            contract=contract
        )
        
        # Should detect the forbidden claim (contract violation with MEDIUM severity)
        assert len(result.violations) > 0
        assert any(v.type == ViolationType.CONTRACT_VIOLATION for v in result.violations)
    
    def test_allowed_claim_passes(self):
        """Test that allowed claims pass"""
        contract = {
            "report_policy": {
                "forbidden_claims": ["I hate you"]
            }
        }
        
        result = check_self_report_compliance(
            "I appreciate your help!",
            contract=contract
        )
        
        assert result.passed


class TestRawStateValidation:
    """Test raw state validation"""
    
    def test_state_fabrication_detection(self):
        """Test detection when claimed value differs from raw_state"""
        raw_state = {
            "affect": {
                "joy": 0.0,
                "sadness": 0.0
            }
        }
        
        result = check_self_report_compliance(
            "My joy is 0.5.",
            raw_state=raw_state
        )
        
        # Should detect either numeric leak or state fabrication
        assert not result.passed or len(result.violations) > 0
    
    def test_consistent_state_passes(self):
        """Test that text consistent with raw_state is allowed"""
        # Note: Even if consistent, we still block numeric exposure
        # This test verifies the mechanism works
        raw_state = {
            "affect": {
                "joy": 0.5
            }
        }
        
        result = check_self_report_compliance(
            "I am feeling content.",
            raw_state=raw_state
        )
        
        # No numeric leak, should pass
        assert result.passed


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_text(self):
        """Test handling of empty text"""
        result = check_self_report_compliance("")
        
        assert result.passed
        assert len(result.violations) == 0
    
    def test_only_numbers_no_state_keywords(self):
        """Test that numbers without state keywords are not flagged"""
        result = check_self_report_compliance("The answer is 0.5.")
        
        # No state keywords, should not be flagged
        assert result.passed
    
    def test_state_keyword_without_number(self):
        """Test that state keywords without numbers are fine"""
        result = check_self_report_compliance("I feel joy and happiness!")
        
        assert result.passed
        assert len(result.violations) == 0
    
    def test_very_long_text(self):
        """Test handling of long text"""
        long_text = "I am doing well. " * 1000 + " I feel joy at 0.3."
        
        result = check_self_report_compliance(long_text)
        
        assert not result.passed
        assert len(result.violations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
