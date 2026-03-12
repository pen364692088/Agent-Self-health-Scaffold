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


def test_clear_stale_lock_blocks_active_or_fresh_lock():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'callback-worker.lock.json').write_text(json.dumps({
        'age_seconds': 60,
        'owner_alive': True,
        'active_lock': True,
        'lease_fresh': True,
        'expected_holder_identity': 'callback-worker'
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'clear_stale_lock', '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['precondition_status'] == 'failed'
    assert data['verdict'] in {'unchanged', 'insufficient_evidence'}
    assert (STATE/'callback-worker.lock.json').exists()


def test_clear_stale_lock_allows_only_stale_dead_owner_lock():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'callback-worker.status.json').write_text(json.dumps({
        'status': 'warning',
        'metrics': {'blocked_by_lock': True},
        'failure_indicators': ['stale_lock_present']
    }))
    (STATE/'callback-worker.lock.json').write_text(json.dumps({
        'age_seconds': 601,
        'owner_alive': False,
        'active_lock': False,
        'lease_fresh': False,
        'expected_holder_identity': 'callback-worker',
        'actual_holder_identity': 'callback-worker'
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'clear_stale_lock', '--component', 'callback-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['precondition_status'] == 'met'
    assert not (STATE/'callback-worker.lock.json').exists()
    assert data['verdict'] in {'recovered', 'unchanged'}


def test_clear_stale_lock_holder_mismatch_is_blocked():
    clear_recovery_logs()
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'mailbox-worker.lock.json').write_text(json.dumps({
        'age_seconds': 700,
        'owner_alive': False,
        'active_lock': False,
        'lease_fresh': False,
        'expected_holder_identity': 'mailbox-worker',
        'actual_holder_identity': 'some-other-holder'
    }))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'clear_stale_lock', '--component', 'mailbox-worker', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['precondition_status'] == 'failed'
    assert (STATE/'mailbox-worker.lock.json').exists()
