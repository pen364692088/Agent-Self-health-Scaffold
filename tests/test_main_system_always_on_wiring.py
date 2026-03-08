import json
import subprocess
from pathlib import Path

W = Path('/home/moonlight/.openclaw/workspace')


def run(cmd):
    return subprocess.run(cmd, cwd=W, capture_output=True, text=True)


def test_policy_exists():
    p = W / 'POLICIES' / 'OPENCLAW_ALWAYS_ON_POLICY.md'
    assert p.exists()
    t = p.read_text()
    assert 'Default Integration Points' in t
    assert 'WIRING_ACTIVE_BUT_SOAK_PENDING' in t


def test_scheduler_quick_runs_and_writes_runtime():
    r = run([str(W / 'tools' / 'agent-self-health-scheduler'), '--mode', 'quick', '--force', '--json'])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data['mode'] == 'quick'
    assert (W / 'artifacts' / 'self_health' / 'runtime' / 'heartbeat_status.json').exists()


def test_gate_tool_emits_json():
    r = run(['python3', str(W / 'tools' / 'gate-self-health-check'), '--json'])
    assert r.stdout.strip()
    data = json.loads(r.stdout)
    assert 'gate_a' in data and 'gate_b' in data and 'gate_c' in data
