#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
TOOL = WORKSPACE / 'tools' / 'session-route-probe'


def run(*args: str) -> dict:
    result = subprocess.run([str(TOOL), *args], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_probe_creates_session_key_and_runtime_shape(tmp_path):
    out = tmp_path / 'probe.json'
    payload = run(
        'probe',
        '--chat-id', 'telegram:8420019401',
        '--account-id', 'manager',
        '--dm-scope', 'per-channel-peer',
        '--out', str(out),
    )
    probe = payload['probe']
    assert probe['route']['session_key']
    assert 'decision_preview' in probe['route']
    assert probe['route_inputs_hash']
    assert Path(payload['saved_to']).exists()


def test_diff_detects_thread_change(tmp_path):
    left = {
        'probe_id': 'a',
        'route_inputs': {'chat_id': 'telegram:1', 'thread_id': 'x', 'account_id': 'manager', 'dm_scope': 'per-channel-peer', 'peer_id': 'telegram:1'},
        'route': {'session_key': 'agent:main:direct:telegram:1:thread:x'},
        'runtime': {'runtime_session_id': 'agent:main:direct:telegram:1:thread:x'},
        'heuristics': {'suspected_cause': 'unknown'},
    }
    right = {
        'probe_id': 'b',
        'route_inputs': {'chat_id': 'telegram:1', 'thread_id': 'y', 'account_id': 'manager', 'dm_scope': 'per-channel-peer', 'peer_id': 'telegram:1'},
        'route': {'session_key': 'agent:main:direct:telegram:1:thread:y'},
        'runtime': {'runtime_session_id': 'agent:main:direct:telegram:1:thread:y'},
        'heuristics': {'suspected_cause': 'unknown'},
    }
    left_path = tmp_path / 'left.json'
    right_path = tmp_path / 'right.json'
    left_path.write_text(json.dumps(left))
    right_path.write_text(json.dumps(right))
    diff = run('diff', '--left', str(left_path), '--right', str(right_path))
    assert diff['session_key_changed'] is True
    assert diff['runtime_session_changed'] is True
    assert diff['suspected_cause'] == 'suspected_thread_change'
