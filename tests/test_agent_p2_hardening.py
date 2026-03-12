import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'
REC = W / 'artifacts' / 'self_health' / 'recovery_logs'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def clear_recovery_logs():
    REC.mkdir(parents=True, exist_ok=True)
    for f in REC.glob('recovery_*.json'):
        f.unlink()


def test_rerun_health_check_is_evidence_refresh():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'heartbeat.status.json').write_text(json.dumps({
        'status': 'unknown',
        'metrics': {},
        'failure_indicators': ['missing_probe']
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'rerun_health_check', '--component', 'heartbeat', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['action_result']['kind'] == 'evidence_refresh'
    assert data['action_result']['counts_as_recovery'] is False


def test_restart_worker_does_not_false_green_without_progress_recovery():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'callback-worker.status.json').write_text(json.dumps({
        'status': 'error',
        'metrics': {'process_alive': False, 'last_progress_time': 'old', 'backlog': 10, 'stuck': True},
        'failure_indicators': ['worker_down', 'worker_stuck', 'no_progress']
    }))
    # simulate process revival but no real progress recovery
    (STATE/'callback-worker.restart_behavior.json').write_text(json.dumps({
        'process_alive': True,
        'last_progress_time': 'old',
        'backlog': 12,
        'stuck': True,
        'keep_failure_indicators': ['no_progress', 'worker_stuck']
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['verdict'] != 'recovered'


def test_min_escalation_stop_after_repeated_failures():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'mailbox-worker.status.json').write_text(json.dumps({
        'status': 'error',
        'metrics': {'process_alive': False, 'last_progress_time': 'old', 'backlog': 7, 'stuck': True},
        'failure_indicators': ['worker_down', 'no_progress']
    }))
    (STATE/'mailbox-worker.restart_behavior.json').write_text(json.dumps({
        'process_alive': True,
        'last_progress_time': 'old',
        'backlog': 9,
        'stuck': True,
        'keep_failure_indicators': ['no_progress']
    }))
    first = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'mailbox-worker', '--json'])
    second = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'mailbox-worker', '--json'])
    third = run([str(W/'tools'/'agent-self-heal'), '--action', 'restart_worker', '--component', 'mailbox-worker', '--json'])
    assert first[0] == 0
    assert second[0] in (0,4)
    assert third[0] == 4
    data = json.loads(third[1])
    assert data['guard']['blocked_reason'] in {'max_retry_exceeded', 'escalation_stop'}
