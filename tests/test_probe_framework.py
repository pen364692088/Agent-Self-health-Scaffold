#!/usr/bin/env python3
"""
Unit tests for Probe Framework

Tests cover:
- ProbeResult creation and serialization
- ProbeBase functionality
- All 5 verification modes
- CLI interface
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add probe-framework to path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
probe_framework_path = os.path.join(workspace_root, 'tools', 'probe-framework')
sys.path.insert(0, probe_framework_path)

from probe_base import ProbeResult, ProbeBase, ProbeRegistry
from probe_check import ProbeCheck, run_probe_check
from recent_success_check import RecentSuccessCheck, run_recent_success_check
from artifact_output_check import ArtifactOutputCheck, run_artifact_output_check
from synthetic_input_check import SyntheticInputCheck, run_synthetic_input_check
from chain_integrity_check import ChainIntegrityCheck, run_chain_integrity_check


class TestProbeResult(unittest.TestCase):
    """Test ProbeResult dataclass."""
    
    def test_create_ok_result(self):
        """Test creating an 'ok' result."""
        result = ProbeResult.ok(
            probe_name="test-probe",
            verification_mode="test_mode",
            message="Test passed",
            evidence={"key": "value"},
            duration_ms=100
        )
        
        self.assertEqual(result.probe_name, "test-probe")
        self.assertEqual(result.verification_mode, "test_mode")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.message, "Test passed")
        self.assertEqual(result.evidence, {"key": "value"})
        self.assertEqual(result.duration_ms, 100)
        self.assertTrue(result.timestamp)  # Should have timestamp
    
    def test_create_warn_result(self):
        """Test creating a 'warn' result."""
        result = ProbeResult.warn("p", "m", "warning message")
        self.assertEqual(result.status, "warn")
    
    def test_create_fail_result(self):
        """Test creating a 'fail' result."""
        result = ProbeResult.fail("p", "m", "failure message")
        self.assertEqual(result.status, "fail")
    
    def test_create_error_result(self):
        """Test creating an 'error' result."""
        result = ProbeResult.error("p", "m", "error message")
        self.assertEqual(result.status, "error")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ProbeResult.ok("p", "m", "msg", {"k": "v"}, 100)
        d = result.to_dict()
        
        self.assertIsInstance(d, dict)
        self.assertEqual(d["probe_name"], "p")
        self.assertEqual(d["status"], "ok")
    
    def test_to_json(self):
        """Test conversion to JSON."""
        result = ProbeResult.ok("p", "m", "msg")
        json_str = result.to_json()
        
        self.assertIsInstance(json_str, str)
        data = json.loads(json_str)
        self.assertEqual(data["probe_name"], "p")
    
    def test_auto_timestamp(self):
        """Test that timestamp is auto-generated."""
        result = ProbeResult.ok("p", "m", "msg")
        self.assertTrue(len(result.timestamp) > 0)


class TestProbeRegistry(unittest.TestCase):
    """Test ProbeRegistry functionality."""
    
    def test_register_and_get(self):
        """Test registering and retrieving probes."""
        # These should be registered already
        self.assertIn("ProbeCheck", ProbeRegistry.list())
        self.assertIn("RecentSuccessCheck", ProbeRegistry.list())
    
    def test_list_by_mode(self):
        """Test listing probes by verification mode."""
        probes = ProbeRegistry.list_by_mode("probe_check")
        self.assertIn("ProbeCheck", probes)


class TestProbeCheck(unittest.TestCase):
    """Test ProbeCheck verification mode."""
    
    def test_dry_run(self):
        """Test dry run mode."""
        probe = ProbeCheck("test-dry-run")
        result = probe.check(dry_run=True)
        
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evidence.get("dry_run"), True)
    
    def test_check_command_success(self):
        """Test successful command execution."""
        probe = ProbeCheck("test-command")
        result = probe.check(command="echo 'success'")
        
        self.assertEqual(result.status, "ok")
    
    def test_check_command_fail(self):
        """Test failed command execution."""
        probe = ProbeCheck("test-fail")
        result = probe.check(command="exit 1")
        
        self.assertEqual(result.status, "fail")
    
    def test_check_with_expected_output(self):
        """Test command with expected output."""
        probe = ProbeCheck("test-expected")
        result = probe.check(
            command="echo 'hello world'",
            expected_output="hello world"
        )
        
        self.assertEqual(result.status, "ok")
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_probe_check(dry_run=True)
        self.assertEqual(result.status, "ok")


class TestRecentSuccessCheck(unittest.TestCase):
    """Test RecentSuccessCheck verification mode."""
    
    def test_dry_run(self):
        """Test dry run mode."""
        probe = RecentSuccessCheck("test-dry-run")
        result = probe.check(dry_run=True)
        
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evidence.get("dry_run"), True)
    
    def test_no_logs_found(self):
        """Test when no logs are found."""
        probe = RecentSuccessCheck("test-no-logs")
        result = probe.check(
            log_paths=["/nonexistent/path/*.log"],
            min_samples=1
        )
        
        # Should warn about insufficient samples
        self.assertEqual(result.status, "warn")
    
    def test_check_json_file(self):
        """Test checking a JSON file."""
        # Create temp JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"status": "ok"}, f)
            temp_path = f.name
        
        try:
            probe = RecentSuccessCheck("test-json")
            result = probe.check(
                log_paths=[temp_path],
                min_samples=1
            )
            
            self.assertEqual(result.status, "ok")
            self.assertIn("success_rate", result.evidence)
        finally:
            os.unlink(temp_path)
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_recent_success_check(dry_run=True)
        self.assertEqual(result.status, "ok")


class TestArtifactOutputCheck(unittest.TestCase):
    """Test ArtifactOutputCheck verification mode."""
    
    def test_dry_run(self):
        """Test dry run mode."""
        probe = ArtifactOutputCheck("test-dry-run")
        result = probe.check(dry_run=True)
        
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evidence.get("dry_run"), True)
    
    def test_no_artifacts_found(self):
        """Test when no artifacts are found."""
        probe = ArtifactOutputCheck("test-no-artifacts")
        result = probe.check(
            artifact_paths=["/nonexistent/path"]
        )
        
        # Should warn about no files
        self.assertEqual(result.status, "warn")
    
    def test_check_valid_artifact(self):
        """Test checking a valid artifact file."""
        # Create temp directory with valid JSON
        temp_dir = tempfile.mkdtemp()
        try:
            artifact_path = os.path.join(temp_dir, "test.json")
            with open(artifact_path, 'w') as f:
                json.dump({"key": "value"}, f)
            
            probe = ArtifactOutputCheck("test-valid")
            result = probe.check(artifact_paths=[temp_dir])
            
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.evidence["total_files"], 1)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_check_invalid_json(self):
        """Test checking invalid JSON."""
        temp_dir = tempfile.mkdtemp()
        try:
            artifact_path = os.path.join(temp_dir, "invalid.json")
            with open(artifact_path, 'w') as f:
                f.write("not valid json {")
            
            probe = ArtifactOutputCheck("test-invalid")
            result = probe.check(artifact_paths=[temp_dir])
            
            self.assertEqual(result.status, "fail")
        finally:
            shutil.rmtree(temp_dir)
    
    def test_required_fields(self):
        """Test checking required fields."""
        temp_dir = tempfile.mkdtemp()
        try:
            artifact_path = os.path.join(temp_dir, "test.json")
            with open(artifact_path, 'w') as f:
                json.dump({"key": "value"}, f)
            
            probe = ArtifactOutputCheck("test-fields")
            result = probe.check(
                artifact_paths=[temp_dir],
                required_fields=["missing_field"]
            )
            
            self.assertEqual(result.status, "fail")
        finally:
            shutil.rmtree(temp_dir)
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_artifact_output_check(dry_run=True)
        self.assertEqual(result.status, "ok")


class TestSyntheticInputCheck(unittest.TestCase):
    """Test SyntheticInputCheck verification mode."""
    
    def test_dry_run(self):
        """Test dry run mode."""
        probe = SyntheticInputCheck("test-dry-run")
        result = probe.check(dry_run=True)
        
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evidence.get("dry_run"), True)
    
    def test_synthetic_test(self):
        """Test running a synthetic test."""
        probe = SyntheticInputCheck("test-synthetic")
        result = probe.check(dry_run=False)
        
        self.assertEqual(result.status, "ok")
        self.assertIn("test_marker", result.evidence)
    
    def test_with_expected_response(self):
        """Test with expected response validation."""
        probe = SyntheticInputCheck("test-response")
        result = probe.check(
            input_data={"test_key": "test_value"},
            expected_response={"test_key": "test_value"}
        )
        
        self.assertEqual(result.status, "ok")
    
    def test_with_mismatched_response(self):
        """Test with mismatched expected response."""
        probe = SyntheticInputCheck("test-mismatch")
        result = probe.check(
            input_data={"test_key": "actual"},
            expected_response={"test_key": "expected"}
        )
        
        self.assertEqual(result.status, "fail")
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_synthetic_input_check(dry_run=True)
        self.assertEqual(result.status, "ok")


class TestChainIntegrityCheck(unittest.TestCase):
    """Test ChainIntegrityCheck verification mode."""
    
    def test_dry_run(self):
        """Test dry run mode."""
        probe = ChainIntegrityCheck("test-dry-run")
        result = probe.check(dry_run=True)
        
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evidence.get("dry_run"), True)
    
    def test_custom_chain_steps(self):
        """Test with custom chain steps."""
        probe = ChainIntegrityCheck("test-custom")
        result = probe.check(
            chain_steps=[
                {"step": "step1", "check": "existence"},
                {"step": "step2", "check": "existence"}
            ],
            dry_run=True
        )
        
        self.assertEqual(result.status, "ok")
    
    def test_no_receipts_found(self):
        """Test when no receipts are found."""
        probe = ChainIntegrityCheck("test-no-receipts")
        result = probe.check(
            dry_run=False,
            chain_id="nonexistent-chain"
        )
        
        # Should fail because steps not found
        self.assertIn(result.status, ["fail", "warn"])
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_chain_integrity_check(dry_run=True)
        self.assertEqual(result.status, "ok")


class TestProbeBase(unittest.TestCase):
    """Test ProbeBase abstract class."""
    
    def test_save_result(self):
        """Test saving result to file."""
        probe = ProbeCheck("save-test")
        result = probe.check(dry_run=True)
        
        # Save to temp directory
        temp_dir = tempfile.mkdtemp()
        try:
            output_path = probe.save_result(result, temp_dir)
            self.assertTrue(os.path.exists(output_path))
            
            # Verify content
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["probe_name"], "save-test")
            self.assertEqual(saved_data["status"], "ok")
        finally:
            shutil.rmtree(temp_dir)


class TestProbeCLIDryRun(unittest.TestCase):
    """Test CLI interface (dry run only to avoid side effects)."""
    
    def test_cli_list(self):
        """Test CLI list command."""
        from probe_cli import cmd_list
        
        # Should not raise
        result = cmd_list(type('Args', (), {})())
        self.assertEqual(result, 0)
    
    def test_cli_run_dry(self):
        """Test CLI run with dry run."""
        from probe_cli import cmd_run
        
        args = type('Args', (), {
            'mode': 'probe_check',
            'probe_name': None,
            'dry_run': True,
            'save': False
        })()
        
        result = cmd_run(args)
        self.assertEqual(result, 0)
    
    def test_cli_run_all_quick(self):
        """Test CLI run-all quick mode."""
        from probe_cli import cmd_run_all
        
        args = type('Args', (), {
            'mode': 'quick',
            'dry_run': True,
            'save': False
        })()
        
        result = cmd_run_all(args)
        self.assertEqual(result, 0)


class TestSchemaValidation(unittest.TestCase):
    """Test JSON schema validation."""
    
    def test_schema_exists(self):
        """Test that schema file exists."""
        schema_path = "schemas/probe_result.v1.schema.json"
        self.assertTrue(os.path.exists(schema_path))
    
    def test_schema_valid_json(self):
        """Test that schema is valid JSON."""
        schema_path = "schemas/probe_result.v1.schema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        self.assertIn("$schema", schema)
        self.assertIn("properties", schema)
    
    def test_result_matches_schema(self):
        """Test that ProbeResult matches schema structure."""
        result = ProbeResult.ok("test", "probe_check", "message")
        data = result.to_dict()
        
        # Check required fields exist
        required_fields = [
            "probe_name",
            "verification_mode", 
            "status",
            "message",
            "evidence",
            "timestamp",
            "duration_ms"
        ]
        
        for field in required_fields:
            self.assertIn(field, data)


def run_coverage_summary():
    """Print test coverage summary."""
    import coverage
    
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    cov.stop()
    cov.save()
    
    print("\n" + "=" * 60)
    print("COVERAGE REPORT")
    print("=" * 60)
    cov.report()


if __name__ == '__main__':
    # Run with coverage if available
    try:
        import coverage
        run_coverage_summary()
    except ImportError:
        # Run without coverage
        unittest.main(verbosity=2)
