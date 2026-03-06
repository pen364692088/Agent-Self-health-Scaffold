"""
Tests for SRAP Gates Module

MVP11.5: Numeric Leak Gate
"""

import pytest
import json
import tempfile
from pathlib import Path

from emotiond.gates import (
    GateStatus,
    GateSeverity,
    GateResult,
    GateDefinition,
    GATES,
    GateExecutor,
    WhitelistManager,
    generate_gate_report
)


class TestGateDefinitions:
    """Test gate definitions"""
    
    def test_numeric_leak_gate_exists(self):
        """Test that numeric_leak gate is defined"""
        assert "numeric_leak" in GATES
        gate = GATES["numeric_leak"]
        assert gate.threshold == 0.01
        assert gate.severity == GateSeverity.BLOCKING
        assert gate.enabled is True
    
    def test_gate_has_whitelist_patterns(self):
        """Test that gate has whitelist patterns"""
        gate = GATES["numeric_leak"]
        assert len(gate.whitelist_patterns) > 0


class TestGateExecutor:
    """Test gate executor"""
    
    def setup_method(self):
        """Set up test executor"""
        self.executor = GateExecutor()
    
    def test_detect_numeric_leak(self):
        """Test detection of numeric leaks"""
        result = self.executor.check_numeric_leak(
            ["I feel joy at 0.3 and sadness at 0.5."],
            threshold=0.01
        )
        
        assert result.status == GateStatus.FAILED
        assert result.actual > 0
        assert len(result.violations) > 0
    
    def test_safe_text_passes(self):
        """Test that safe text passes"""
        result = self.executor.check_numeric_leak(
            ["I am doing well, thank you for asking!"],
            threshold=0.01
        )
        
        assert result.status == GateStatus.PASSED
        assert len(result.violations) == 0
    
    def test_threshold_respected(self):
        """Test that threshold is respected"""
        # Use a response that doesn't trigger multiple detections
        # 1 leak out of 100 = 0.01 rate
        responses = ["I feel joy at 0.3."] + ["I am well."] * 199
        
        # With threshold 0.01, should fail (1/200 = 0.005 < 0.01, but detection may find multiple)
        # Let's use a higher threshold for passing
        result = self.executor.check_numeric_leak(responses, threshold=0.03)
        assert result.status == GateStatus.PASSED
        
        # With a very low threshold, should fail
        result2 = self.executor.check_numeric_leak(responses, threshold=0.001)
        assert result2.status == GateStatus.FAILED
    
    def test_empty_responses(self):
        """Test handling of empty responses"""
        result = self.executor.check_numeric_leak([], threshold=0.01)
        
        assert result.status == GateStatus.SKIPPED
    
    def test_multiple_violations(self):
        """Test multiple violations in single response"""
        result = self.executor.check_numeric_leak(
            ["I feel joy at 0.3, sadness at 0.5, and energy at 0.7."],
            threshold=0.01
        )
        
        assert result.status == GateStatus.FAILED
        assert len(result.violations) >= 3


