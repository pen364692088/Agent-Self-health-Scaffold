#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
ORCH = WORKSPACE / 'tools' / 'subtask-orchestrate'
WORKER = WORKSPACE / 'tools' / 'callback-worker'
WORKFLOW = WORKSPACE / 'WORKFLOW_STATE.json'


def test_resume_is_single_advancement_entrypoint_for_pending_workflow():
    old = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        WORKFLOW.write_text(json.dumps({
            'active': True,
            'steps': [
                {'id': 's1', 'task': 'do x', 'model': 'gpt', 'status': 'pending'}
            ]
        }))
        out = subprocess.check_output([str(ORCH), 'resume'], text=True)
        data = json.loads(out)
        assert data['entrypoint'] == 'subtask-orchestrate.resume'
        assert data['action'] in ('spawn_next', 'wait', 'none', 'notify_user')
        assert 'advance' in data
    finally:
        if old is None:
            WORKFLOW.unlink(missing_ok=True)
        else:
            WORKFLOW.write_text(old)


def test_callback_worker_reports_single_entrypoint_health():
    out = subprocess.check_output([str(WORKER), '--health'], text=True)
    data = json.loads(out)
    assert data['entrypoint'] == 'subtask-orchestrate resume'
