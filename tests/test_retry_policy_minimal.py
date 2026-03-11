#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
POLICY = WORKSPACE / 'tools' / 'retry-policy'
HANDLER = WORKSPACE / 'tools' / 'subagent-completion-handler'
WORKFLOW = WORKSPACE / 'WORKFLOW_STATE.json'


def test_retry_policy_degrades_on_second_retry():
    out = subprocess.check_output([str(POLICY), 'decide', '--error-type', 'tool_failed', '--retry-count', '1', '--max-retries', '3', '--model', 'gpt', '--degraded-model', 'haiku'], text=True)
    data = json.loads(out)
    assert data['action'] == 'retry'
    assert data['mode'] == 'retry_degraded'
    assert data['next_model'] == 'haiku'


def test_failed_step_schedules_retry_instead_of_escalating():
    old = WORKFLOW.read_text() if WORKFLOW.exists() else None
    try:
        WORKFLOW.write_text(json.dumps({
            'active': True,
            'steps': [
                {'id': 's1', 'task_id': 't1', 'task': 'do x', 'model': 'gpt', 'degraded_model': 'haiku', 'status': 'running', 'run_id': 'run1', 'retry_count': 0, 'max_retries': 2}
            ]
        }))
        payload = json.dumps({'task_id': 't1', 'run_id': 'run1', 'status': 'failed', 'summary': 'tool blew up', 'error': {'type': 'tool_failed'}})
        out = subprocess.check_output([str(HANDLER), '--payload', payload], text=True)
        data = json.loads(out)
        assert data['action'] == 'spawn_next'
        wf = json.loads(WORKFLOW.read_text())
        step = wf['steps'][0]
        assert step['status'] == 'pending'
        assert step['retry_count'] == 1
    finally:
        if old is None:
            WORKFLOW.unlink(missing_ok=True)
        else:
            WORKFLOW.write_text(old)
