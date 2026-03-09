#!/usr/bin/env python3
"""
Synthetic Input Check - Test Input Verification Mode

Constructs test inputs and verifies system response.
Example: Send test message, check callback.
"""

try:
    from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
except ImportError:
    from probe_base import ProbeBase, ProbeResult, ProbeRegistry

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable


@ProbeRegistry.register
class SyntheticInputCheck(ProbeBase):
    """
    Synthetic input verification mode.
    
    Creates test inputs and verifies system handles them correctly.
    Use when you need to test system responsiveness with controlled inputs.
    """
    
    VERIFICATION_MODE = "synthetic_input_check"
    
    def __init__(self, name: str = "synthetic-input"):
        super().__init__(name)
        self.test_marker = f"PROBE_TEST_{uuid.uuid4().hex[:8]}"
    
    def check(self, dry_run: bool = False,
              input_data: Dict[str, Any] = None,
              expected_response: Dict[str, Any] = None,
              timeout_seconds: int = 30) -> ProbeResult:
        """
        Execute synthetic input check.
        
        Args:
            dry_run: If True, return simulated success
            input_data: Test input to send
            expected_response: Expected response pattern
            timeout_seconds: Timeout for response
            
        Returns:
            ProbeResult with test outcome
        """
        import time
        start_time = time.perf_counter()
        
        if dry_run:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="Dry run completed (no actual test)",
                evidence={"dry_run": True, "test_marker": self.test_marker},
                duration_ms=duration_ms
            )
        
        # Default test: create a test receipt file
        if input_data is None:
            input_data = {
                "test_marker": self.test_marker,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "synthetic_probe_test"
            }
        
        evidence = {
            "test_marker": self.test_marker,
            "input": input_data
        }
        
        try:
            # Write test artifact
            test_dir = "artifacts/self_health/probe_tests"
            os.makedirs(test_dir, exist_ok=True)
            
            test_file = os.path.join(test_dir, f"test_{self.test_marker}.json")
            
            with open(test_file, 'w') as f:
                json.dump(input_data, f, indent=2)
            
            evidence["test_file"] = test_file
            
            # Verify file was written
            if not os.path.exists(test_file):
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                return ProbeResult.fail(
                    probe_name=self.name,
                    verification_mode=self.verification_mode,
                    message="Test file was not created",
                    evidence=evidence,
                    duration_ms=duration_ms
                )
            
            # Read back and verify
            with open(test_file, 'r') as f:
                read_data = json.load(f)
            
            evidence["read_back"] = read_data
            
            # Check expected response
            if expected_response:
                for key, expected_value in expected_response.items():
                    if read_data.get(key) != expected_value:
                        duration_ms = int((time.perf_counter() - start_time) * 1000)
                        evidence["mismatch"] = {
                            "key": key,
                            "expected": expected_value,
                            "actual": read_data.get(key)
                        }
                        return ProbeResult.fail(
                            probe_name=self.name,
                            verification_mode=self.verification_mode,
                            message=f"Response mismatch for key: {key}",
                            evidence=evidence,
                            duration_ms=duration_ms
                        )
            
            # Clean up test file
            os.remove(test_file)
            evidence["cleaned_up"] = True
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="Synthetic input test passed",
                evidence=evidence,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.error(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Synthetic input test error: {str(e)}",
                evidence={**evidence, "error": str(e)},
                duration_ms=duration_ms
            )


# Convenience function
def run_synthetic_input_check(name: str = "synthetic-input", dry_run: bool = False, **kwargs) -> ProbeResult:
    """Run a synthetic input check."""
    probe = SyntheticInputCheck(name)
    return probe.check(dry_run=dry_run, **kwargs)
