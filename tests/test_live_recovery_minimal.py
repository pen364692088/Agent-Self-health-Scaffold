#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
RUN_STATE = WORKSPACE / 'tools' / 'run-state'
RECOVERY = WORKSPACE / 'tools' / 'session-start-recovery'
WORKFLOW = WORKSPACE / 'WORKFLOW_STATE.json'
LAST_SESSION = WORKSPACE / '.last_session_id'


def test_restart_recovery_surfaces_auto_continue_for_pending_step():
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    old_last = LAST_SESSION.read_text() if LAST_SESSION.exists() else None
    try:
        subprocess.check_output([str(RUN_STATE), 'update', '--patch-json', json.dumps({'last_error_type': None, 'hard_block': False, 'hard_block_reason': None})], text=True)
        WORKFLOW.write_text(json.dumps({
            'active': True,
            'workflow_type': 'serial',
            'steps': [
                {'id': 's1', 'task': 'resume me', 'model': 'gpt', 'status': 'pending'}
            ]
        }))
        LAST_SESSION.write_text('old-session')
        env = os.environ.copy()
        env['OPENCLAW_SESSION_ID'] = 'new-session'
        out = subprocess.check_output([str(RECOVERY), '--recover', '--json'], text=True, env=env)
        data = json.loads(out)
        assert data['is_new_session'] is True
        assert data['durable_resume_action'] == 'spawn_pending'
        assert data['durable_should_auto_continue'] is True
    finally:
        if old_workflow is None:
            WORKFLOW.unlink(missing_ok=True)
        else:
            WORKFLOW.write_text(old_workflow)
        if old_last is None:
            LAST_SESSION.unlink(missing_ok=True)
        else:
            LAST_SESSION.write_text(old_last)


def test_compact_like_recovery_keeps_idle_when_no_live_work():
    old_workflow = WORKFLOW.read_text() if WORKFLOW.exists() else None
    old_last = LAST_SESSION.read_text() if LAST_SESSION.exists() else None
    try:
        WORKFLOW.unlink(missing_ok=True)
        subprocess.check_output([str(RUN_STATE), 'update', '--patch-json', json.dumps({'last_error_type': None, 'hard_block': False, 'hard_block_reason': None})], text=True)
        LAST_SESSION.write_text('older-session')
        env = os.environ.copy()
        env['OPENCLAW_SESSION_ID'] = 'compact-new-session'
        out = subprocess.check_output([str(RECOVERY), '--recover', '--json'], text=True, env=env)
        data = json.loads(out)
        assert data['is_new_session'] is True
        assert data['durable_resume_action'] == 'idle'
        assert data['durable_should_auto_continue'] is False
    finally:
        if old_workflow is None:
            WORKFLOW.unlink(missing_ok=True)
        else:
            WORKFLOW.write_text(old_workflow)
        if old_last is None:
            LAST_SESSION.unlink(missing_ok=True)
        else:
            LAST_SESSION.write_text(old_last)
