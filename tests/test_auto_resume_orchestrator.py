import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

W = Path(os.environ.get('OPENCLAW_WORKSPACE', '/home/moonlight/.openclaw/workspace'))
TOOL = W / 'tools' / 'auto-resume-orchestrator'
RUN_STATE = W / 'state' / 'durable_execution' / 'RUN_STATE.json'
WORKFLOW = W / 'WORKFLOW_STATE.json'
CONFIG = W / 'state' / 'durable_execution' / 'AUTO_RESUME_CONFIG.json'
RUNTIME = W / 'state' / 'durable_execution' / 'AUTO_RESUME_RUNTIME.json'


def run(cmd):
    return subprocess.run(cmd, cwd=W, capture_output=True, text=True)


def _restore(path, old):
    if old is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old)


def test_auto_resume_happy_path_resumes_pending_workflow_step():
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    old_run_state = RUN_STATE.read_text() if RUN_STATE.exists() else None
    old_config = CONFIG.read_text() if CONFIG.exists() else None
    old_runtime = RUNTIME.read_text() if RUNTIME.exists() else None
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'enabled': True, 'cooldown_seconds': 1, 'lease_ttl_seconds': 60, 'max_recovery_attempts_per_target': 3, 'task_overrides': {}}, indent=2))
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'echo back: auto-resume', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.parent.mkdir(parents=True, exist_ok=True)
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'x', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.write_text(json.dumps({'status': 'running', 'hard_block': False, 'resume_action': 'spawn_pending', 'recovery_hint': {'should_auto_continue': True}, 'next_step': {'id': 's1'}, 'last_checkpoint': {'ts': '2026-03-11T14:00:00'}}))
        r = run([str(TOOL), '--once', '--json'])
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data['action'] == 'resumed'
        assert data['resume']['action'] in {'spawn_next', 'wait', 'none', 'notify_user'}
    finally:
        _restore(WORKFLOW, old_workflow); _restore(RUN_STATE, old_run_state); _restore(CONFIG, old_config); _restore(RUNTIME, old_runtime)


def test_auto_resume_respects_global_disable():
    old_config = CONFIG.read_text() if CONFIG.exists() else None
    old_runtime = RUNTIME.read_text() if RUNTIME.exists() else None
    old_run_state = RUN_STATE.read_text() if RUN_STATE.exists() else None
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'enabled': False, 'cooldown_seconds': 1, 'lease_ttl_seconds': 60, 'max_recovery_attempts_per_target': 3, 'task_overrides': {}}, indent=2))
        RUN_STATE.parent.mkdir(parents=True, exist_ok=True)
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'x', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.write_text(json.dumps({'status': 'running', 'hard_block': False, 'resume_action': 'spawn_pending', 'recovery_hint': {'should_auto_continue': True}, 'next_step': {'id': 's1'}, 'last_checkpoint': {'ts': '2026-03-11T14:00:00'}}))
        r = run([str(TOOL), '--once', '--json'])
        data = json.loads(r.stdout)
        assert data['action'] == 'skip'
        assert data['reason'] == 'global_disabled'
    finally:
        _restore(CONFIG, old_config); _restore(RUNTIME, old_runtime); _restore(RUN_STATE, old_run_state); _restore(WORKFLOW, old_workflow)


def test_auto_resume_respects_task_override_disable():
    old_config = CONFIG.read_text() if CONFIG.exists() else None
    old_runtime = RUNTIME.read_text() if RUNTIME.exists() else None
    old_run_state = RUN_STATE.read_text() if RUN_STATE.exists() else None
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'enabled': True, 'cooldown_seconds': 1, 'lease_ttl_seconds': 60, 'max_recovery_attempts_per_target': 3, 'task_overrides': {'s1': {'enabled': False}}}, indent=2))
        RUN_STATE.parent.mkdir(parents=True, exist_ok=True)
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'x', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.write_text(json.dumps({'status': 'running', 'hard_block': False, 'resume_action': 'spawn_pending', 'recovery_hint': {'should_auto_continue': True}, 'next_step': {'id': 's1'}, 'last_checkpoint': {'ts': '2026-03-11T14:00:00'}}))
        r = run([str(TOOL), '--once', '--json'])
        data = json.loads(r.stdout)
        assert data['action'] == 'skip'
        assert data['reason'] == 'task_override_disabled'
    finally:
        _restore(CONFIG, old_config); _restore(RUNTIME, old_runtime); _restore(RUN_STATE, old_run_state); _restore(WORKFLOW, old_workflow)


def test_auto_resume_cooldown_prevents_duplicate_resume():
    old_config = CONFIG.read_text() if CONFIG.exists() else None
    old_runtime = RUNTIME.read_text() if RUNTIME.exists() else None
    old_run_state = RUN_STATE.read_text() if RUN_STATE.exists() else None
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'enabled': True, 'cooldown_seconds': 999, 'lease_ttl_seconds': 60, 'max_recovery_attempts_per_target': 3, 'task_overrides': {}}, indent=2))
        RUN_STATE.parent.mkdir(parents=True, exist_ok=True)
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'x', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.write_text(json.dumps({'status': 'running', 'hard_block': False, 'resume_action': 'spawn_pending', 'recovery_hint': {'should_auto_continue': True}, 'next_step': {'id': 's1'}, 'last_checkpoint': {'ts': '2026-03-11T14:00:00'}}))
        RUNTIME.parent.mkdir(parents=True, exist_ok=True)
        RUNTIME.write_text(json.dumps({'last_attempt_at': datetime.now().isoformat(), 'last_target': 's1', 'last_checkpoint_ts': '2026-03-11T14:00:00', 'last_result': 'resumed', 'recovery_counts': {}}, indent=2))
        r = run([str(TOOL), '--once', '--json'])
        data = json.loads(r.stdout)
        assert data['action'] == 'skip'
        assert data['reason'] == 'cooldown_active'
    finally:
        _restore(CONFIG, old_config); _restore(RUNTIME, old_runtime); _restore(RUN_STATE, old_run_state); _restore(WORKFLOW, old_workflow)


def test_auto_resume_skips_hard_blocked_work():
    old_config = CONFIG.read_text() if CONFIG.exists() else None
    old_runtime = RUNTIME.read_text() if RUNTIME.exists() else None
    old_run_state = RUN_STATE.read_text() if RUN_STATE.exists() else None
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'enabled': True, 'cooldown_seconds': 1, 'lease_ttl_seconds': 60, 'max_recovery_attempts_per_target': 3, 'task_overrides': {}}, indent=2))
        RUN_STATE.parent.mkdir(parents=True, exist_ok=True)
        WORKFLOW.write_text(json.dumps({'active': True, 'workflow_type': 'serial', 'steps': [{'id': 's1', 'task': 'x', 'model': 'gpt', 'status': 'pending'}]}))
        RUN_STATE.write_text(json.dumps({'status': 'running', 'hard_block': True, 'resume_action': 'hard_block', 'recovery_hint': {'should_auto_continue': False}, 'next_step': {'id': 's1'}, 'last_checkpoint': {'ts': '2026-03-11T14:00:00'}}))
        r = run([str(TOOL), '--once', '--json'])
        data = json.loads(r.stdout)
        assert data['action'] == 'skip'
        assert data['reason'] == 'hard_blocked'
    finally:
        _restore(CONFIG, old_config); _restore(RUNTIME, old_runtime); _restore(RUN_STATE, old_run_state); _restore(WORKFLOW, old_workflow)
