#!/usr/bin/env python3
"""
CC-Godmode Subagent Orchestrator v2.0
Reliable callback system with Join/Poll + Receipt + Fallback mailbox architecture

Enhancements v2.0:
- Atomic file writes (tmp → rename)
- Jitter on exponential backoff
- Per-task deadline + global timeout
- Idempotent receipt handling
- Structured event logging

Lock Ordering Convention:
=========================
This module uses a single lock (self.lock) for thread safety.
If multiple locks are introduced in the future, always acquire in this order:
    1. self.lock (Orchestrator lock)
    2. storage_lock (if added)
    3. io_lock (if added)
    
NEVER acquire in reverse order to prevent deadlock.

For internal methods called while holding lock, use _locked() versions:
    - _save_pending_to_storage_locked() - called when already holding self.lock
    - _save_pending_to_storage() - public wrapper that acquires lock first
"""

import json
import time
import os
import uuid
import random
import fcntl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
import threading
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubtaskStatus:
    SPAWNED = "spawned"
    PENDING = "pending"
    JOINING = "joining"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


# Standard receipt JSON schema
RECEIPT_SCHEMA = {
    "task_id": str,
    "run_id": str,
    "session_key": str,
    "status": "ok|fail|timeout",
    "summary": str,
    "artifacts": list,
    "error": dict,
    "ts": str
}


class Subtask:
    """Represents a single subtask managed by the orchestrator"""
    
    def __init__(self, task_id: str, run_id: str, child_session_key: str, 
                 description: str = "", deadline: Optional[datetime] = None, 
                 max_retries: int = 3, **kwargs):
        self.task_id = task_id
        self.run_id = run_id
        self.child_session_key = child_session_key
        self.description = description
        self.status = SubtaskStatus.SPAWNED
        self.deadline = deadline or datetime.now() + timedelta(hours=1)
        self.max_retries = max_retries
        self.retries = 0
        self.attempt = 0
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.output_paths = []
        self.artifacts = []
        self.summary = ""
        self.error = None
        self.result_data = None
        self.metadata = kwargs

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'run_id': self.run_id,
            'child_session_key': self.child_session_key,
            'description': self.description,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'max_retries': self.max_retries,
            'retries': self.retries,
            'attempt': self.attempt,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_paths': self.output_paths,
            'artifacts': self.artifacts,
            'summary': self.summary,
            'error': self.error,
            'result_data': self.result_data,
            'metadata': self.metadata
        }

    def from_dict(self, data: dict):
        self.task_id = data.get('task_id', '')
        self.run_id = data.get('run_id', '')
        self.child_session_key = data.get('child_session_key', '')
        self.description = data.get('description', '')
        self.status = data.get('status', SubtaskStatus.SPAWNED)
        self.deadline = datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
        self.max_retries = data.get('max_retries', 3)
        self.retries = data.get('retries', 0)
        self.attempt = data.get('attempt', 0)
        self.created_at = datetime.fromisoformat(data['created_at'])
        self.started_at = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        self.completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        self.output_paths = data.get('output_paths', [])
        self.artifacts = data.get('artifacts', [])
        self.summary = data.get('summary', '')
        self.error = data.get('error')
        self.result_data = data.get('result_data')
        self.metadata = data.get('metadata', {})


