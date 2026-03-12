import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def assert_contract(data):
    for key in ['probe_name','component','status','observed_at','evidence','metrics','failure_indicators','recoverability_hint']:
        assert key in data


def test_heartbeat_probe_contract_and_mapping():
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'heartbeat.status.json').write_text(json.dumps({
        'status': 'warning',
        'metrics': {'last_seen': '2026-03-08T00:00:00Z', 'lag_seconds': 95, 'consecutive_failures': 2, 'last_successful_cycle': '2026-03-08T00:00:00Z'},
        'failure_indicators': ['heartbeat_stale']
    }))
    code, out, err = run([str(W/'tools'/'agent-probe'), '--component', 'heartbeat', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert_contract(data)
    assert data['component'] == 'heartbeat'
    assert data['recoverability_hint'] == 'rerun_health_check'


def test_worker_probe_contract_and_mapping():
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'callback-worker.status.json').write_text(json.dumps({
        'status': 'error',
        'metrics': {'process_alive': True, 'last_progress_time': '2026-03-08T00:00:00Z', 'backlog': 12, 'stuck': True},
        'failure_indicators': ['worker_stuck', 'backlog_high']
    }))
    code, out, err = run([str(W/'tools'/'agent-probe'), '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert_contract(data)
    assert data['recoverability_hint'] == 'restart_worker'


def test_systemd_probe_contract_from_fixture_file():
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'systemd.callback-worker.status.json').write_text(json.dumps({
        'status': 'failed',
        'metrics': {'service_state': 'failed'},
        'failure_indicators': ['systemd_failed']
    }))
    code, out, err = run([str(W/'tools'/'agent-probe'), '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert_contract(data)
