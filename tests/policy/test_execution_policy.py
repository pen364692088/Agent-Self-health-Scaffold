"""
Execution Policy Tests

Unit tests for execution policy enforcement framework.
Run with: pytest tests/policy/test_execution_policy.py -v
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Tools paths
TOOLS_DIR = Path.home() / ".openclaw" / "workspace" / "tools"
POLICY_EVAL = TOOLS_DIR / "policy-eval"
POLICY_DOCTOR = TOOLS_DIR / "policy-doctor"


def run_policy_eval(path: str, tool: str, operation: str = "write") -> dict:
    """Run policy-eval and return parsed result."""
    result = subprocess.run(
        [str(POLICY_EVAL), "--path", path, "--tool", tool, "--operation", operation, "--json"],
        capture_output=True,
        text=True
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"decision": "error", "stdout": result.stdout, "stderr": result.stderr}


class TestPathMatcher:
    """Test path pattern matching."""
    
    def test_exact_match(self):
        """Test exact path match."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        assert result["decision"] == "deny"
        assert result["rule_id"] == "OPENCLAW_PATH_NO_EDIT"
    
    def test_nested_path_match(self):
        """Test nested path match."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/POLICIES/TEST.md",
            tool="edit"
        )
        assert result["decision"] == "deny"
    
    def test_non_sensitive_path_allow(self):
        """Test non-sensitive path is allowed."""
        result = run_policy_eval(
            path="/tmp/test.txt",
            tool="edit"
        )
        assert result["decision"] == "allow"
    
    def test_expanded_path(self):
        """Test expanded home directory path."""
        expanded_path = str(Path.home() / ".openclaw" / "config.json")
        result = run_policy_eval(
            path=expanded_path,
            tool="edit"
        )
        assert result["decision"] == "deny"


class TestToolMatcher:
    """Test tool matching."""
    
    def test_edit_tool_blocked(self):
        """Test edit tool is blocked for sensitive paths."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        assert result["decision"] == "deny"
    
    def test_write_tool_warned(self):
        """Test write tool triggers warning for sensitive paths."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="write"
        )
        assert result["decision"] == "warn"
        assert result["rule_id"] == "SENSITIVE_PATH_PREFER_SAFE_WRITE"
    
    def test_safe_tools_allowed(self):
        """Test safe tools are allowed."""
        # exec is allowed (not in deny list)
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="exec"
        )
        assert result["decision"] == "allow"


class TestDecisionLogic:
    """Test decision logic."""
    
    def test_deny_decision(self):
        """Test deny decision."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        assert result["decision"] == "deny"
        assert "fallback" in result
    
    def test_warn_decision(self):
        """Test warn decision."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="write"
        )
        assert result["decision"] == "warn"
    
    def test_allow_decision(self):
        """Test allow decision."""
        result = run_policy_eval(
            path="/tmp/test.txt",
            tool="edit"
        )
        assert result["decision"] == "allow"
        assert result["rule_id"] is None


class TestPriority:
    """Test rule priority."""
    
    def test_p0_rules_first(self):
        """Test P0 rules are evaluated first."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        # Should get P0 deny, not P1 warn
        assert result["decision"] == "deny"
        matched = result.get("matched_rules", [])
        if matched:
            assert matched[0].get("priority") == "P0"


class TestConflictResolution:
    """Test conflict resolution between rules."""
    
    def test_higher_priority_wins(self):
        """Test higher priority rule wins."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        assert result["decision"] == "deny"


class TestFallback:
    """Test fallback suggestions."""
    
    def test_deny_has_fallback(self):
        """Test deny decisions include fallback."""
        result = run_policy_eval(
            path="~/.openclaw/workspace/SOUL.md",
            tool="edit"
        )
        assert result["decision"] == "deny"
        assert "fallback" in result
        assert "safe-write" in result["fallback"] or "safe-replace" in result["fallback"]


class TestRuleLoading:
    """Test rule loading."""
    
    def test_rules_file_exists(self):
        """Test rules file exists."""
        rules_file = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_RULES.yaml"
        assert rules_file.exists(), "Rules file should exist"
    
    def test_load_rules(self):
        """Test rules can be loaded."""
        import yaml
        rules_file = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_RULES.yaml"
        with open(rules_file) as f:
            rules = yaml.safe_load(f)
        assert "metadata" in rules
        assert "rules" in rules
        assert len(rules["rules"]) > 0
    
    def test_rules_have_required_fields(self):
        """Test rules have required fields."""
        import yaml
        rules_file = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_RULES.yaml"
        with open(rules_file) as f:
            rules = yaml.safe_load(f)
        for rule in rules["rules"]:
            assert "id" in rule
            assert "status" in rule
            assert "priority" in rule
            assert "action" in rule
            assert "reason" in rule


class TestSchemaValidation:
    """Test schema validation."""
    
    def test_schema_file_exists(self):
        """Test schema file exists."""
        schema_file = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_SCHEMA.json"
        assert schema_file.exists(), "Schema file should exist"
    
    def test_schema_is_valid_json(self):
        """Test schema is valid JSON."""
        schema_file = Path.home() / ".openclaw" / "workspace" / "POLICIES" / "EXECUTION_POLICY_SCHEMA.json"
        with open(schema_file) as f:
            schema = json.load(f)
        assert "$schema" in schema


class TestPolicyDoctor:
    """Test policy-doctor tool."""
    
    def test_policy_doctor_runs(self):
        """Test policy-doctor runs successfully."""
        result = subprocess.run(
            [str(POLICY_DOCTOR), "--json"],
            capture_output=True,
            text=True
        )
        
        output = json.loads(result.stdout)
        assert "summary" in output
        assert "checks" in output
    
    def test_policy_doctor_healthy(self):
        """Test policy-doctor reports healthy status."""
        result = subprocess.run(
            [str(POLICY_DOCTOR), "--json"],
            capture_output=True,
            text=True
        )
        
        output = json.loads(result.stdout)
        assert output["summary"]["healthy"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
