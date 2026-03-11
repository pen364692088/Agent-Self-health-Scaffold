#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
POLICY = WORKSPACE / 'tools' / 'hard-block-policy'
RUN_STATE = WORKSPACE / 'tools' / 'run-state'


def test_hard_block_policy_classify():
    out = subprocess.check_output([str(POLICY), 'classify', '--error-type', 'missing_permission'], text=True)
    data = json.loads(out)
    assert data['hard_block'] is True
    assert data['reason'] == 'missing_permission'


def test_non_hard_block_error_stays_non_blocking():
    subprocess.check_output([str(RUN_STATE), 'update', '--patch-json', json.dumps({'last_error_type': 'subagent_failed', 'hard_block': False})], text=True)
    out = subprocess.check_output([str(RUN_STATE), 'derive'], text=True)
    data = json.loads(out)
    assert data['hard_block'] is False
