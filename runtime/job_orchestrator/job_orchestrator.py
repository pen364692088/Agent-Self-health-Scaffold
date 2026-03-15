"""
Durable Job Orchestrator

Provides durable parent/child job orchestration with:
- Idempotency via idempotency_key
- Dependency DAG support
- Retry/backoff policies
- Ledger event logging
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_ledger import TaskLedger

JOBS_DIR = "artifacts/jobs"
MAX_RETRY_DEFAULT = 3


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff: str = "exponential"  # fixed | linear | exponential
    base_delay_sec: float = 1.0
    max_delay_sec: float = 60.0

    def calculate_delay(self, attempt: int) -> float:
        if self.backoff == "fixed":
            return self.base_delay_sec
        elif self.backoff == "linear":
            return min(self.base_delay_sec * attempt, self.max_delay_sec)
        elif self.backoff == "exponential":
            return min(self.base_delay_sec * (2 ** (attempt - 1)), self.max_delay_sec)
        return self.base_delay_sec

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobSpec:
    job_id: str
    task_id: str
    run_id: str
    agent_role: str  # manager | coder | auditor
    command: str
    args: List[str] = field(default_factory=list)
    timeout_sec: int = 3600
    retry_policy: Optional[RetryPolicy] = None
    depends_on: List[str] = field(default_factory=list)
    idempotency_key: str = ""
    parent_run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.retry_policy:
            d["retry_policy"] = self.retry_policy.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JobSpec":
        if "retry_policy" in d and d["retry_policy"]:
            d["retry_policy"] = RetryPolicy(**d["retry_policy"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class JobRunState:
    job_id: str
    status: str  # pending | running | succeeded | failed | retrying
    attempt: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    exit_code: Optional[int] = None
    output_path: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParentChildDependency:
    parent_job_id: str
    child_job_ids: List[str]
    wait_strategy: str = "all"  # all | any | none
    on_child_failure: str = "fail"  # fail | continue | retry_child

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JobOrchestrator:
    """Durable job orchestrator with dependency support."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.jobs_dir = self.root / JOBS_DIR
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = TaskLedger(self.root)
        self._idempotency_cache: Dict[str, str] = {}
        self._load_idempotency_cache()

    def _load_idempotency_cache(self) -> None:
        """Load existing idempotency keys to prevent duplicates."""
        for path in self.jobs_dir.glob("*.spec.json"):
            try:
                with path.open() as f:
                    spec = json.load(f)
                key = spec.get("idempotency_key")
                if key:
                    self._idempotency_cache[key] = spec["job_id"]
            except Exception:
                continue

    def submit_job(self, spec: JobSpec) -> str:
        """Submit a job for execution. Returns job_id."""
        # Check idempotency
        if spec.idempotency_key and spec.idempotency_key in self._idempotency_cache:
            existing_id = self._idempotency_cache[spec.idempotency_key]
            # Return existing job without creating new one
            return existing_id

        # Ensure job_id
        if not spec.job_id:
            spec.job_id = str(uuid.uuid4())

        # Set default retry policy
        if not spec.retry_policy:
            spec.retry_policy = RetryPolicy()

        # Persist spec
        spec_path = self.jobs_dir / f"{spec.job_id}.spec.json"
        with spec_path.open("w") as f:
            json.dump(spec.to_dict(), f, indent=2, ensure_ascii=False)

        # Initialize state
        state = JobRunState(
            job_id=spec.job_id,
            status="pending",
        )
        self._write_state(state)

        # Update cache
        if spec.idempotency_key:
            self._idempotency_cache[spec.idempotency_key] = spec.job_id

        # Log to ledger
        self._log_job_event(spec, "job_submitted")

        # Check dependencies
        if spec.depends_on:
            self._check_dependencies(spec)

        return spec.job_id

    def get_job_state(self, job_id: str) -> JobRunState:
        """Get current job state."""
        state_path = self.jobs_dir / f"{job_id}.state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"Job {job_id} not found")

        with state_path.open() as f:
            return JobRunState(**json.load(f))

    def get_job_spec(self, job_id: str) -> JobSpec:
        """Get job specification."""
        spec_path = self.jobs_dir / f"{job_id}.spec.json"
        if not spec_path.exists():
            raise FileNotFoundError(f"Job {job_id} not found")

        with spec_path.open() as f:
            return JobSpec.from_dict(json.load(f))

    def start_job(self, job_id: str) -> None:
        """Mark job as started."""
        state = self.get_job_state(job_id)
        state.status = "running"
        state.started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state.attempt += 1
        self._write_state(state)
        self._log_job_event(self.get_job_spec(job_id), "job_started")

    def complete_job(self, job_id: str, exit_code: int = 0, output_path: Optional[str] = None) -> None:
        """Mark job as completed."""
        state = self.get_job_state(job_id)
        state.status = "succeeded" if exit_code == 0 else "failed"
        state.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state.exit_code = exit_code
        state.output_path = output_path
        self._write_state(state)
        self._log_job_event(self.get_job_spec(job_id), "job_succeeded" if exit_code == 0 else "job_failed")

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error."""
        state = self.get_job_state(job_id)
        spec = self.get_job_spec(job_id)

        # Check retry policy
        if spec.retry_policy and state.attempt < spec.retry_policy.max_attempts:
            state.status = "retrying"
            state.error = error
            self._write_state(state)
            self._log_job_event(spec, "retry_scheduled")
        else:
            state.status = "failed"
            state.error = error
            state.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._write_state(state)
            self._log_job_event(spec, "job_failed")

    def await_children(self, parent_job_id: str, timeout_sec: int = 3600) -> List[JobRunState]:
        """Wait for all children to complete. Returns list of child states."""
        spec = self.get_job_spec(parent_job_id)
        if not spec.depends_on:
            return []

        deadline = time.time() + timeout_sec
        children: List[JobRunState] = []

        while time.time() < deadline:
            all_done = True
            children = []

            for child_id in spec.depends_on:
                try:
                    child_state = self.get_job_state(child_id)
                    children.append(child_state)
                    if child_state.status not in ("succeeded", "failed"):
                        all_done = False
                except FileNotFoundError:
                    all_done = False

            if all_done:
                self._log_job_event(spec, "dependency_resolved")
                return children

            time.sleep(1)

        raise TimeoutError(f"Timeout waiting for children of {parent_job_id}")

    def _check_dependencies(self, spec: JobSpec) -> bool:
        """Check if all dependencies are satisfied."""
        for dep_id in spec.depends_on:
            try:
                state = self.get_job_state(dep_id)
                if state.status == "failed":
                    return False
            except FileNotFoundError:
                return False
        return True

    def _write_state(self, state: JobRunState) -> None:
        """Write job state to file."""
        state_path = self.jobs_dir / f"{state.job_id}.state.json"
        with state_path.open("w") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def _log_job_event(self, spec: JobSpec, event_type: str) -> None:
        """Log job event to ledger."""
        event = {
            "event_id": f"evt-job-{spec.job_id}-{event_type}",
            "task_id": spec.task_id,
            "run_id": spec.run_id,
            "parent_run_id": spec.parent_run_id,
            "step_id": spec.job_id,
            "type": event_type,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": {"job_id": spec.job_id, "agent_role": spec.agent_role},
            "idempotency_key": f"job-{spec.job_id}-{event_type}",
        }
        self.ledger.append_event(event)


def submit_job(root: Path | str, spec: JobSpec) -> str:
    """Convenience function to submit a job."""
    orchestrator = JobOrchestrator(root)
    return orchestrator.submit_job(spec)


def get_job_state(root: Path | str, job_id: str) -> JobRunState:
    """Convenience function to get job state."""
    orchestrator = JobOrchestrator(root)
    return orchestrator.get_job_state(job_id)
