#!/usr/bin/env python3
import os
from __future__ import annotations

import json
import subprocess
from pathlib import Path

WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', Path(__file__).parent.parent))
TOOL = WORKSPACE / 'tools' / 'capture-wake-session-diff'
PROBE_DIR = WORKSPACE / 'artifacts' / 'session_reuse' / 'probe' / 'real_samples'


def test_capture_tool_outputs_incident_paths_and_level():
    result = subprocess.run([
        str(TOOL),
        '--chat-id', 'telegram:8420019401',
        '--account-id', 'manager',
        '--dm-scope', 'per-channel-peer',
        '--baseline', str(PROBE_DIR / 'normal_continuation_7886.json'),
        '--inbound-event-id', 'telegram:test-capture',
    ], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload['level'] in {'confirmed', 'likely', 'inconclusive'}
    assert Path(payload['current_probe_path']).exists()
    assert Path(payload['incident_report_path']).exists()
    assert 'diff' in payload
