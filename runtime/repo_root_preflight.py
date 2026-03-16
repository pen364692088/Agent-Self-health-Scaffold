#!/usr/bin/env python3
"""
Repo Root Preflight

Purpose:
  Enforce correct repository root before any project actions.
  Prevents workspace drift to wrong directories.

Usage:
  from runtime.repo_root_preflight import RepoRootPreflight
  
  preflight = RepoRootPreflight()
  result = preflight.check()
  
  if result.passed:
      # Proceed with action
  else:
      # Block and report

Version: v1.0
Date: 2026-03-16
Status: MANDATORY_ENFORCEMENT
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class PreflightStatus(Enum):
    PASS = "pass"
    BLOCK = "block"


@dataclass
class RepoRootResult:
    """Result of repo root preflight check"""
    passed: bool
    expected_root: str
    actual_root: Optional[str]
    status: PreflightStatus
    reason: str
    action_type: str
    block_reason: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "expected_root": self.expected_root,
            "actual_root": self.actual_root,
            "status": self.status.value,
            "reason": self.reason,
            "action_type": self.action_type,
            "block_reason": self.block_reason
        }


class RepoRootPreflight:
    """
    Repo Root Preflight
    
    Enforces correct repository root before project actions.
    """
    
    # Project-specific canonical repo roots
    CANONICAL_ROOTS = {
        "Agent-Self-health-Scaffold": "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold",
    }
    
    # Remote URLs for verification
    CANONICAL_REMOTES = {
        "Agent-Self-health-Scaffold": "git@github.com:pen364692088/Agent-Self-health-Scaffold.git",
    }
    
    # Actions that require preflight
    TRIGGER_ACTIONS = [
        "file_read_write",
        "test_execution",
        "git_rebase",
        "git_merge",
        "git_cherry_pick",
        "git_push",
        "state_update",
        "mutation",
    ]
    
    def __init__(self, project_name: str = "Agent-Self-health-Scaffold"):
        self.project_name = project_name
        self.expected_root = self.CANONICAL_ROOTS.get(project_name)
        self.expected_remote = self.CANONICAL_REMOTES.get(project_name)
        
        workspace = os.environ.get("OPENCLAW_WORKSPACE",
                                   os.path.expanduser("~/.openclaw/workspace"))
        self.evidence_dir = os.path.join(workspace, "artifacts/preflight")
        os.makedirs(self.evidence_dir, exist_ok=True)
    
    def check(self, action_type: str = "general") -> RepoRootResult:
        """
        Execute repo root preflight check.
        
        Args:
            action_type: Type of action being attempted
            
        Returns:
            RepoRootResult with check outcome
        """
        if not self.expected_root:
            return RepoRootResult(
                passed=False,
                expected_root="unknown",
                actual_root=None,
                status=PreflightStatus.BLOCK,
                reason=f"Unknown project: {self.project_name}",
                action_type=action_type,
                block_reason="unknown_project"
            )
        
        # Get actual repo root
        actual_root = self._get_git_root()
        
        if actual_root is None:
            return RepoRootResult(
                passed=False,
                expected_root=self.expected_root,
                actual_root=None,
                status=PreflightStatus.BLOCK,
                reason="Not in a git repository",
                action_type=action_type,
                block_reason="not_git_repo"
            )
        
        # Check if matches expected
        if actual_root != self.expected_root:
            return RepoRootResult(
                passed=False,
                expected_root=self.expected_root,
                actual_root=actual_root,
                status=PreflightStatus.BLOCK,
                reason=f"Repo root mismatch: expected {self.expected_root}, got {actual_root}",
                action_type=action_type,
                block_reason="repo_root_mismatch"
            )
        
        # Verify remote if available
        if self.expected_remote:
            actual_remote = self._get_git_remote()
            if actual_remote and actual_remote != self.expected_remote:
                return RepoRootResult(
                    passed=False,
                    expected_root=self.expected_root,
                    actual_root=actual_root,
                    status=PreflightStatus.BLOCK,
                    reason=f"Remote mismatch: expected {self.expected_remote}, got {actual_remote}",
                    action_type=action_type,
                    block_reason="remote_mismatch"
                )
        
        # All checks passed
        return RepoRootResult(
            passed=True,
            expected_root=self.expected_root,
            actual_root=actual_root,
            status=PreflightStatus.PASS,
            reason="All repo root checks passed",
            action_type=action_type,
            block_reason=None
        )
    
    def check_or_block(self, action_type: str = "general") -> RepoRootResult:
        """
        Check and block if failed.
        
        Raises:
            RuntimeError: If preflight fails
        """
        result = self.check(action_type)
        
        if not result.passed:
            raise RuntimeError(self.get_block_message(result))
        
        return result
    
    def _get_git_root(self) -> Optional[str]:
        """Get current git repository root"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_git_remote(self) -> Optional[str]:
        """Get current git remote origin URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def get_block_message(self, result: RepoRootResult) -> str:
        """Generate human-readable block message"""
        if result.passed:
            return ""
        
        return f"""🚫 REPO ROOT PREFLIGHT BLOCKED

Project: {self.project_name}
Action: {result.action_type}

Expected Root: {result.expected_root}
Actual Root: {result.actual_root or 'NOT IN GIT REPO'}

Reason: {result.reason}
Block Type: {result.block_reason}

=== HOW TO FIX ===

cd {self.expected_root}

Then retry your action.

=== FORBIDDEN ===

❌ Do NOT continue from wrong workspace
❌ Do NOT use ~/.openclaw/workspace as project root
❌ Do NOT skip repo root preflight
"""
    
    def log_evidence(self, result: RepoRootResult, task_id: str = None) -> str:
        """Log preflight evidence"""
        if task_id is None:
            task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        evidence = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            **result.to_dict()
        }
        
        evidence_path = os.path.join(
            self.evidence_dir,
            f"repo_root_preflight_{task_id}.json"
        )
        
        with open(evidence_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_path


# =============================================================================
# Convenience functions
# =============================================================================

def check_repo_root(project_name: str = "Agent-Self-health-Scaffold") -> bool:
    """Quick check if in correct repo root"""
    preflight = RepoRootPreflight(project_name)
    result = preflight.check()
    return result.passed


def enforce_repo_root(project_name: str = "Agent-Self-health-Scaffold") -> None:
    """Enforce correct repo root or raise error"""
    preflight = RepoRootPreflight(project_name)
    preflight.check_or_block()


# =============================================================================
# Decorator for automatic enforcement
# =============================================================================

def require_correct_repo(project_name: str = "Agent-Self-health-Scaffold"):
    """
    Decorator to enforce correct repo before function execution.
    
    Usage:
        @require_correct_repo("Agent-Self-health-Scaffold")
        def my_function():
            # Will only execute if in correct repo
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            preflight = RepoRootPreflight(project_name)
            preflight.check_or_block(action_type=func.__name__)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI interface for repo_root_preflight"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Repo Root Preflight")
    parser.add_argument("--project", default="Agent-Self-health-Scaffold",
                       help="Project name")
    parser.add_argument("--action", default="general",
                       help="Action type")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON")
    parser.add_argument("--strict", action="store_true",
                       help="Exit with error code on failure")
    
    args = parser.parse_args()
    
    preflight = RepoRootPreflight(args.project)
    result = preflight.check(args.action)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.passed:
            print(f"✅ REPO ROOT CHECK PASSED")
            print(f"   Expected: {result.expected_root}")
            print(f"   Actual: {result.actual_root}")
        else:
            print(preflight.get_block_message(result))
    
    if args.strict and not result.passed:
        exit(1)


if __name__ == "__main__":
    main()
