"""
Execution Policy E2E Tests

End-to-end tests for execution policy enforcement.
Tests behavior-level verification for Gate B.

Run with: pytest tests/e2e/test_execution_policy_e2e.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Tools paths
TOOLS_DIR = Path.home() / ".openclaw" / "workspace" / "tools"
POLICY_EVAL = TOOLS_DIR / "policy-eval"
POLICY_DOCTOR = TOOLS_DIR / "policy-doctor"
SAFE_WRITE = TOOLS_DIR / "safe-write"
SAFE_REPLACE = TOOLS_DIR / "safe-replace"


class TestPolicyEvalE2E:
    """E2E tests for policy-eval tool."""
    
    def test_policy_eval_blocks_edit_on_sensitive_path(self):
        """Test policy-eval blocks edit tool on ~/.openclaw/** paths."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "~/.openclaw/workspace/SOUL.md", "--tool", "edit", "--json"],
            capture_output=True,
            text=True
        )
        
        # Should exit with error (deny)
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
        
        output = json.loads(result.stdout)
        assert output["decision"] == "deny"
        assert output["rule_id"] == "OPENCLAW_PATH_NO_EDIT"
    
    def test_policy_eval_warns_on_write_sensitive(self):
        """Test policy-eval warns on write to sensitive path."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "~/.openclaw/test.txt", "--tool", "write", "--json"],
            capture_output=True,
            text=True
        )
        
        # Should exit with success (warn)
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        assert output["decision"] == "warn"
    
    def test_policy_eval_allows_non_sensitive(self):
        """Test policy-eval allows operations on non-sensitive paths."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "/tmp/test.txt", "--tool", "edit", "--json"],
            capture_output=True,
            text=True
        )
        
        # Should exit with success
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        assert output["decision"] == "allow"
    
    def test_policy_eval_allows_safe_tools(self):
        """Test policy-eval allows safe tools on sensitive paths."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "~/.openclaw/test.txt", "--tool", "exec", "--json"],
            capture_output=True,
            text=True
        )
        
        # Should exit with success
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        assert output["decision"] == "allow"


class TestSafeWriteE2E:
    """E2E tests for safe-write tool."""
    
    def test_safe_write_creates_file(self):
        """Test safe-write creates file atomically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            result = subprocess.run(
                [str(SAFE_WRITE), str(test_file), "Hello, World!", "--json"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert test_file.exists()
            assert test_file.read_text() == "Hello, World!"
    
    def test_safe_write_overwrites_existing(self):
        """Test safe-write overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("old content")
            
            result = subprocess.run(
                [str(SAFE_WRITE), str(test_file), "new content", "--json"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert test_file.read_text() == "new content"
    
    def test_safe_write_includes_hash(self):
        """Test safe-write returns hash verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            result = subprocess.run(
                [str(SAFE_WRITE), str(test_file), "content", "--json"],
                capture_output=True,
                text=True
            )
            
            output = json.loads(result.stdout)
            assert output["success"] is True
            assert "hash" in output


class TestSafeReplaceE2E:
    """E2E tests for safe-replace tool."""
    
    def test_safe_replace_replaces_content(self):
        """Test safe-replace replaces content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")
            
            result = subprocess.run(
                [str(SAFE_REPLACE), str(test_file), "World", "Universe", "--json"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert test_file.read_text() == "Hello, Universe!"
    
    def test_safe_replace_fails_if_not_found(self):
        """Test safe-replace fails if old string not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")
            
            result = subprocess.run(
                [str(SAFE_REPLACE), str(test_file), "NotPresent", "New", "--json"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 1
            output = json.loads(result.stdout)
            assert output["success"] is False
    
    def test_safe_replace_counts_replacements(self):
        """Test safe-replace counts replacements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("a a a")
            
            result = subprocess.run(
                [str(SAFE_REPLACE), str(test_file), "a", "b", "--json"],
                capture_output=True,
                text=True
            )
            
            output = json.loads(result.stdout)
            assert output["success"] is True
            assert output["replacements"] == 3


class TestPolicyDoctorE2E:
    """E2E tests for policy-doctor tool."""
    
    def test_policy_doctor_runs(self):
        """Test policy-doctor runs successfully."""
        result = subprocess.run(
            [str(POLICY_DOCTOR), "--json"],
            capture_output=True,
            text=True
        )
        
        # Should complete (may have warnings)
        assert result.returncode in [0, 1]
        
        output = json.loads(result.stdout)
        assert "summary" in output
        assert "checks" in output
    
    def test_policy_doctor_checks_all(self):
        """Test policy-doctor checks all components."""
        result = subprocess.run(
            [str(POLICY_DOCTOR), "--json"],
            capture_output=True,
            text=True
        )
        
        output = json.loads(result.stdout)
        check_names = [c["name"] for c in output["checks"]]
        
        assert "rules_file" in check_names
        assert "schema_file" in check_names
        assert "policy_document" in check_names
        assert "tools" in check_names


class TestNoFalseBlocks:
    """Test that there are no false blocks."""
    
    def test_non_openclaw_paths_allowed(self):
        """Test non-~/.openclaw paths are allowed for all tools."""
        test_paths = [
            "/tmp/test.txt",
            "/home/user/test.txt",
            "/var/log/test.txt"
        ]
        
        for path in test_paths:
            result = subprocess.run(
                [str(POLICY_EVAL), "--path", path, "--tool", "edit", "--json"],
                capture_output=True,
                text=True
            )
            
            output = json.loads(result.stdout)
            assert output["decision"] == "allow", f"Path {path} should be allowed"
    
    def test_safe_operations_on_sensitive_paths(self):
        """Test safe operations are allowed on sensitive paths."""
        safe_tools = ["exec", "sed", "python", "read"]
        
        for tool in safe_tools:
            result = subprocess.run(
                [str(POLICY_EVAL), "--path", "~/.openclaw/test.txt", "--tool", tool, "--json"],
                capture_output=True,
                text=True
            )
            
            output = json.loads(result.stdout)
            assert output["decision"] == "allow", f"Tool {tool} should be allowed"


class TestRegressionTests:
    """Regression tests for historical issues."""
    
    def test_edit_on_soul_md_blocked(self):
        """Regression: edit on SOUL.md should be blocked."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "~/.openclaw/workspace/SOUL.md", "--tool", "edit"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        assert "DENY" in result.stdout
    
    def test_edit_on_tools_md_blocked(self):
        """Regression: edit on TOOLS.md should be blocked."""
        result = subprocess.run(
            [str(POLICY_EVAL), "--path", "~/.openclaw/workspace/TOOLS.md", "--tool", "edit"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
