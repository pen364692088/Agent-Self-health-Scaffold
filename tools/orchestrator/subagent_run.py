#!/usr/bin/env python3
"""
Subagent Run - One-Shot Execution Module

This module provides a programmatic way to spawn and manage subagents
with reliable callback handling.

Usage in agent code:
    from subagent_run import SubagentRunner
    
    runner = SubagentRunner()
    result = runner.run(
        task="Implement feature X",
        model="iflow/qwen3-coder-plus",
        timeout=300
    )
    # result contains task_id, run_id, summary, artifacts
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add orchestrator to path
WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
ORCHESTRATOR_DIR = WORKSPACE / "tools" / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_DIR))

from orchestrator import Orchestrator, SubtaskStatus


class SubagentRunner:
    """
    One-shot subagent execution with reliable callback handling.
    
    This class wraps the orchestrator to provide a simple interface
    for spawning subagents and waiting for completion.
    
    Example:
        runner = SubagentRunner()
        
        # Step 1: Prepare spawn
        spawn_info = runner.prepare_spawn(
            task="Implement feature X",
            model="iflow/qwen3-coder-plus"
        )
        
        # Step 2: Execute spawn (agent must call sessions_spawn)
        print(f"Execute: {spawn_info['spawn_command']}")
        
        # Step 3: Join and collect
        result = runner.join_and_collect(
            task_id=spawn_info['task_id'],
            timeout=300
        )
    """
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir:
            self.workspace = Path(workspace_dir)
        else:
            self.workspace = WORKSPACE
        
        self.orchestrator = Orchestrator(workspace_dir=str(self.workspace))
        self.mailbox_dir = self.workspace / "reports" / "subtasks"
        self.mailbox_dir.mkdir(parents=True, exist_ok=True)
    
    def check_pending(self) -> int:
        """Check and return number of pending tasks"""
        return len(self.orchestrator.pending_subtasks)
    
    def auto_resume(self, timeout: float = 60) -> bool:
        """
        Auto-resume any pending tasks.
        
        Call this before spawning new tasks to ensure clean state.
        """
        if not self.orchestrator.pending_subtasks:
            return True
        
        print(f"Auto-resuming {len(self.orchestrator.pending_subtasks)} pending tasks...")
        return self.orchestrator.join_all(timeout=timeout)
    
    def prepare_spawn(
        self,
        task: str,
        model: str = "iflow/qwen3-coder-plus",
        timeout: float = 300,
        max_retries: int = 3,
        auto_resume: bool = True
    ) -> Dict[str, Any]:
        """
        Prepare a subagent spawn with orchestrator registration.
        
        This is Step 1 of the one-shot workflow.
        
        Args:
            task: Task description
            model: Model to use for subagent
            timeout: Timeout in seconds
            max_retries: Maximum retry attempts
            auto_resume: Whether to auto-resume pending tasks first
        
        Returns:
            Dict with task_id, run_id, session_key, spawn_command, join_command
        """
        # Auto-resume if requested
        if auto_resume and self.orchestrator.pending_subtasks:
            self.auto_resume(timeout=min(timeout, 60))
            # Refresh orchestrator
            self.orchestrator = Orchestrator(workspace_dir=str(self.workspace))
        
        # Register task
        task_id, run_id, session_key = self.orchestrator.spawn_task(
            description=task,
            model=model,
            max_retries=max_retries
        )
        
        # Build commands
        spawn_command = f"sessions_spawn runtime=subagent model={model} task='{task[:100]}'"
        join_command = f"subtask-orchestrate join -t {timeout} --task-id {task_id}"
        
        return {
            "task_id": task_id,
            "run_id": run_id,
            "session_key": session_key,
            "model": model,
            "spawn_command": spawn_command,
            "join_command": join_command,
            "timeout": timeout
        }
    
    def join_and_collect(
        self,
        task_id: str,
        timeout: float = 300,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Join a specific task and collect results.
        
        This is Step 2 of the one-shot workflow.
        
        Args:
            task_id: Task ID to join
            timeout: Timeout in seconds
            poll_interval: Initial poll interval (with exponential backoff)
        
        Returns:
            Dict with task_id, status, summary, artifacts, elapsed_seconds
        """
        start_time = time.time()
        
        # Check if task exists
        if task_id in self.orchestrator.completed_subtasks:
            task = self.orchestrator.completed_subtasks[task_id]
            return self._build_result(task, time.time() - start_time)
        
        if task_id not in self.orchestrator.pending_subtasks:
            return {
                "task_id": task_id,
                "status": "not_found",
                "summary": f"Task {task_id} not found in orchestrator",
                "artifacts": [],
                "elapsed_seconds": 0
            }
        
        # Poll for completion
        task = self.orchestrator.pending_subtasks[task_id]
        current_interval = poll_interval
        max_interval = 20.0
        
        while True:
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed > timeout:
                self.orchestrator._handle_task_timeout(task)
                return {
                    "task_id": task_id,
                    "status": "timeout",
                    "summary": f"Task timed out after {timeout}s",
                    "artifacts": [],
                    "elapsed_seconds": elapsed
                }
            
            # Check mailbox
            mailbox_file = self.mailbox_dir / f"{task_id}.done.json"
            if mailbox_file.exists():
                with open(mailbox_file) as f:
                    receipt = json.load(f)
                
                self.orchestrator._mark_task_completed(task, receipt)
                return self._build_result(task, time.time() - start_time)
            
            # Check if already completed (via explicit receipt)
            if task_id in self.orchestrator.completed_subtasks:
                task = self.orchestrator.completed_subtasks[task_id]
                return self._build_result(task, time.time() - start_time)
            
            # Wait with exponential backoff
            time.sleep(current_interval)
            current_interval = min(current_interval * 2, max_interval)
    
    def run(
        self,
        task: str,
        model: str = "iflow/qwen3-coder-plus",
        timeout: float = 300,
        auto_resume: bool = True
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        One-shot run (requires agent to execute spawn command).
        
        This method returns the spawn info, then agent must:
        1. Execute the spawn_command
        2. Call join_and_collect with the task_id
        
        Returns:
            (task_id, spawn_command, join_info)
        """
        spawn_info = self.prepare_spawn(
            task=task,
            model=model,
            timeout=timeout,
            auto_resume=auto_resume
        )
        
        return (
            spawn_info["task_id"],
            spawn_info["spawn_command"],
            {
                "join_command": spawn_info["join_command"],
                "timeout": timeout
            }
        )
    
    def _build_result(self, task: Any, elapsed: float) -> Dict[str, Any]:
        """Build result dict from completed task"""
        return {
            "task_id": task.task_id,
            "run_id": task.run_id,
            "status": task.status,
            "summary": task.summary or "",
            "artifacts": task.artifacts or task.output_paths or [],
            "elapsed_seconds": elapsed,
            "result_data": task.result_data
        }
    
    def list_tasks(self) -> Dict[str, Any]:
        """List all tasks"""
        return {
            "pending": len(self.orchestrator.pending_subtasks),
            "completed": len(self.orchestrator.completed_subtasks),
            "pending_ids": list(self.orchestrator.pending_subtasks.keys()),
            "completed_ids": list(self.orchestrator.completed_subtasks.keys())
        }
    
    def cleanup(self, keep_days: int = 7) -> int:
        """Cleanup old completed tasks"""
        return self.orchestrator.gc(keep_days=keep_days)


# Convenience function
def subagent_run(
    task: str,
    model: str = "iflow/qwen3-coder-plus",
    timeout: float = 300
) -> Tuple[str, str, Dict]:
    """
    Convenience function for one-shot subagent execution.
    
    Usage:
        task_id, spawn_cmd, join_info = subagent_run(
            task="Implement feature X",
            model="iflow/qwen3-coder-plus",
            timeout=300
        )
        
        # Agent must execute spawn_cmd
        # Then call join_and_collect
    """
    runner = SubagentRunner()
    return runner.run(task=task, model=model, timeout=timeout)


if __name__ == "__main__":
    # Test
    print("Subagent Runner Test")
    print("=" * 50)
    
    runner = SubagentRunner()
    
    # Check pending
    pending = runner.check_pending()
    print(f"Pending tasks: {pending}")
    
    # Prepare spawn
    spawn_info = runner.prepare_spawn(
        task="Test task",
        model="iflow/qwen3-coder-plus"
    )
    
    print(f"\nTask ID: {spawn_info['task_id']}")
    print(f"Run ID: {spawn_info['run_id']}")
    print(f"\nSpawn command:\n  {spawn_info['spawn_command']}")
    print(f"\nJoin command:\n  {spawn_info['join_command']}")
