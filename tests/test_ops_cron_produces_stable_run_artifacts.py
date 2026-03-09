#!/usr/bin/env python3
import os

import json
import subprocess
from pathlib import Path

WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', Path(__file__).parent.parent))
CRON = WORKSPACE / 'scripts' / 'openviking_ops_cron.py'


def _pick_one_doc_uri() -> str:
    result = subprocess.run(
        ['openviking', '-o', 'json', 'ls', 'viking://resources/user/memory/'],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    for item in payload.get('result', []):
        if not item.get('isDir'):
            return item['uri']
    raise RuntimeError('No leaf doc found')


def test_ops_cron_produces_stable_run_artifacts():
    doc = _pick_one_doc_uri()
    r = subprocess.run(['python3', str(CRON), '--doc-ids', doc, '--json'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    payload = json.loads(r.stdout)
    run_dir = Path(payload['artifacts']['run_dir'])
    assert (run_dir / 'ops_run.json').exists()
    assert (run_dir / 'healthcheck_result.json').exists()
    assert (run_dir / 'metrics.json').exists()
    assert (run_dir / 'policy_decision.json').exists()
