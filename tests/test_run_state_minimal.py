#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
TOOL = WORKSPACE / 'tools' / 'run-state'
RUN_STATE = WORKSPACE / 'state' / 'durable_execution' / 'RUN_STATE.json'
WORKFLOW = WORKSPACE / 'WORKFLOW_STATE.json'


def test_run_state_derive_and_recoverable_hint():
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        subprocess.check_output([str(TOOL), 'update', '--patch-json', json.dumps({'last_error_type': None, 'hard_block': False, 'hard_block_reason': None})], text=True)
        WORKFLOW.write_text(json.dumps({
            'active': True,
            'workflow_type': 'serial',
            'steps': [
                {'id': 's1', 'task': 'do a', 'model': 'x', 'status': 'done'},
                {'id': 's2', 'task': 'do b', 'model': 'x', 'status': 'pending', 'depends_on': ['s1']},
            ]
        }))
        out = subprocess.check_output([str(TOOL), 'recover'], text=True)
        data = json.loads(out)
        assert data['resume_action'] == 'spawn_pending'
        assert data['recovery_hint']['should_auto_continue'] is True
        assert RUN_STATE.exists()
    finally:
        if old_workflow is None:
            WORKFLOW.unlink(missing_ok=True)
        else:
            WORKFLOW.write_text(old_workflow)


def test_run_state_hard_block_update():
    subprocess.check_output([str(TOOL), 'update', '--patch-json', json.dumps({'last_error_type': 'missing_permission', 'hard_block': True})], text=True)
    out = subprocess.check_output([str(TOOL), 'derive'], text=True)
    data = json.loads(out)
    assert data['resume_action'] == 'hard_block'
    assert data['hard_block'] is True
