#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
ROLLUP = WORKSPACE / 'scripts' / 'openviking_daily_rollup.py'


def test_daily_rollup_aggregates_metrics_correctly(tmp_path):
    day = '20990101'
    ops_root = tmp_path / 'ops_runs' / day
    run1 = ops_root / 'run1'
    run2 = ops_root / 'run2'
    run1.mkdir(parents=True)
    run2.mkdir(parents=True)

    for i, run in enumerate([run1, run2], start=1):
        (run / 'ops_run.json').write_text(json.dumps({'run_id': f'r{i}', 'status': 'ok', 'errors': []}))
        (run / 'metrics.json').write_text(json.dumps({
            'coverage': {'min': 0.9 - i*0.01, 'p50': 0.95, 'p95': 0.99},
            'skipped_chunks_count': i,
            'fallback_trigger_count': i*2,
            'dual_guard_trim_count': i*3,
            'offenders_topN': [{'doc_id': 'doc://x'}],
        }))
        (run / 'policy_decision.json').write_text(json.dumps({'decisions': [{'level': 'WARN' if i == 1 else 'ERROR'}]}))

    out_root = tmp_path / 'daily'
    r = subprocess.run([
        'python3', str(ROLLUP), '--date', day, '--ops-root', str(tmp_path / 'ops_runs'), '--out-root', str(out_root), '--json'
    ], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    payload = json.loads(r.stdout)
    rollup = json.loads(Path(payload['daily_rollup']).read_text())

    assert rollup['run_count'] == 2
    assert rollup['skipped_chunks_count']['sum'] == 3
    assert rollup['fallback_trigger_count']['sum'] == 6
    assert rollup['dual_guard_trim_count']['sum'] == 9
    assert rollup['policy_level_distribution']['WARN'] == 1
    assert rollup['policy_level_distribution']['ERROR'] == 1
