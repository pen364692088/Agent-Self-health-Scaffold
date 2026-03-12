"""Tests for Durable Job Orchestrator."""
import json
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from job_orchestrator.job_orchestrator import (
    JobOrchestrator,
    JobSpec,
    JobRunState,
    RetryPolicy,
    ParentChildDependency,
    submit_job,
    get_job_state,
)


def test_submit_job_creates_files(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        idempotency_key="unique-key-1",
    )

    job_id = orchestrator.submit_job(spec)
    assert job_id == "job-1"

    spec_path = tmp_path / "artifacts/jobs/job-1.spec.json"
    state_path = tmp_path / "artifacts/jobs/job-1.state.json"

    assert spec_path.exists()
    assert state_path.exists()


def test_submit_job_is_idempotent(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        idempotency_key="unique-key-1",
    )

    orchestrator.submit_job(spec)

    # Submit again with same idempotency_key
    spec2 = JobSpec(
        job_id="job-2",  # Different job_id
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        idempotency_key="unique-key-1",  # Same key
    )

    returned_id = orchestrator.submit_job(spec2)
    assert returned_id == "job-1"  # Returns existing job

    # Should not create job-2 files
    assert not (tmp_path / "artifacts/jobs/job-2.spec.json").exists()


def test_get_job_state(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        idempotency_key="key-1",
    )
    orchestrator.submit_job(spec)

    state = orchestrator.get_job_state("job-1")
    assert state.status == "pending"
    assert state.attempt == 0


def test_start_and_complete_job(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        idempotency_key="key-1",
    )
    orchestrator.submit_job(spec)

    orchestrator.start_job("job-1")
    state = orchestrator.get_job_state("job-1")
    assert state.status == "running"
    assert state.attempt == 1

    orchestrator.complete_job("job-1", exit_code=0, output_path="/tmp/output")
    state = orchestrator.get_job_state("job-1")
    assert state.status == "succeeded"
    assert state.exit_code == 0


def test_fail_job_with_retry(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        retry_policy=RetryPolicy(max_attempts=3, backoff="exponential"),
        idempotency_key="key-1",
    )
    orchestrator.submit_job(spec)
    orchestrator.start_job("job-1")

    # First failure should trigger retry
    orchestrator.fail_job("job-1", "temporary error")
    state = orchestrator.get_job_state("job-1")
    assert state.status == "retrying"

    # Start again and fail again
    orchestrator.start_job("job-1")
    orchestrator.fail_job("job-1", "another error")
    state = orchestrator.get_job_state("job-1")
    assert state.status == "retrying"


def test_fail_job_exceeds_retry_limit(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo hello",
        retry_policy=RetryPolicy(max_attempts=2),
        idempotency_key="key-1",
    )
    orchestrator.submit_job(spec)

    # Attempt 1
    orchestrator.start_job("job-1")
    orchestrator.fail_job("job-1", "error 1")

    # Attempt 2
    orchestrator.start_job("job-1")
    orchestrator.fail_job("job-1", "error 2")

    state = orchestrator.get_job_state("job-1")
    assert state.status == "failed"


def test_dependency_tracking(tmp_path):
    orchestrator = JobOrchestrator(tmp_path)

    # Create parent job
    parent_spec = JobSpec(
        job_id="parent-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="manager",
        command="manage",
        idempotency_key="parent-key",
    )
    orchestrator.submit_job(parent_spec)

    # Create child job with dependency
    child_spec = JobSpec(
        job_id="child-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="code",
        depends_on=["parent-1"],
        idempotency_key="child-key",
    )
    orchestrator.submit_job(child_spec)

    spec = orchestrator.get_job_spec("child-1")
    assert "parent-1" in spec.depends_on


def test_retry_policy_backoff_calculation():
    policy = RetryPolicy(max_attempts=5, backoff="exponential", base_delay_sec=1.0)

    assert policy.calculate_delay(1) == 1.0
    assert policy.calculate_delay(2) == 2.0
    assert policy.calculate_delay(3) == 4.0
    assert policy.calculate_delay(4) == 8.0

    policy_linear = RetryPolicy(backoff="linear", base_delay_sec=2.0)
    assert policy_linear.calculate_delay(1) == 2.0
    assert policy_linear.calculate_delay(2) == 4.0
    assert policy_linear.calculate_delay(3) == 6.0

    policy_fixed = RetryPolicy(backoff="fixed", base_delay_sec=5.0)
    assert policy_fixed.calculate_delay(1) == 5.0
    assert policy_fixed.calculate_delay(2) == 5.0


def test_convenience_functions(tmp_path):
    spec = JobSpec(
        job_id="job-1",
        task_id="task-1",
        run_id="run-1",
        agent_role="coder",
        command="echo",
        idempotency_key="key-1",
    )

    job_id = submit_job(tmp_path, spec)
    assert job_id == "job-1"

    state = get_job_state(tmp_path, "job-1")
    assert state.status == "pending"
