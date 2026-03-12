import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_heartbeat_anomaly_flows_into_recovery_kernel():
    STATE.mkdir(parents=True, exist_ok=True)
    for f in (W/'artifacts'/'self_health'/'recovery_logs').glob('recovery_*.json'):
        f.unlink()
    marker = STATE/'heartbeat.status.json'
    marker.write_text(json.dumps({
        'status': 'warning',
        'metrics': {'last_seen': '2026-03-08T00:00:00Z', 'lag_seconds': 120, 'consecutive_failures': 3, 'last_successful_cycle': '2026-03-08T00:00:00Z'},
        'failure_indicators': ['heartbeat_stale', 'consecutive_failures']
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'rotate_logs', '--component', 'heartbeat', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['component'] == 'heartbeat'
    assert data['snapshot_before_path']
    assert data['snapshot_after_path']
    assert data['verdict'] in {'recovered', 'unchanged', 'degraded', 'insufficient_evidence'}
    before = json.loads(Path(data['snapshot_before_path']).read_text())
    assert before['component'] == 'heartbeat'
    assert 'lag_seconds' in before['metrics']
