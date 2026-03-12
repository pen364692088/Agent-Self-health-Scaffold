import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
LOCK_DIR = W / 'artifacts' / 'self_health' / 'locks'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_scheduler_quick_mode():
    code, out, err = run([str(W/'tools'/'agent-self-health-scheduler'), '--mode', 'quick', '--json', '--force'])
    assert code == 0, err
    data = json.loads(out)
    assert data['mode'] == 'quick'
    assert 'tasks' in data
    assert 'recovery_apply' in data['tasks']
    assert data['tasks']['recovery_apply'].get('exit_code') == 0


def test_scheduler_full_mode():
    code, out, err = run([str(W/'tools'/'agent-self-health-scheduler'), '--mode', 'full', '--json', '--force'])
    assert code == 0, err
    data = json.loads(out)
    assert data['mode'] == 'full'
    assert 'recovery_apply' in data['tasks']


def test_gate_check():
    code, out, err = run([str(W/'tools'/'gate-self-health-check'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert 'gate_a' in data
    assert 'gate_b' in data
    assert 'gate_c' in data
    assert data['gate_a']['status'] in {'PASS', 'FAIL'}
