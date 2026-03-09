#!/usr/bin/env python3
"""
Session Continuity v1.1.1 Tests

Tests for hotfix issues:
1. Objective parser (no false "missing" reports)
2. Field-level conflict resolution
3. Context ratio handling

Run with: pytest tests/session_continuity/test_session_continuity_v111.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent))
sys.path.insert(0, str(WORKSPACE / "tools"))

import pytest


class TestObjectiveParser:
    """Tests for objective field extraction."""
    
    def test_header_format(self):
        """Test ## Current Objective format."""
        content = """# Test
## Current Objective
实现目标
"""
        # Import the function
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "valid"
        assert "实现目标" in normalized
    
    def test_colon_format(self):
        """Test Objective: xxx format."""
        content = "Objective: 实现目标"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Objective")
        assert status == "valid"
        assert "实现目标" in normalized
    
    def test_list_format(self):
        """Test - Objective: xxx format."""
        content = "- Objective: 实现目标"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Objective")
        assert status == "valid"
        assert "实现目标" in normalized
    
    def test_bold_format(self):
        """Test **Current Objective**: xxx format."""
        content = "**Current Objective**: 实现目标"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "valid"
        assert "实现目标" in normalized
    
    def test_empty_value(self):
        """Test empty objective."""
        content = "## Current Objective\n\n"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "empty"
    
    def test_placeholder_value(self):
        """Test placeholder values."""
        content = "## Current Objective\nTBD"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "empty"
    
    def test_missing_field(self):
        """Test missing objective."""
        content = "## Other Section\nSome content"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "missing"
    
    def test_multiline_value(self):
        """Test multiline objective."""
        content = "## Current Objective\n实现目标\n继续工作"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "valid"
        assert "实现目标" in normalized
    
    def test_chinese_english_mixed(self):
        """Test Chinese/English mixed."""
        content = "## Current Objective 目标\nImplement the protocol"
        from session_start_recovery import extract_field_value
        status, raw, normalized = extract_field_value(content, "Current Objective")
        assert status == "valid"
    
    def test_real_session_state(self):
        """Test with real SESSION-STATE.md."""
        from session_start_recovery import extract_all_fields
        fields = extract_all_fields(WORKSPACE / "SESSION-STATE.md")
        
        assert "objective" in fields
        assert fields["objective"]["status"] == "valid"
        assert fields["objective"]["value"] != ""


class TestFieldLevelConflictResolution:
    """Tests for field-level conflict resolution."""
    
    def test_resolve_single_source(self):
        """Test resolution with single valid source."""
        from session_start_recovery import resolve_field_conflicts
        
        field_values = {
            "session_state_md": {"status": "valid", "value": "目标A"}
        }
        
        result = resolve_field_conflicts(field_values)
        assert result["status"] == "valid"
        assert result["value"] == "目标A"
        assert result["chosen_source"] == "session_state_md"
    
    def test_resolve_priority_winner(self):
        """Test resolution with priority-based winner."""
        from session_start_recovery import resolve_field_conflicts
        
        field_values = {
            "session_state_md": {"status": "valid", "value": "目标A"},
            "handoff_md": {"status": "valid", "value": "目标B"}
        }
        
        result = resolve_field_conflicts(field_values)
        assert result["status"] == "valid"
        # handoff_md has higher priority (80 vs 70)
        assert result["chosen_source"] == "handoff_md"
    
    def test_resolve_conflict_detection(self):
        """Test conflict detection in resolution."""
        from session_start_recovery import resolve_field_conflicts
        
        field_values = {
            "session_state_md": {"status": "valid", "value": "目标A"},
            "handoff_md": {"status": "valid", "value": "目标B"}
        }
        
        result = resolve_field_conflicts(field_values)
        assert result["conflicts"] is not None
        assert len(result["conflicts"]) == 1
    
    def test_resolve_all_empty(self):
        """Test resolution with all empty values."""
        from session_start_recovery import resolve_field_conflicts
        
        field_values = {
            "session_state_md": {"status": "empty", "value": ""},
            "handoff_md": {"status": "empty", "value": ""}
        }
        
        result = resolve_field_conflicts(field_values)
        assert result["status"] == "missing"
    
    def test_resolve_with_repo_evidence(self):
        """Test resolution with repo evidence."""
        from session_start_recovery import resolve_field_conflicts
        
        field_values = {
            "repo_evidence": {"status": "valid", "value": "main"},
            "session_state_md": {"status": "valid", "value": "feature-a"}
        }
        
        result = resolve_field_conflicts(field_values)
        # repo_evidence has highest priority (100)
        assert result["chosen_source"] == "repo_evidence"


class TestRecoveryIntegration:
    """Integration tests for recovery flow."""
    
    def test_full_recovery(self):
        """Test full recovery with field extraction."""
        import subprocess
        
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--recover", "--json"],
            capture_output=True, text=True
        )
        
        assert result.returncode == 0
        data = json.loads(result.stdout)
        
        # Check field resolution exists
        assert "field_resolution" in data
        assert "objective" in data["field_resolution"]
        assert data["field_resolution"]["objective"]["status"] == "valid"
    
    def test_no_false_missing(self):
        """Test that objective is not falsely reported as missing."""
        import subprocess
        
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--recover", "--json"],
            capture_output=True, text=True
        )
        
        data = json.loads(result.stdout)
        
        # Objective should be valid, not missing
        obj_status = data["field_resolution"]["objective"]["status"]
        assert obj_status == "valid", f"Expected 'valid', got '{obj_status}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])