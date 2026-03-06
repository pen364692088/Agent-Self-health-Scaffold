#!/usr/bin/env python3
"""
E2E tests for project-check pipeline.
"""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path

TOOLS_DIR = Path.home() / ".openclaw" / "workspace" / "tools"
ARTIFACTS_BASE = Path.home() / ".openclaw" / "workspace" / "artifacts" / "project_check"


def run_cmd(cmd):
    """Run command and return result."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=True
    )
    return result.returncode, result.stdout, result.stderr


def test_health_checks():
    """Test --health endpoints."""
    code, out, err = run_cmd(f"{TOOLS_DIR}/project-check --health")
    assert code == 0, f"project-check --health failed: {err}"
    data = json.loads(out)
    assert data["status"] == "healthy"
    
    code, out, err = run_cmd(f"{TOOLS_DIR}/project-check-phase --health")
    assert code == 0, f"project-check-phase --health failed: {err}"
    data = json.loads(out)
    assert data["status"] == "healthy"


def test_init_creates_manifest():
    """Test init creates manifest with correct structure."""
    # Create temp repo
    with tempfile.TemporaryDirectory() as tmpdir:
        # Init git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=tmpdir, capture_output=True)
        
        # Run init
        code, out, err = run_cmd(f"{TOOLS_DIR}/project-check init {tmpdir}")
        assert code == 0, f"init failed: {err}"
        assert "Created check:" in out
        
        # Extract check_id
        check_id = out.split("Created check:")[1].strip().split()[0]
        
        # Verify manifest exists
        manifest_path = ARTIFACTS_BASE / check_id / "manifest.json"
        assert manifest_path.exists(), f"manifest not found at {manifest_path}"
        
        # Verify manifest structure
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest["check_id"] == check_id
        assert len(manifest["phases"]) == 5
        assert manifest["repo"]["path"] == tmpdir
        
        # Cleanup
        shutil.rmtree(ARTIFACTS_BASE / check_id)


def test_status_shows_phases():
    """Test status shows all phases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=tmpdir, capture_output=True)
        
        # Run init
        code, out, err = run_cmd(f"{TOOLS_DIR}/project-check init {tmpdir}")
        check_id = out.split("Created check:")[1].strip().split()[0]
        
        # Run status
        code, out, err = run_cmd(f"{TOOLS_DIR}/project-check status {check_id}")
        assert code == 0, f"status failed: {err}"
        assert "phase_a_repo" in out
        assert "phase_b_tests" in out
        
        # Cleanup
        shutil.rmtree(ARTIFACTS_BASE / check_id)


if __name__ == "__main__":
    test_health_checks()
    print("✅ test_health_checks")
    
    test_init_creates_manifest()
    print("✅ test_init_creates_manifest")
    
    test_status_shows_phases()
    print("✅ test_status_shows_phases")
    
    print("\nAll tests passed!")