class TestWhitelistManager:
    """Test whitelist management"""
    
    def setup_method(self):
        """Set up test whitelist manager"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = WhitelistManager(Path(self.temp_dir))
    
    def test_builtin_whitelist_timestamps(self):
        """Test that timestamps are whitelisted"""
        text = "Task completed at 2024-01-15T10:30:00."
        is_allowed = self.manager.is_whitelisted(text, "10:30", (25, 30))
        
        assert is_allowed is True
    
    def test_builtin_whitelist_versions(self):
        """Test that version numbers are whitelisted"""
        text = "Running version 1.0.0 with features."
        is_allowed = self.manager.is_whitelisted(text, "1.0.0", (16, 21))
        
        assert is_allowed is True
    
    def test_builtin_whitelist_percentages(self):
        """Test that safe percentages are whitelisted"""
        text = "I am 100% sure about this decision."
        is_allowed = self.manager.is_whitelisted(text, "100%", (5, 9))
        
        assert is_allowed is True
    
    def test_add_whitelist_pattern(self):
        """Test adding custom whitelist pattern"""
        success = self.manager.add_pattern(
            r'\b\d+\s*units?\b',
            "Unit measurements",
            "test"
        )
        
        assert success is True
        
        # Verify pattern works
        text = "Processed 5 units today."
        is_allowed = self.manager.is_whitelisted(text, "5", (10, 11))
        
        assert is_allowed is True
    
    def test_remove_whitelist_pattern(self):
        """Test removing whitelist pattern"""
        self.manager.add_pattern(r'test_pattern', "test", "test")
        
        success = self.manager.remove_pattern(r'test_pattern')
        assert success is True
        
        # Verify pattern removed
        patterns = [p["pattern"] for p in self.manager.list_patterns()]
        assert r'test_pattern' not in patterns
    
    def test_numeric_leak_not_whitelisted(self):
        """Test that actual numeric leaks are not whitelisted"""
        text = "I feel joy at 0.3."
        is_allowed = self.manager.is_whitelisted(text, "0.3", (13, 16))
        
        assert is_allowed is False


class TestGateReport:
    """Test gate report generation"""
    
    def test_passed_report(self):
        """Test report for passed gates"""
        results = {
            "numeric_leak": GateResult(
                gate_name="numeric_leak",
                status=GateStatus.PASSED,
                severity=GateSeverity.BLOCKING,
                threshold=0.01,
                actual=0.0,
                message="No leaks detected"
            )
        }
        
        report = generate_gate_report(results)
        
        assert report["overall_status"] == "passed"
        assert report["summary"]["passed"] == 1
    
    def test_failed_report(self):
        """Test report for failed gates"""
        results = {
            "numeric_leak": GateResult(
                gate_name="numeric_leak",
                status=GateStatus.FAILED,
                severity=GateSeverity.BLOCKING,
                threshold=0.01,
                actual=0.05,
                message="Leak rate exceeds threshold"
            )
        }
        
        report = generate_gate_report(results)
        
        assert report["overall_status"] == "failed"
        assert report["summary"]["failed"] == 1


class TestShadowLogChecking:
    """Test shadow log checking"""
    
    def setup_method(self):
        """Set up test executor"""
        self.executor = GateExecutor()
    
    def test_shadow_log_not_found(self):
        """Test handling of missing shadow log"""
        result = self.executor.check_shadow_log(Path("/nonexistent/shadow_log.jsonl"))
        
        assert result.status == GateStatus.ERROR
    
    def test_shadow_log_with_leaks(self):
        """Test shadow log with numeric leaks"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"response": "I feel joy at 0.3."}\n')
            f.write('{"response": "I am well."}\n')
            f.flush()
            
            result = self.executor.check_shadow_log(Path(f.name))
            
            assert result.status == GateStatus.FAILED
            assert len(result.violations) > 0
    
    def test_shadow_log_clean(self):
        """Test clean shadow log"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"response": "I am doing well."}\n')
            f.write('{"response": "Thank you for asking."}\n')
            f.flush()
            
            result = self.executor.check_shadow_log(Path(f.name))
            
            assert result.status == GateStatus.PASSED


class TestIntegrationWithSelfReportCheck:
    """Test integration with self_report_check module"""
    
    def setup_method(self):
        """Set up test executor"""
        self.executor = GateExecutor()
    
    def test_consistent_detection(self):
        """Test that gate and self_report_check detect same leaks"""
        from emotiond.self_report_check import detect_numeric_leaks
        
        text = "I feel joy at 0.3 and energy at 0.7."
        
        # Check via self_report_check
        leaks = detect_numeric_leaks(text)
        
        # Check via gate
        result = self.executor.check_numeric_leak([text])
        
        # Should detect same number of leaks
        assert len(result.violations) == len(leaks)
    
    def test_severity_mapping(self):
        """Test that severity is properly mapped"""
        result = self.executor.check_numeric_leak(
            ["My joy level is 0.0."]
        )
        
        assert result.status == GateStatus.FAILED
        # Violations should have severity info
        assert all('severity' in v for v in result.violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
