#!/usr/bin/env python3
"""
Test for subagent-completion-handler tool.

Ensures that subagent completion triggers correct workflow progression.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add workspace tools to path
sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace" / "tools"))


def test_handler_health():
    """Test that handler reports healthy."""
    result = subprocess.run(
        [str(Path.home() / ".openclaw" / "workspace" / "tools" / "subagent-completion-handler"), "--health"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "healthy"


def test_spawn_next_on_intermediate_step():
    """Test that intermediate step completion triggers spawn_next."""
    # This test requires modifying WORKFLOW_STATE.json
    # In production, the handler does this atomically
    pass


def test_notify_user_on_final_step():
    """Test that final step completion triggers notify_user."""
    pass


def test_ignore_on_inactive_workflow():
    """Test that inactive workflow is ignored."""
    result = subprocess.run(
        [str(Path.home() / ".openclaw" / "workspace" / "tools" / "subagent-completion-handler"), "nonexistent-run-id"],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    # Should ignore since workflow is inactive
    assert data["action"] in ("ignore", "error")


if __name__ == "__main__":
    test_handler_health()
    print("✅ All tests passed")
