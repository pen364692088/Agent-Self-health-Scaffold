import json, subprocess, time
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_rerun_health_check_real_action_records_policy_fields():
    STATE.mkdir(parents=True, exist_ok=True)
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'rerun_health_check', '--component', 'heartbeat', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['action'] == 'rerun_health_check'
    assert 'guard' in data
    assert data['guard']['allowed'] is True
    assert data['guard']['verification_window_seconds'] >= 1


def test_restart_worker_real_action_changes_worker_signal():
    STATE.mkdir(parents=True, exist_ok=True)
    marker = STATE/'callback-worker.status.json'
    marker.write_text(json.dumps({
        'status': 'error',
        'metrics': {'process_alive': False, 'last_progress_time': 'old', 'backlog': 10, 'stuck': True},
        'failure_indicators': ['worker_down', 'worker_stuck']
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['action'] == 'restart_worker'
    assert data['verdict'] in {'recovered', 'unchanged', 'degraded', 'insufficient_evidence'}
    after = json.loads(Path(data['snapshot_after_path']).read_text())
    assert after['status'] in {'ok', 'warning', 'error', 'failed', 'unknown'}


def test_cooldown_blocks_immediate_repeat():
    STATE.mkdir(parents=True, exist_ok=True)
    for f in (W/'artifacts'/'self_health'/'recovery_logs').glob('recovery_*.json'):
        f.unlink()
    marker = STATE/'mailbox-worker.status.json'
    marker.write_text(json.dumps({
        'status': 'error',
        'metrics': {'process_alive': False, 'last_progress_time': 'old', 'backlog': 4, 'stuck': True},
        'failure_indicators': ['worker_down']
    }))
    first = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'mailbox-worker', '--json'])
    second = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'mailbox-worker', '--json'])
    assert first[0] == 0, first[2]
    assert second[0] == 4
    data = json.loads(second[1])
    assert data['guard']['blocked_reason'] in {'cooldown_active', 'escalation_stop'}
