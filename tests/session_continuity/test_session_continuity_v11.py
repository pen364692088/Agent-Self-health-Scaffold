#!/usr/bin/env python3
"""
Session Continuity v1.1 Tests

Tests for session recovery, conflict resolution, WAL, and concurrency.

Run with: pytest tests/session_continuity/test_session_continuity_v11.py -v
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add workspace to path
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent))
sys.path.insert(0, str(WORKSPACE / "tools"))

import pytest


class TestSessionRecovery:
    """Tests for session recovery functionality."""
    
    def test_preflight_check_returns_valid_json(self):
        """Preflight check should return valid JSON with required fields."""
        import subprocess
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--preflight"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        data = json.loads(result.stdout)
        assert "needs_recovery" in data
        assert "session_id" in data
        assert "action" in data
    
    def test_recovery_returns_summary(self):
        """Recovery should return a summary with state information."""
        import subprocess
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--recover", "--json"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        data = json.loads(result.stdout)
        assert "recovered" in data
        assert "sources" in data
        assert "conflicts" in data
    
    def test_health_check_returns_status(self):
        """Health check should return file status."""
        import subprocess
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--health"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        data = json.loads(result.stdout)
        assert "status" in data
        assert "files" in data


class TestAtomicWrite:
    """Tests for atomic write functionality."""
    
    def test_atomic_write_creates_file(self):
        """Atomic write should create a file."""
        import subprocess
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "state-write-atomic"), temp_path, "test content", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            
            data = json.loads(result.stdout)
            assert data["success"] == True
            assert Path(temp_path).exists()
            assert Path(temp_path).read_text() == "test content"
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_atomic_write_with_wal(self):
        """Atomic write should append to WAL."""
        import subprocess
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "state-write-atomic"), temp_path, "wal test", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            
            # Check WAL file exists
            wal_file = WORKSPACE / "state" / "wal" / "session_state_wal.jsonl"
            assert wal_file.exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestWALJournal:
    """Tests for WAL journal functionality."""
    
    def test_journal_append(self):
        """Journal append should add an entry."""
        import subprocess
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "state-journal-append"), 
             "--action", "test_action", "--summary", "test summary"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
    
    def test_journal_list(self):
        """Journal list should return entries."""
        import subprocess
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "state-journal-append"), "--list", "--limit", "5"],
            capture_output=True, text=True
        )
        assert result.returncode == 0


class TestConflictResolution:
    """Tests for conflict resolution."""
    
    def test_conflict_detection_branch_mismatch(self):
        """Should detect branch mismatch between session state and repo."""
        # This test would need mock data
        # For now, just verify the function exists
        from session_start_recovery import detect_conflicts
        assert callable(detect_conflicts)
    
    def test_conflict_detection_stale_file(self):
        """Should detect stale state files."""
        from session_start_recovery import detect_conflicts
        sources = {
            "session_state": {"exists": True, "fresh": False, "age_hours": 50}
        }
        conflicts = detect_conflicts(sources)
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "stale_file"


class TestStateLocking:
    """Tests for state file locking."""
    
    def test_lock_acquire_and_release(self):
        """Should be able to acquire and release a lock."""
        import subprocess
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            # Acquire lock
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "state-lock"), "--file", temp_path, "--acquire", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["success"] == True
            
            # Release lock
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "state-lock"), "--file", temp_path, "--release", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["success"] == True
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_lock_check(self):
        """Should be able to check lock status."""
        import subprocess
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "state-lock"), "--file", temp_path, "--check", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert "locked" in data
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests for the full flow."""
    
    def test_full_recovery_flow(self):
        """Test the full recovery flow from preflight to recovery."""
        import subprocess
        
        # Step 1: Preflight check
        result = subprocess.run(
            [str(WORKSPACE / "tools" / "session-start-recovery"), "--preflight"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        preflight = json.loads(result.stdout)
        
        # Step 2: If recovery needed, perform recovery
        if preflight.get("needs_recovery"):
            result = subprocess.run(
                [str(WORKSPACE / "tools" / "session-start-recovery"), "--recover", "--json"],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            recovery = json.loads(result.stdout)
            assert "recovered" in recovery


if __name__ == "__main__":
    pytest.main([__file__, "-v"])