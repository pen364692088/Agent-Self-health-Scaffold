#!/usr/bin/env python3
"""
Project Check Pipeline - Core Library

Main principles:
- Main session only does orchestration
- Each phase runs in isolated session
- All outputs are artifacts (status.json, summary.md, raw.log)
- Progress queries only read status.json
"""

import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

ARTIFACTS_BASE = Path.home() / ".openclaw" / "workspace" / "artifacts" / "project_check"

DEFAULT_PHASES = [
    {
        "id": "phase_a_repo",
        "name": "Repo Snapshot",
        "entrypoint": "project-check-phase repo-snapshot",
        "timeout": 60
    },
    {
        "id": "phase_b_tests",
        "name": "Fast Tests",
        "entrypoint": "project-check-phase fast-tests",
        "timeout": 300
    },
    {
        "id": "phase_c_testbot",
        "name": "Conversation E2E",
        "entrypoint": "project-check-phase testbot-e2e",
        "timeout": 600,
        "depends_on": ["phase_b_tests"]
    },
    {
        "id": "phase_d_gate",
        "name": "Replay + Hard Gate",
        "entrypoint": "project-check-phase hard-gate",
        "timeout": 300,
        "depends_on": ["phase_c_testbot"]
    },
    {
        "id": "phase_e_final",
        "name": "Final Aggregation",
        "entrypoint": "project-check-phase aggregate",
        "timeout": 60,
        "depends_on": ["phase_d_gate"]
    }
]


def generate_check_id() -> str:
    """Generate unique check ID."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"check_{ts}_{short_uuid}"


def create_manifest(
    repo_path: str,
    phases: Optional[List[Dict]] = None,
    check_id: Optional[str] = None,
    stop_on_failure: bool = True
) -> Dict[str, Any]:
    """Create a new check manifest."""
    if phases is None:
        phases = DEFAULT_PHASES
    
    if check_id is None:
        check_id = generate_check_id()
    
    # Get repo info
    repo = {"path": repo_path}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True
        )
        repo["branch"] = result.stdout.strip()
        
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True
        )
        repo["commit"] = result.stdout.strip()[:12]
    except Exception:
        pass
    
    artifacts_dir = str(ARTIFACTS_BASE / check_id)
    
    manifest = {
        "check_id": check_id,
        "phases": phases,
        "repo": repo,
        "artifacts_dir": artifacts_dir,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "stop_on_failure": stop_on_failure
    }
    
    return manifest


def save_manifest(manifest: Dict) -> Path:
    """Save manifest to artifacts directory."""
    artifacts_dir = Path(manifest["artifacts_dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_path = artifacts_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path


def create_phase_dir(artifacts_dir: Path, phase_id: str) -> Path:
    """Create phase output directory."""
    phase_dir = artifacts_dir / phase_id
    phase_dir.mkdir(parents=True, exist_ok=True)
    return phase_dir


def write_phase_status(
    phase_dir: Path,
    status: Dict[str, Any]
) -> Path:
    """Write phase status.json."""
    status_path = phase_dir / "status.json"
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)
    return status_path


def write_phase_summary(phase_dir: Path, summary: str) -> Path:
    """Write phase summary.md."""
    summary_path = phase_dir / "summary.md"
    with open(summary_path, "w") as f:
        f.write(summary)
    return summary_path


def read_phase_status(artifacts_dir: Path, phase_id: str) -> Optional[Dict]:
    """Read phase status.json."""
    status_path = artifacts_dir / phase_id / "status.json"
    if status_path.exists():
        with open(status_path) as f:
            return json.load(f)
    return None


def get_all_phase_statuses(artifacts_dir: Path, manifest: Dict) -> Dict[str, Dict]:
    """Get all phase statuses."""
    statuses = {}
    for phase in manifest["phases"]:
        phase_id = phase["id"]
        status = read_phase_status(artifacts_dir, phase_id)
        statuses[phase_id] = status
    return statuses


def get_next_pending_phase(manifest: Dict, artifacts_dir: Path) -> Optional[Dict]:
    """Get the next phase that should run."""
    statuses = get_all_phase_statuses(artifacts_dir, manifest)
    
    for phase in manifest["phases"]:
        phase_id = phase["id"]
        status = statuses.get(phase_id)
        
        # Already done (success or failure)
        if status and status.get("state") in ["done", "failed", "skipped"]:
            # If failed and stop_on_failure, no more phases
            if status.get("state") == "failed" and manifest.get("stop_on_failure"):
                return None
            continue
        
        # Check dependencies
        deps = phase.get("depends_on", [])
        all_deps_done = all(
            statuses.get(dep, {}).get("state") == "done"
            for dep in deps
        )
        
        if all_deps_done:
            # Not started yet, or still running
            if status is None or status.get("state") == "pending":
                return phase
    
    return None


def is_check_complete(manifest: Dict, artifacts_dir: Path) -> bool:
    """Check if all phases are done."""
    statuses = get_all_phase_statuses(artifacts_dir, manifest)
    
    for phase in manifest["phases"]:
        phase_id = phase["id"]
        status = statuses.get(phase_id)
        
        if status is None:
            return False
        if status.get("state") not in ["done", "failed", "skipped"]:
            return False
    
    return True


def get_check_result(manifest: Dict, artifacts_dir: Path) -> Dict[str, Any]:
    """Get overall check result."""
    statuses = get_all_phase_statuses(artifacts_dir, manifest)
    
    all_ok = all(
        s.get("ok", False) for s in statuses.values() if s
    )
    
    failed_phases = [
        pid for pid, s in statuses.items()
        if s and s.get("state") == "failed"
    ]
    
    return {
        "check_id": manifest["check_id"],
        "ok": all_ok,
        "all_done": is_check_complete(manifest, artifacts_dir),
        "failed_phases": failed_phases,
        "phases": statuses
    }