class EventLogger:
    """Structured event logger for orchestrator state transitions"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = log_dir / "events.jsonl"
        self.lock = threading.Lock()
    
    def log(self, task_id: str, state_from: str, state_to: str, 
            run_id: str = "", attempt: int = 0, elapsed_ms: float = 0,
            reason: str = "", **kwargs):
        """Log a state transition event"""
        event = {
            'ts': datetime.now().isoformat(),
            'task_id': task_id,
            'state_from': state_from,
            'state_to': state_to,
            'run_id': run_id,
            'attempt': attempt,
            'elapsed_ms': elapsed_ms,
            'reason': reason,
            **kwargs
        }
        
        with self.lock:
            with open(self.events_file, 'a') as f:
                f.write(json.dumps(event) + '\n')


class Orchestrator:
    """Main orchestrator managing subtasks with reliable callback system"""
    
    def __init__(self, workspace_dir: str = "/home/moonlight/.openclaw/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.orchestrator_dir = self.workspace_dir / "tools" / "orchestrator"
        self.orchestrator_dir.mkdir(parents=True, exist_ok=True)
        
        # Subtasks directory for fallback mailbox
        self.subtasks_dir = self.workspace_dir / "reports" / "subtasks"
        self.subtasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Events directory for structured logging
        self.events_dir = self.workspace_dir / "reports" / "orchestrator"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # Current pending subtasks
        self.pending_subtasks: Dict[str, Subtask] = {}
        self.completed_subtasks: Dict[str, Subtask] = {}
        self.lock = threading.Lock()  # Use Lock(), not RLock - call _locked() versions when already holding lock
        self._lock_holder = threading.local()  # Track lock ownership for _locked() safety
        self._lock_holder.depth = 0  # Initialize to 0 (not holding lock)
        
        # Event logger
        self.event_logger = EventLogger(self.events_dir)
        
        # Configuration
        self.max_poll_interval = 20  # seconds
        self.initial_poll_interval = 1  # second
        self.default_deadline = timedelta(hours=1)
        self.jitter_factor = 0.1  # ±10% jitter
        
        # Load any existing pending tasks (for recovery)
        self.load_pending_from_storage()
    
    def _check_lock_held(self) -> bool:
        """Check if current thread holds the lock (debug helper)"""
        return getattr(self._lock_holder, 'depth', 0) > 0

    def spawn_task(self, description: str, 
                   deadline: Optional[datetime] = None, 
                   max_retries: int = 3, 
                   model: str = "",
                   **kwargs) -> Tuple[str, str, str]:
        """
        Spawn a NEW subtask (returns task_id, run_id, session_key)
        
        Use this when you want to create a new subagent task.
        The returned values should be used in sessions_spawn.
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        session_key = f"agent:main:subagent:{uuid.uuid4().hex}"
        
        with self.lock:
            subtask = Subtask(
                task_id=task_id,
                run_id=run_id,
                child_session_key=session_key,
                description=description,
                deadline=deadline or (datetime.now() + self.default_deadline),
                max_retries=max_retries,
                model=model,
                **kwargs
            )
            subtask.status = SubtaskStatus.PENDING
            subtask.started_at = datetime.now()
            
            self.pending_subtasks[task_id] = subtask
            self._save_pending_to_storage_locked()
            
            self.event_logger.log(
                task_id=task_id,
                state_from="none",
                state_to=SubtaskStatus.PENDING,
                run_id=run_id,
                reason="spawned"
            )
            
            logger.info(f"Spawned task {task_id} with run_id {run_id}")
            
        return task_id, run_id, session_key

    def attach_subtask(self, run_id: str, child_session_key: str,
                       description: str = "",
                       deadline: Optional[datetime] = None,
                       max_retries: int = 3,
                       **kwargs) -> str:
        """
        Attach to an EXISTING subagent run
        
        Use this when the subagent was already spawned externally
        and you want to track it with the orchestrator.
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        with self.lock:
            subtask = Subtask(
                task_id=task_id,
                run_id=run_id,
                child_session_key=child_session_key,
                description=description,
                deadline=deadline or (datetime.now() + self.default_deadline),
                max_retries=max_retries,
                **kwargs
            )
            subtask.status = SubtaskStatus.PENDING
            subtask.started_at = datetime.now()
            
            self.pending_subtasks[task_id] = subtask
            self._save_pending_to_storage_locked()
            
            self.event_logger.log(
                task_id=task_id,
                state_from="none",
                state_to=SubtaskStatus.PENDING,
                run_id=run_id,
                reason="attached"
            )
            
            logger.info(f"Attached to existing run {run_id} as task {task_id}")
            
        return task_id

    def join_all(self, timeout: float = 300, per_task_timeout: float = 600) -> bool:
        """
        Join all pending subtasks with timeout
        
        Args:
            timeout: Global timeout for the join operation
            per_task_timeout: Maximum time per task before marking as timeout
        
        Returns:
            True if all tasks completed, False if any timed out
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                pending_count = len(self.pending_subtasks)
                if pending_count == 0:
                    logger.info("All subtasks completed")
                    return True
            
            # Check global timeout
            if time.time() - start_time > timeout:
                logger.warning(f"Global join timeout after {timeout}s")
                return False
            
            # Poll for completion
            completed = self._poll_all(per_task_timeout)
            
            if completed > 0:
                logger.info(f"Join progress: {completed} tasks completed")
            
            # Exponential backoff with jitter
            base_interval = min(
                self.initial_poll_interval * (2 ** min(self._get_max_retries(), 4)),
                self.max_poll_interval
            )
            # Add jitter (±10%)
            jitter = base_interval * self.jitter_factor * (random.random() * 2 - 1)
            poll_interval = max(0.1, base_interval + jitter)
            
            time.sleep(poll_interval)

    def _get_max_retries(self) -> int:
        """Get max retries among pending tasks"""
        if not self.pending_subtasks:
            return 0
        return max([task.retries for task in self.pending_subtasks.values()], default=0)

    def _poll_all(self, per_task_timeout: float) -> int:
        """Poll all pending subtasks for completion"""
        completed_count = 0
        now = datetime.now()
        
        with self.lock:
            tasks_to_check = list(self.pending_subtasks.items())
        
        for task_id, task in tasks_to_check:
            elapsed = (now - task.created_at).total_seconds()
            
            # Check per-task timeout
            if elapsed > per_task_timeout:
                if self._handle_task_timeout(task):
                    completed_count += 1
                continue
            
            # Check for completion
            check_result = self._poll_single_task(task)
            if check_result:
                completed_count += 1
        
        return completed_count

    def _poll_single_task(self, task: Subtask) -> bool:
        """Poll a single task for completion, return True if completed"""
        # First check mailbox (most reliable fallback)
        mailbox_result = self._check_mailbox_fallback(task)
        if mailbox_result:
            self._mark_task_completed(task, mailbox_result)
            return True
        
        # Check for explicit receipt (if available)
        receipt = self._check_explicit_receipt(task)
        if receipt:
            self._mark_task_completed(task, receipt)
            return True
        
        # Check for task-specific deadline
        if datetime.now() > task.deadline:
            return self._handle_task_timeout(task)
        
        # Still pending
        return False

    def _check_explicit_receipt(self, task: Subtask) -> Optional[Dict[str, Any]]:
        """Check for explicit receipt from subagent (if session system available)"""
        # This would check session history for SUBTASK_DONE message
        # Implementation depends on available session tools
        return None

    def _check_mailbox_fallback(self, task: Subtask) -> Optional[Dict[str, Any]]:
        """Check fallback mailbox file for completion"""
        mailbox_file = self.subtasks_dir / f"{task.task_id}.done.json"
        
        if mailbox_file.exists():
            try:
                with open(mailbox_file, 'r') as f:
                    result = json.load(f)
                
                # Verify the result matches our task
                if result.get('task_id') == task.task_id:
                    # Validate receipt schema
                    if result.get('status') in ['ok', 'fail', 'timeout']:
                        return result
            except Exception as e:
                logger.error(f"Error reading mailbox file {mailbox_file}: {e}")
        
        return None

    def _mark_task_completed(self, task: Subtask, result: Dict[str, Any]):
        """Mark a task as completed with the given result (idempotent)"""
        with self.lock:
            # Idempotency: already completed, ignore duplicate
            if task.status == SubtaskStatus.COMPLETED:
                logger.info(f"Task {task.task_id} already completed, ignoring duplicate receipt")
                return
            
            elapsed_ms = 0
            if task.started_at:
                elapsed_ms = (datetime.now() - task.started_at).total_seconds() * 1000
            
            task.status = SubtaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result_data = result
            task.summary = result.get('summary', '')
            task.artifacts = result.get('artifacts', [])
            task.output_paths = result.get('output_paths', task.artifacts)
            task.error = result.get('error')
            
            # Move from pending to completed
            if task.task_id in self.pending_subtasks:
                del self.pending_subtasks[task.task_id]
            self.completed_subtasks[task.task_id] = task
            
            # Save to storage
            self._save_pending_to_storage_locked()
            
            # Log event
            self.event_logger.log(
                task_id=task.task_id,
                state_from=SubtaskStatus.PENDING,
                state_to=SubtaskStatus.COMPLETED,
                run_id=task.run_id,
                attempt=task.attempt,
                elapsed_ms=elapsed_ms,
                reason="completed"
            )
            
            logger.info(f"Task {task.task_id} marked as completed")

    def _handle_task_timeout(self, task: Subtask) -> bool:
        """Handle task timeout with retry logic"""
        with self.lock:
            if task.retries < task.max_retries:
                # Retry the task
                old_status = task.status
                task.status = SubtaskStatus.RETRYING
                task.retries += 1
                task.attempt += 1
                task.deadline = datetime.now() + self.default_deadline
                
                self._save_pending_to_storage_locked()
                
                self.event_logger.log(
                    task_id=task.task_id,
                    state_from=old_status,
                    state_to=SubtaskStatus.RETRYING,
                    run_id=task.run_id,
                    attempt=task.attempt,
                    reason=f"timeout_retry_{task.retries}"
                )
                
                logger.info(f"Task {task.task_id} timeout, retrying ({task.retries}/{task.max_retries})")
                return False
            else:
                # Max retries exceeded
                task.status = SubtaskStatus.TIMEOUT
                task.completed_at = datetime.now()
                
                # Move to completed
                if task.task_id in self.pending_subtasks:
                    del self.pending_subtasks[task.task_id]
                self.completed_subtasks[task.task_id] = task
                
                self._save_pending_to_storage_locked()
                
                self.event_logger.log(
                    task_id=task.task_id,
                    state_from=SubtaskStatus.PENDING,
                    state_to=SubtaskStatus.TIMEOUT,
                    run_id=task.run_id,
                    attempt=task.attempt,
                    reason="max_retries_exceeded"
                )
                
                logger.error(f"Task {task.task_id} failed after {task.max_retries} retries")
                return True

    def _save_pending_to_storage_locked(self):
        """
        Save pending tasks to storage - MUST be called while holding self.lock
        
        This is the internal version for use when caller already holds the lock.
        
        WARNING: Caller MUST hold self.lock before calling this method.
        Calling without holding the lock will cause race conditions.
        
        Debug mode: Set ORCHESTRATOR_DEBUG=1 to enable lock safety checks.
        """
        # Debug safety check (can be disabled in production)
        import os
        if os.environ.get('ORCHESTRATOR_DEBUG') == '1':
            # Python Lock doesn't have "owned_by_current_thread" API
            # This is a best-effort check for development
            if not self.lock.locked():
                raise RuntimeError(
                    "_save_pending_to_storage_locked() called without holding lock! "
                    "This is a race condition bug. Use _save_pending_to_storage() instead."
                )
        
        storage_file = self.orchestrator_dir / "pending_subtasks.json"
        tmp_file = storage_file.with_suffix('.tmp')
        
        # Build data (caller holds lock, so no need to re-acquire)
        data = {
            'pending': {k: v.to_dict() for k, v in self.pending_subtasks.items()},
            'completed': {k: v.to_dict() for k, v in self.completed_subtasks.items()},
            'timestamp': datetime.now().isoformat()
        }
        
        # Atomic write: write to temp, then rename
        try:
            with open(tmp_file, 'w') as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            os.rename(tmp_file, storage_file)
        except Exception as e:
            logger.error(f"Error saving pending tasks: {e}")
            if tmp_file.exists():
                tmp_file.unlink()

    def _save_pending_to_storage(self):
        """
        Save pending tasks to storage (public wrapper)
        
        Acquires lock and calls _locked version.
        Use this when caller does NOT hold the lock.
        """
        with self.lock:
            self._save_pending_to_storage_locked()

    def load_pending_from_storage(self):
        """Load pending tasks from persistent storage (for recovery)"""
        storage_file = self.orchestrator_dir / "pending_subtasks.json"
        
        if not storage_file.exists():
            return
            
        try:
            with open(storage_file, 'r') as f:
                data = json.load(f)
            
            with self.lock:
                for task_id, task_data in data.get('pending', {}).items():
                    task = Subtask("", "", "")
                    task.from_dict(task_data)
                    self.pending_subtasks[task_id] = task
                
                for task_id, task_data in data.get('completed', {}).items():
                    task = Subtask("", "", "")
                    task.from_dict(task_data)
                    self.completed_subtasks[task_id] = task
                    
            logger.info(f"Loaded {len(self.pending_subtasks)} pending and {len(self.completed_subtasks)} completed tasks from storage")
        except Exception as e:
            logger.error(f"Error loading pending tasks from storage: {e}")

    def process_explicit_receipt(self, receipt_data: Dict[str, Any]) -> bool:
        """Process an explicit receipt from a subagent (idempotent)"""
        task_id = receipt_data.get('task_id')
        
        with self.lock:
            if task_id in self.pending_subtasks:
                task = self.pending_subtasks[task_id]
                
                # Verify the receipt matches expected task
                if receipt_data.get('run_id') == task.run_id:
                    self._mark_task_completed(task, receipt_data)
                    return True
                else:
                    logger.warning(f"Receipt for task {task_id} has mismatched run_id")
                    return False
            elif task_id in self.completed_subtasks:
                # Already completed - idempotent handling
                logger.info(f"Receipt for task {task_id} but already completed - ignoring duplicate")
                return True
            else:
                logger.info(f"Receipt for task {task_id} but task not found")
                return False

    def generate_run_report(self) -> Dict[str, Any]:
        """Generate a comprehensive run report"""
        all_tasks = {**self.pending_subtasks, **self.completed_subtasks}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tasks': len(all_tasks),
            'pending_tasks': len(self.pending_subtasks),
            'completed_tasks': len(self.completed_subtasks),
            'success_rate': len([t for t in self.completed_subtasks.values() 
                                if t.status == SubtaskStatus.COMPLETED]) / len(all_tasks) if all_tasks else 0,
            'tasks': {
                task_id: task.to_dict() for task_id, task in all_tasks.items()
            },
            'summary_stats': {
                'total_duration': self._calculate_total_duration(),
                'avg_completion_time': self._calculate_avg_completion_time(),
                'retries_used': sum(task.retries for task in all_tasks.values()),
                'timeouts': len([t for t in self.completed_subtasks.values() 
                                if t.status == SubtaskStatus.TIMEOUT])
            }
        }
        
        # Write report to file
        report_file = self.orchestrator_dir / f"run_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

    def _calculate_total_duration(self) -> float:
        """Calculate total duration of all completed tasks"""
        if not self.completed_subtasks:
            return 0
        
        durations = []
        for task in self.completed_subtasks.values():
            if task.started_at and task.completed_at:
                durations.append((task.completed_at - task.started_at).total_seconds())
        
        return sum(durations)

    def _calculate_avg_completion_time(self) -> float:
        """Calculate average completion time"""
        durations = self._calculate_total_duration()
        completed_count = len(self.completed_subtasks)
        return durations / completed_count if completed_count > 0 else 0

    def gc(self, keep_days: int = 7):
        """Garbage collect old completed tasks"""
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        with self.lock:
            to_remove = [
                task_id for task_id, task in self.completed_subtasks.items()
                if task.completed_at and task.completed_at < cutoff
            ]
            for task_id in to_remove:
                del self.completed_subtasks[task_id]
        
        self._save_pending_to_storage()
        
        # Also clean mailbox files
        if self.subtasks_dir.exists():
            for f in self.subtasks_dir.glob("*.done.json"):
                try:
                    with open(f) as fp:
                        data = json.load(fp)
                    ts = datetime.fromisoformat(data.get('ts', data.get('timestamp', '')))
                    if ts < cutoff:
                        f.unlink()
                except:
                    pass
        
        return len(to_remove)
    
    def cleanup_zombie_tasks(self) -> Dict[str, Any]:
        """
        Clean up zombie tasks - tasks that are:
        1. Past deadline but still pending
        2. No receipt file
        3. No active session
        
        Returns:
            Dict with cleaned count and details
        """
        now = datetime.now()
        cleaned = []
        
        with self.lock:
            zombie_task_ids = []
            
            for task_id, task in list(self.pending_subtasks.items()):
                # Check if past deadline
                if task.deadline and now > task.deadline:
                    # Check if there's a receipt
                    receipt_file = self.subtasks_dir / f"{task_id}.done.json"
                    has_receipt = receipt_file.exists()
                    
                    # Check if session might still be active (simple heuristic)
                    # If deadline passed more than 5 minutes ago, definitely zombie
                    is_zombie = (now - task.deadline).total_seconds() > 300
                    
                    if is_zombie and not has_receipt:
                        zombie_task_ids.append(task_id)
                        cleaned.append({
                            "task_id": task_id,
                            "run_id": task.run_id,
                            "description": task.description[:50],
                            "deadline": task.deadline.isoformat() if task.deadline else None,
                            "status": "zombie_cleaned"
                        })
            
            # Remove zombie tasks from pending
            for task_id in zombie_task_ids:
                task = self.pending_subtasks[task_id]
                task.status = SubtaskStatus.TIMEOUT
                task.completed_at = now
                task.error = {"type": "zombie_cleanup", "message": "Task exceeded deadline without completion"}
                
                # Move to completed
                del self.pending_subtasks[task_id]
                self.completed_subtasks[task_id] = task
                
                self.event_logger.log(
                    task_id=task_id,
                    state_from=SubtaskStatus.PENDING,
                    state_to=SubtaskStatus.TIMEOUT,
                    run_id=task.run_id,
                    reason="zombie_cleanup"
                )
            
            self._save_pending_to_storage_locked()
        
        logger.info(f"Cleaned up {len(cleaned)} zombie tasks")
        return {
            "cleaned_count": len(cleaned),
            "cleaned_tasks": cleaned
        }
    
    def get_stuck_tasks(self) -> List[Dict[str, Any]]:
        """
        Get tasks that might be stuck - past deadline but still pending.
        Use this for diagnostics.
        """
        now = datetime.now()
        stuck = []
        
        with self.lock:
            for task_id, task in self.pending_subtasks.items():
                if task.deadline and now > task.deadline:
                    stuck.append({
                        "task_id": task_id,
                        "run_id": task.run_id,
                        "description": task.description[:50],
                        "deadline": task.deadline.isoformat() if task.deadline else None,
                        "overdue_seconds": (now - task.deadline).total_seconds() if task.deadline else 0
                    })
        
        return stuck


# Backwards compatible alias
def spawn_subtask(*args, **kwargs):
    """Deprecated: Use spawn_task or attach_subtask instead"""
    logger.warning("spawn_subtask is deprecated, use spawn_task or attach_subtask")
    return Orchestrator().attach_subtask(*args, **kwargs)


if __name__ == "__main__":
    # Quick test
    orch = Orchestrator()
    task_id, run_id, session_key = orch.spawn_task("Test task")
    print(f"Spawned: {task_id}, {run_id}, {session_key}")
